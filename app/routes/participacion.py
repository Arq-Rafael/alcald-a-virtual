from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app, jsonify, send_file
from app import db
from app.models.participacion import Radicado, RespuestaRadicado
from app.utils import can_access, admin_required
import os
import datetime
import hashlib
import io
from werkzeug.utils import secure_filename
import json
import csv

participacion_bp = Blueprint('participacion', __name__, url_prefix='/participacion')

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xls', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def can_radicar():
    """Verifica si el usuario puede radicar nuevos documentos"""
    role = session.get('role', '').lower()
    secretaria = session.get('secretaria', '').lower()
    return role in ['admin', 'superadmin'] or 'gobierno' in secretaria or 'gobierno' in role

def get_oficinas():
    """Carga las oficinas desde el archivo de configuración o base de datos"""
    return {
        'SGOB': 'Secretaría General y de Gobierno',
        'SPLA': 'Secretaría de Planeación y Obras Públicas',
        'SDSC': 'Secretaría de Desarrollo Social y Comunitario',
        'SDRU': 'Secretaría de Desarrollo Rural Medio Ambiente y Competitividad',
        'SHAC': 'Secretaría de Hacienda y Gestión Financiera'
    }

def radicado_to_dict(radicado):
    """Convierte un objeto Radicado a diccionario JSON-serializable"""
    return {
        'id': radicado.id,
        'numero_radicado': radicado.numero_radicado,
        'fecha_radicacion': radicado.fecha_radicacion.isoformat() if radicado.fecha_radicacion else None,
        'fecha_vencimiento': radicado.fecha_vencimiento.isoformat() if radicado.fecha_vencimiento else None,
        'tipo': radicado.tipo,
        'remitente_nombre': radicado.remitente_nombre,
        'remitente_entidad': radicado.remitente_entidad,
        'asunto': radicado.asunto,
        'descripcion': radicado.descripcion,
        'oficina_destino': radicado.oficina_destino,
        'plazo_dias': radicado.plazo_dias,
        'estado': radicado.estado,
        'dias_restantes': radicado.dias_restantes,
        'semaforo': radicado.semaforo,
        'creado_por': radicado.creado_por
    }

