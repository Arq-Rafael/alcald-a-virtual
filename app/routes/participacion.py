from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app, jsonify, send_file
from app import db
from app.models.participacion import Radicado, RespuestaRadicado
from app.utils import can_access, admin_required
import os
import datetime
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
        
        # Generar número de radicado
        year = datetime.datetime.now().year
        count = Radicado.query.filter(Radicado.numero_radicado.like(f"%{year}%")).count()
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