@participacion_bp.route('', endpoint='index')
def index():
    """Vista principal del módulo de participación (iOS26 mejorado)"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
        
    user = session.get('user')
    role = session.get('role', '').lower()
    secretaria = session.get('secretaria', '')
    
    # Obtener radicados según el usuario y su secretaría
    if can_radicar():
        # Admin y gobierno ven todos
        radicados = Radicado.query.order_by(Radicado.fecha_radicacion.desc()).all()
    else:
        # Otros usuarios ven solo los asignados a su secretaría
        oficinas_dict = get_oficinas()
        # Buscar la clave de la secretaría del usuario
        codigo_oficina = None
        for codigo, nombre in oficinas_dict.items():
            if secretaria and (nombre.lower() in secretaria.lower() or secretaria.lower() in nombre.lower()):
                codigo_oficina = codigo
                break
        
        if codigo_oficina:
            radicados = Radicado.query.filter(
                Radicado.oficina_destino == codigo_oficina
            ).order_by(Radicado.fecha_radicacion.desc()).all()
        else:
            # Fallback: filtrar por asignado_a
            radicados = Radicado.query.filter(
                (Radicado.asignado_a == user) | (Radicado.asignado_a == secretaria)
            ).order_by(Radicado.fecha_radicacion.desc()).all()

    # Convertir a JSON para JavaScript
    radicados_json = [radicado_to_dict(r) for r in radicados]
    
    return render_template(
        'participacion_ios26.html',
        radicados=radicados_json,
        puede_radicar=can_radicar(),
        oficinas=get_oficinas(),
        es_admin=(role in ['admin', 'superadmin'])
    )

@participacion_bp.route('/radicar-api', methods=['POST'], endpoint='radicar_api')
def radicar_api():
    """API para radicar nuevo documento (desde modal AJAX)"""
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    
    if not can_radicar():
        return jsonify({'success': False, 'error': 'No tiene permisos para radicar'}), 403
        
    try:
        # Obtener datos del formulario
        tipo = request.form.get('tipo')
        remitente_nombre = request.form.get('remitente_nombre')
        remitente_entidad = request.form.get('remitente_entidad', '')
        asunto = request.form.get('asunto')
        descripcion = request.form.get('descripcion')
        oficina_destino = request.form.get('oficina_destino')
        plazo_dias = int(request.form.get('plazo_dias', 5))
        
        # Validar campos requeridos
        if not all([tipo, remitente_nombre, asunto, descripcion, oficina_destino]):
            return jsonify({
                'success': False,
                'error': 'Faltan campos requeridos'
            }), 400
        
        # Número de radicado: manual si viene, auto si no
        numero_radicado = request.form.get('numero_radicado', '').strip()
        year = datetime.datetime.now().year
        if numero_radicado:
            # Verificar que no exista ya
            if Radicado.query.filter_by(numero_radicado=numero_radicado).first():
                return jsonify({
                    'success': False,
                    'error': f'El número de radicado {numero_radicado} ya existe. Por favor usa otro.'
                }), 409
        else:
            count = Radicado.query.filter(Radicado.numero_radicado.like(f"RAD-{year}-%")).count()
            numero_radicado = f"RAD-{year}-{str(count+1).zfill(5)}"
        
        # Crear radicado
        nuevo_radicado = Radicado(
            numero_radicado=numero_radicado,
            tipo=tipo,
            remitente_nombre=remitente_nombre,
            remitente_entidad=remitente_entidad,
            asunto=asunto,
            descripcion=descripcion,
            oficina_destino=oficina_destino,
            plazo_dias=plazo_dias,
            creado_por=session.get('user'),
            asignado_a=session.get('user')
        )
        
        # Procesar archivo PDF
        if 'pdf' in request.files:
            pdf_file = request.files['pdf']
            if pdf_file and pdf_file.filename and allowed_file(pdf_file.filename):
                upload_folder = os.path.join(current_app.config.get('DATA_DIR', 'data'), 'uploads', 'radicados')
                os.makedirs(upload_folder, exist_ok=True)
                
                filename = secure_filename(pdf_file.filename)
                unique_name = f"{numero_radicado}_{filename}"
                file_path = os.path.join(upload_folder, unique_name)
                pdf_file.save(file_path)
                
                nuevo_radicado.set_adjuntos([unique_name])
        
        # Guardar en base de datos
        db.session.add(nuevo_radicado)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'numero_radicado': numero_radicado,
            'message': f'Radicado {numero_radicado} creado exitosamente'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f'Error al radicar: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Error al procesar: {str(e)}'
        }), 500

@participacion_bp.route('/listar', methods=['GET'], endpoint='listar')
def listar():
    """API para obtener lista de radicados (JSON)"""
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    
    user = session.get('user')
    secretaria = session.get('secretaria', '')
    
    # Filtrar según permisos
    if can_radicar():
        radicados = Radicado.query.order_by(Radicado.fecha_radicacion.desc()).all()
    else:
        radicados = Radicado.query.filter(
            (Radicado.asignado_a == user) | (Radicado.asignado_a == secretaria)
        ).order_by(Radicado.fecha_radicacion.desc()).all()
    
    radicados_json = [radicado_to_dict(r) for r in radicados]
    
    return jsonify({
        'success': True,
        'radicados': radicados_json
    }), 200

@participacion_bp.route('/ver/<int:id>', methods=['GET'], endpoint='ver')
def ver_radicado(id):
    """Ver detalle de un radicado"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    radicado = Radicado.query.get_or_404(id)
    
    # Verificar permisos
    user = session.get('user')
    secretaria = session.get('secretaria', '')
    
    is_authorized = (
        can_radicar() or 
        radicado.asignado_a == user or 
        radicado.asignado_a == secretaria or
        radicado.creado_por == user
    )
    
    if not is_authorized:
        flash('No tiene permiso para ver este radicado.', 'danger')
        return redirect(url_for('participacion.index'))
    
    respuestas = [
        {
            'id': r.id,
            'fecha': r.fecha_respuesta.isoformat() if r.fecha_respuesta else None,
            'texto': r.respuesta_texto,
            'respondido_por': r.respondido_por
        }
        for r in radicado.respuestas
    ]
    
    return render_template(
        'participacion_ver.html',
        radicado=radicado,
        respuestas=respuestas,
        oficinas=get_oficinas()
    )

@participacion_bp.route('/responder/<int:id>', methods=['GET', 'POST'], endpoint='responder')
def responder(id):
    """Responder a un radicado"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    radicado = Radicado.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            respuesta_texto = request.form.get('respuesta_texto')
            
            if not respuesta_texto:
                flash('La respuesta no puede estar vacía.', 'warning')
                return redirect(url_for('participacion.responder', id=id))
            
            nueva_respuesta = RespuestaRadicado(
                radicado_id=radicado.id,
                respuesta_texto=respuesta_texto,
                respondido_por=session.get('user')
            )
            
            # Procesar archivos adjuntos
            if 'adjuntos_respuesta' in request.files:
                uploaded_files = request.files.getlist('adjuntos_respuesta')
                saved_paths = []
                upload_folder = os.path.join(current_app.config.get('DATA_DIR', 'data'), 'uploads', 'respuestas')
                os.makedirs(upload_folder, exist_ok=True)
                
                for file in uploaded_files:
                    if file and file.filename and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        unique_name = f"RESP_{radicado.numero_radicado}_{filename}"
                        file_path = os.path.join(upload_folder, unique_name)
                        file.save(file_path)
                        saved_paths.append(unique_name)
                
                if saved_paths:
                    nueva_respuesta.set_adjuntos(saved_paths)
            
            db.session.add(nueva_respuesta)
            radicado.estado = 'RESPONDIDO'
            db.session.commit()
            
            flash('Respuesta enviada exitosamente.', 'success')
            return redirect(url_for('participacion.ver', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al responder: {str(e)}', 'danger')
            return redirect(url_for('participacion.responder', id=id))
    
    return render_template(
        'participacion_responder.html',
        radicado=radicado,
        oficinas=get_oficinas()
    )

@participacion_bp.route('/descargar/<int:id>', methods=['GET'], endpoint='descargar')
def descargar(id):
    """Descargar radicado o respuesta"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    radicado = Radicado.query.get_or_404(id)
    adjuntos = radicado.get_adjuntos()
    
    if not adjuntos:
        flash('No hay archivos para descargar.', 'warning')
        return redirect(url_for('participacion.ver', id=id))
    
    # Descargar el primer archivo (principal)
    archivo = adjuntos[0]
    upload_folder = os.path.join(current_app.config.get('DATA_DIR', 'data'), 'uploads', 'radicados')
    file_path = os.path.join(upload_folder, archivo)
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    
    flash('Archivo no encontrado.', 'error')
    return redirect(url_for('participacion.ver', id=id))

@participacion_bp.route('/siguiente-radicado', methods=['GET'], endpoint='siguiente_radicado')
def siguiente_radicado():
    """Retorna el siguiente número de radicado disponible para el año actual"""
    if 'user' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    year = datetime.datetime.now().year
    count = Radicado.query.filter(Radicado.numero_radicado.like(f"RAD-{year}-%")).count()
    numero = f"RAD-{year}-{str(count + 1).zfill(5)}"
    return jsonify({'numero': numero})


@participacion_bp.route('/radicado/<int:id>/constancia-pdf', methods=['GET'], endpoint='constancia_pdf')
def constancia_pdf(id):
    """Genera y descarga la constancia de radicado en PDF"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    radicado = Radicado.query.get_or_404(id)

    # Verificar permisos mínimos
    user = session.get('user')
    secretaria = session.get('secretaria', '')
    is_authorized = (
        can_radicar() or
        radicado.asignado_a == user or
        radicado.asignado_a == secretaria or
        radicado.creado_por == user
    )
    if not is_authorized:
        return jsonify({'error': 'Sin permiso para descargar esta constancia'}), 403

    # Código de verificación único (12 chars hex derivado del ID + número + fecha)
    raw = f"{radicado.id}-{radicado.numero_radicado}-{radicado.fecha_radicacion}"
    codigo_verificacion = hashlib.sha256(raw.encode()).hexdigest()[:12].upper()

    # Datos de oficina destino
    oficinas = get_oficinas()
    nombre_oficina = oficinas.get(radicado.oficina_destino, radicado.oficina_destino or '—')

    # Fecha formateada
    fecha_rad = radicado.fecha_radicacion.strftime('%d de %B de %Y') if radicado.fecha_radicacion else '—'
    fecha_venc = radicado.fecha_vencimiento.strftime('%d/%m/%Y') if radicado.fecha_vencimiento else '—'

    # Ruta logo
    logo_path = os.path.join(current_app.root_path, '..', 'static', 'imagenes', 'logo_new.png')
    logo_path = os.path.abspath(logo_path)
    logo_src = f"file:///{logo_path.replace(chr(92), '/')}" if os.path.exists(logo_path) else ''

    estado_label = {
        'PENDIENTE': 'Pendiente',
        'EN_TRAMITE': 'En Trámite',
        'RESPONDIDO': 'Respondido',
    }.get(radicado.estado, radicado.estado)

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Inter', Arial, sans-serif; color: #1a1a1a; background: #fff; padding: 2.5cm; }}
  .header {{ display: flex; align-items: center; gap: 1.5rem; border-bottom: 3px solid #0f4c81; padding-bottom: 1.2rem; margin-bottom: 1.8rem; }}
  .header img {{ width: 72px; height: 72px; object-fit: contain; }}
  .header-text h1 {{ font-size: 1.05rem; color: #0f4c81; font-weight: 700; margin-bottom: .2rem; }}
  .header-text p {{ font-size: .8rem; color: #555; }}
  .titulo-constancia {{ text-align: center; font-size: 1.3rem; font-weight: 700; color: #0f4c81;
    margin-bottom: 1.5rem; letter-spacing: .5px; text-transform: uppercase; }}
  .numero-grande {{ text-align: center; font-size: 2.2rem; font-weight: 700; color: #1565c0;
    background: #eef4fb; border-radius: 12px; padding: .8rem 1.5rem; margin-bottom: 2rem;
    letter-spacing: 1px; border: 2px solid #b3cde8; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 1.5rem; }}
  th {{ background: #0f4c81; color: white; padding: .55rem .9rem; text-align: left;
    font-size: .78rem; font-weight: 600; }}
  td {{ padding: .55rem .9rem; font-size: .82rem; border-bottom: 1px solid #e5e7eb; }}
  tr:nth-child(even) td {{ background: #f8fafc; }}
  .section-label {{ font-size: .7rem; font-weight: 700; color: #0f4c81; text-transform: uppercase;
    letter-spacing: .8px; margin-bottom: .5rem; margin-top: 1.2rem; }}
  .asunto-box {{ background: #f8fafc; border-left: 4px solid #0f4c81; padding: .8rem 1rem;
    border-radius: 0 8px 8px 0; font-size: .83rem; margin-bottom: 1.5rem; line-height: 1.5; }}
  .verificacion {{ margin-top: 2rem; border: 1.5px dashed #b3cde8; border-radius: 10px;
    padding: 1rem 1.2rem; display: flex; align-items: center; gap: 1.2rem; }}
  .verif-icon {{ font-size: 2rem; }}
  .verif-label {{ font-size: .72rem; color: #555; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; }}
  .verif-code {{ font-size: 1.05rem; font-weight: 700; color: #0f4c81; font-family: monospace; letter-spacing: 2px; }}
  .footer {{ margin-top: 2.5rem; text-align: center; font-size: .72rem; color: #888;
    border-top: 1px solid #e5e7eb; padding-top: 1rem; }}
</style>
</head>
<body>
  <!-- ENCABEZADO -->
  <div class="header">
    {'<img src="' + logo_src + '" alt="Logo Alcaldía">' if logo_src else '<div style="width:72px;height:72px;background:#0f4c81;border-radius:8px;"></div>'}
    <div class="header-text">
      <h1>Alcaldía Municipal de Supatá</h1>
      <p>Sistema de Gestión Documental · Participación Ciudadana</p>
    </div>
  </div>

  <!-- TÍTULO Y NÚMERO -->
  <div class="titulo-constancia">Constancia de Radicación</div>
  <div class="numero-grande">{radicado.numero_radicado}</div>

  <!-- DATOS DEL RADICADO -->
  <p class="section-label">Información del Radicado</p>
  <table>
    <tr><th>Campo</th><th>Valor</th></tr>
    <tr><td>Fecha de Radicación</td><td>{fecha_rad}</td></tr>
    <tr><td>Tipo</td><td>{radicado.tipo}</td></tr>
    <tr><td>Estado</td><td>{estado_label}</td></tr>
    <tr><td>Plazo de respuesta</td><td>{radicado.plazo_dias} días hábiles</td></tr>
    <tr><td>Fecha de vencimiento</td><td>{fecha_venc}</td></tr>
    <tr><td>Oficina destinataria</td><td>{nombre_oficina}</td></tr>
    <tr><td>Radicado por</td><td>{radicado.creado_por or '—'}</td></tr>
  </table>

  <!-- DATOS DEL REMITENTE -->
  <p class="section-label">Datos del Remitente</p>
  <table>
    <tr><th>Campo</th><th>Valor</th></tr>
    <tr><td>Nombre</td><td>{radicado.remitente_nombre}</td></tr>
    <tr><td>Entidad / Organización</td><td>{radicado.remitente_entidad or 'Particular'}</td></tr>
  </table>

  <!-- ASUNTO Y DESCRIPCIÓN -->
  <p class="section-label">Asunto y Descripción</p>
  <div class="asunto-box">
    <strong>{radicado.asunto}</strong><br>
    <span style="color:#555;">{radicado.descripcion or ''}</span>
  </div>

  <!-- CÓDIGO DE VERIFICACIÓN -->
  <div class="verificacion">
    <div class="verif-icon">🔐</div>
    <div>
      <div class="verif-label">Código de Verificación</div>
      <div class="verif-code">{codigo_verificacion}</div>
      <div style="font-size:.7rem;color:#888;margin-top:.25rem;">
        Use este código para verificar la autenticidad de este documento ante la Alcaldía Municipal.
      </div>
    </div>
  </div>

  <!-- PIE DE PÁGINA -->
  <div class="footer">
    Alcaldía Municipal de Supatá · Sistema de Gestión Documental<br>
    Documento generado el {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')} · {radicado.numero_radicado}
  </div>
</body>
</html>"""

    try:
        from weasyprint import HTML as WP_HTML
        pdf_bytes = WP_HTML(string=html_content).write_pdf()
        nombre_archivo = f"constancia_{radicado.numero_radicado}.pdf"
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=nombre_archivo
        )
    except Exception as e:
        # Fallback: devolver HTML con auto-print para que el usuario guarde como PDF
        # Funciona en Windows (dev) y en cualquier entorno sin GTK
        print(f'WeasyPrint no disponible ({e}), usando fallback HTML/print')
        print_html = html_content.replace(
            '</style>',
            '''
  @media print {
    body { padding: 1.5cm; }
    .no-print { display: none !important; }
  }
  .print-bar {
    position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
    background: #0f4c81; color: white; padding: .75rem 1.5rem;
    display: flex; align-items: center; justify-content: space-between;
    font-family: Arial, sans-serif; font-size: .9rem; box-shadow: 0 2px 8px rgba(0,0,0,.3);
  }
  .print-bar button {
    background: white; color: #0f4c81; border: none; padding: .5rem 1.2rem;
    border-radius: 6px; font-weight: 700; cursor: pointer; font-size: .85rem;
  }
  @media print { .print-bar { display: none; } body { padding-top: 0; } }
</style>'''
        ).replace(
            '<body>',
            '''<body>
  <div class="print-bar no-print">
    <span>📄 Constancia de Radicación — Guardar como PDF</span>
    <div style="display:flex;gap:.75rem;">
      <button onclick="window.print()">🖨️ Imprimir / Guardar PDF</button>
      <button onclick="window.close()" style="background:rgba(255,255,255,.2);color:white;border:1px solid rgba(255,255,255,.4);">✕ Cerrar</button>
    </div>
  </div>
  <div style="height:56px;" class="no-print"></div>'''
        ).replace(
            '</body>',
            '<script>window.addEventListener("load",function(){setTimeout(function(){window.print();},600);});</script></body>'
        )
        return print_html, 200, {'Content-Type': 'text/html; charset=utf-8'}


@participacion_bp.route('/eliminar/<int:id>', methods=['POST'], endpoint='eliminar')
def eliminar(id):
    """Eliminar radicado (solo admin)"""
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    
    role = session.get('role', '').lower()
    if role not in ['admin', 'superadmin']:
        return jsonify({'success': False, 'error': 'Solo administradores pueden eliminar radicados'}), 403
    
    radicado = Radicado.query.get(id)
    if not radicado:
        return jsonify({'success': False, 'error': 'Radicado no encontrado'}), 404
    
    try:
        numero = radicado.numero_radicado
        db.session.delete(radicado)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Radicado {numero} eliminado exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
