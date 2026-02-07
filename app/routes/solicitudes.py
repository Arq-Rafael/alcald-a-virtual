import os
import csv
import uuid
import json
import datetime
import datetime as dt
from datetime import timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, session, abort, current_app, jsonify
from werkzeug.utils import secure_filename
from app.utils import get_sqlite, dias_restantes, color_semaforo_dias, admin_required, load_plan_desarrollo
from app import db

solicitudes_bp = Blueprint('solicitudes', __name__)

# --- Routes: Solicitudes Generales (CSV) ---

@solicitudes_bp.route('/solicitudes', methods=['GET', 'POST'], endpoint='index')
def solicitudes():
    secretarias = [
      "Secretaría General y de Gobierno",
      "Secretaría de Planeación y Obras Públicas",
      "Secretaría de Desarrollo Social y Comunitario",
      "Secretaría de Desarrollo Rural Medio Ambiente y Competitividad",
      "Secretaría de Hacienda y Gestión Financiera"
    ]

    path = current_app.config['SOLICITUDES_PATH']

    if request.method == 'POST':
        raw_val = request.form.get('valor','').strip()
        try:
            num = int(raw_val.replace('.', ''))
            valor_formatted = '$ ' + '{:,.0f}'.format(num).replace(',', '.')
        except ValueError:
            valor_formatted = raw_val        
         
        row = [
            request.form.get('municipio','').strip(),
            request.form.get('nit','').strip(),
            request.form.get('fecha',''),
            request.form.get('secretaria',''),
            request.form.get('objeto','').strip(),
            request.form.get('justificacion','').strip(),
            valor_formatted,
            request.form.get('meta_producto',''),
            request.form.get('eje',''),
            request.form.get('sector',''),
            request.form.get('codigo_bpim',''),
            'nuevo'  # Estado inicial: nuevo (entra directo a certificados)
        ]
        
        try:
            with open(path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
            flash('✅ Solicitud guardada correctamente.', 'success')
        except Exception as e:
            flash(f'Error guardando solicitud: {e}', 'danger')
            
        return redirect(url_for('solicitudes.index'))

    # Load Plan de Desarrollo data
    plan_list = load_plan_desarrollo()
    
    # Cargar solicitudes del usuario actual
    user_solicitudes = []
    current_user = session.get('user', 'invitado')
    
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Filtrar por municipio (asumiendo que es el identificador del usuario)
                    # Ajusta esto según tu lógica de autenticación
                    user_solicitudes.append({
                        'municipio': row.get('municipio', ''),
                        'nit': row.get('nit', ''),
                        'fecha': row.get('fecha', ''),
                        'secretaria': row.get('secretaria', ''),
                        'objeto': row.get('objeto', ''),
                        'justificacion': row.get('justificacion', ''),
                        'valor': row.get('valor', ''),
                        'meta_producto': row.get('meta_producto', ''),
                        'eje': row.get('eje', ''),
                        'sector': row.get('sector', ''),
                        'codigo_bpim': row.get('codigo_bpim', ''),
                        'estado': row.get('estado', 'borrador')
                    })
    except Exception as e:
        print(f"Error cargando solicitudes: {e}")

    is_admin = session.get('user_role') == 'admin' or session.get('user') == 'admin'

    return render_template(
        'solicitudes_modern.html',
        secretarias=secretarias,
        plan_list=plan_list,
        user_solicitudes=user_solicitudes,
        today=dt.date.today().isoformat(),
        is_admin=is_admin
    )


@solicitudes_bp.route('/solicitudes/editar', methods=['POST'], endpoint='editar_solicitud')
def editar_solicitud():
    """Edita una solicitud existente en el CSV"""
    path = current_app.config['SOLICITUDES_PATH']
    
    try:
        indice = int(request.form.get('indice', -1))
        
        # Leer todas las filas
        rows = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        if indice < 0 or indice >= len(rows) - 1:  # -1 porque la primera fila es header
            flash('❌ Solicitud no encontrada', 'danger')
            return redirect(url_for('solicitudes.index'))
        
        # Formatear valor
        raw_val = request.form.get('valor', '').strip()
        try:
            num = int(raw_val.replace('$', '').replace('.', '').replace(',', '').strip())
            valor_formatted = '$ ' + '{:,.0f}'.format(num).replace(',', '.')
        except ValueError:
            valor_formatted = raw_val
        
        # Determinar nuevo estado: si fue 'generado', cambiar a 'editado', si no preservar
        estado_actual = rows[indice + 1][11] if len(rows[indice + 1]) > 11 else 'nuevo'
        # Siempre marcamos como editado para reactivar el flujo hacia certificados
        nuevo_estado = 'editado'
        
        # Actualizar la fila (indice + 1 porque hay header)
        rows[indice + 1] = [
            request.form.get('municipio', rows[indice + 1][0]).strip(),
            request.form.get('nit', rows[indice + 1][1]).strip(),
            request.form.get('fecha', ''),
            request.form.get('secretaria', ''),
            request.form.get('objeto', '').strip(),
            request.form.get('justificacion', '').strip(),
            valor_formatted,
            request.form.get('meta_producto', ''),
            request.form.get('eje', rows[indice + 1][8] if len(rows[indice + 1]) > 8 else ''),
            request.form.get('sector', rows[indice + 1][9] if len(rows[indice + 1]) > 9 else ''),
            request.form.get('codigo_bpim', rows[indice + 1][10] if len(rows[indice + 1]) > 10 else ''),
            nuevo_estado  # Cambiar a 'editado' si fue 'generado'
        ]
        
        # Escribir de vuelta al archivo
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
            f.flush()  # Flush del buffer Python
            os.fsync(f.fileno())  # Sincronización forzada al disco
        
        flash('✅ Solicitud actualizada correctamente', 'success')
    except Exception as e:
        flash(f'❌ Error actualizando solicitud: {e}', 'danger')
    
    return redirect(url_for('solicitudes.index'))


@solicitudes_bp.route('/solicitudes/enviar_certificado', methods=['POST'], endpoint='enviar_certificado')
def enviar_certificado():
    """Marca una solicitud como lista para generar certificado"""
    path = current_app.config['SOLICITUDES_PATH']
    
    try:
        indice = int(request.form.get('indice', -1))
        
        # Leer todas las filas
        rows = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        if indice < 0 or indice >= len(rows) - 1:
            flash('❌ Solicitud no encontrada', 'danger')
            return redirect(url_for('solicitudes.index'))
        
        # Actualizar estado a "pendiente"
        row_index = indice + 1
        if len(rows[row_index]) > 11:
            rows[row_index][11] = 'pendiente'
        else:
            # Si no existe la columna, agregarla
            rows[row_index].append('pendiente')
        
        # Escribir de vuelta al archivo
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
            f.flush()  # Flush del buffer Python
            os.fsync(f.fileno())  # Sincronización forzada al disco
        flash('✅ Solicitud enviada para generar certificado', 'success')
    except Exception as e:
        flash(f'❌ Error enviando solicitud: {e}', 'danger')
    
    return redirect(url_for('solicitudes.index'))


@solicitudes_bp.route('/solicitudes/eliminar', methods=['POST'], endpoint='eliminar_solicitud')
@admin_required
def eliminar_solicitud():
    """Elimina una solicitud (solo admin)"""
    path = current_app.config['SOLICITUDES_PATH']
    try:
        indice = int(request.form.get('indice', -1))
        rows = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        if indice < 0 or indice >= len(rows) - 1:
            flash('❌ Solicitud no encontrada', 'danger')
            return redirect(url_for('solicitudes.index'))
        rows.pop(indice + 1)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
            f.flush()
            os.fsync(f.fileno())
        flash('✅ Solicitud eliminada', 'success')
    except Exception as e:
        flash(f'❌ Error eliminando solicitud: {e}', 'danger')
    return redirect(url_for('solicitudes.index'))


# --- Schemas ---

def init_arbolado_schema():
    conn = get_sqlite(); cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tala_solicitudes (
        id TEXT PRIMARY KEY,
        consecutivo INTEGER,
        fecha TEXT,
        solicitante TEXT,
        doc_solicitante TEXT,
        direccion TEXT,
        barrio_vereda TEXT,
        motivo TEXT,
        arboles_json TEXT,
        estado TEXT,
        observaciones TEXT,
        creado_por TEXT,
        creado_en TEXT,
        actualizado_en TEXT,
        eliminado INTEGER DEFAULT 0,
        visita_path TEXT,
        comp_ratio FLOAT DEFAULT 2.0,
        arboles_talar INTEGER DEFAULT 0,
        arboles_compensar INTEGER DEFAULT 0,
        cert_path TEXT,
        cert_fecha TEXT,
        cert_vence TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tala_seq (k TEXT PRIMARY KEY, n INTEGER)
    """)
    cur.execute("INSERT OR IGNORE INTO tala_seq (k, n) VALUES ('seq', 0)")
    conn.commit(); conn.close()

def next_tala_consecutivo():
    conn = get_sqlite(); cur = conn.cursor()
    cur.execute("UPDATE tala_seq SET n = n + 1 WHERE k='seq'")
    conn.commit()
    cur.execute("SELECT n FROM tala_seq WHERE k='seq'")
    n = cur.fetchone()['n']
    conn.close()
    return n

# Init schemas on module load
try:
    with current_app.app_context():
        init_arbolado_schema()
except:
    pass # Will run on first request if context fails here

# --- Routes: Arbolado (Tala) ---

@solicitudes_bp.route('/arbolado', endpoint='tala_list')
def tala_list():
    q = (request.args.get('q') or '').strip()
    estado = (request.args.get('estado') or '').strip()

    base = "SELECT * FROM tala_solicitudes WHERE eliminado=0"
    params = []
    if estado:
        base += " AND estado=?"; params.append(estado)
    if q:
        like = f"%{q}%"
        base += " AND (solicitante LIKE ? OR doc_solicitante LIKE ? OR direccion LIKE ? OR barrio_vereda LIKE ?)"
        params += [like, like, like, like]
    base += " ORDER BY actualizado_en DESC"

    conn = get_sqlite(); cur = conn.cursor()
    cur.execute(base, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    return render_template('tala_list.html', rows=rows, q=q, estado=estado)

@solicitudes_bp.route('/arbolado/nueva', methods=['GET','POST'])
def tala_nueva():
    if request.method != 'POST':
        return render_template('tala_form.html')

    solicitante = (request.form.get('solicitante') or '').strip()
    doc         = (request.form.get('doc_solicitante') or '').strip()
    direccion   = (request.form.get('direccion') or '').strip()
    barrio      = (request.form.get('barrio_vereda') or '').strip()
    motivo      = (request.form.get('motivo') or '').strip()
    arboles     = (request.form.get('arboles_json') or '').strip()
    obs         = (request.form.get('observaciones') or '').strip()

    sid = str(uuid.uuid4())
    consecutivo = next_tala_consecutivo()
    now = datetime.datetime.now().isoformat(timespec='seconds')

    conn = get_sqlite(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO tala_solicitudes (
            id, consecutivo, fecha, solicitante, doc_solicitante, direccion, barrio_vereda,
            motivo, arboles_json, estado, observaciones, creado_por, creado_en, actualizado_en
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (sid, consecutivo, now, solicitante, doc, direccion, barrio, motivo, arboles,
          'Radicada', obs, session.get('user',''), now, now))
    conn.commit(); conn.close()

    flash(f'Solicitud de tala #{consecutivo} creada.', 'success')
    return redirect(url_for('solicitudes.tala_list')) # Use endpoint

# --- Routes: Comite ---

@solicitudes_bp.route('/comite', endpoint='comite_list')
def comite_list():
    # Placeholder implementation
    return render_template('base.html', content="Módulo de Comité migrado (Listado)")

# --- Routes: Riesgo ---

@solicitudes_bp.route('/riesgo', endpoint='riesgo_list')
def riesgo_list():
    # Placeholder implementation
    return render_template('base.html', content="Módulo de Riesgo migrado (Listado)")

# --- Routes: Contratacion ---

@solicitudes_bp.route('/contratacion', endpoint='contrat_list')
def contrat_list():
    """Módulo de gestión de contratos SECOP I y SECOP II"""
    from flask import session
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    # Importar can_access localmente para evitar circular imports
    from app.utils import can_access
    if not can_access('contratos'):
        flash('No tienes permisos para acceder a este módulo', 'error')
        return redirect(url_for('main.dashboard'))
    return render_template('contratos.html')
# Alias para compatibilidad: /contratos -> /contratacion
@solicitudes_bp.route('/contratos', endpoint='contratos_alias')
def contratos_alias():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    # Importar can_access localmente para evitar circular imports
    from app.utils import can_access
    if not can_access('contratos'):
        flash('No tienes permisos para acceder a este módulo', 'error')
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('solicitudes.contrat_list'))

# =========================
#  MÓDULO: CALENDARIO DE EVENTOS
# =========================

from app.models.calendario import EventoCalendario
import calendar as cal_module

@solicitudes_bp.route('/calendario')
def calendario():
    """Muestra el calendario con eventos del usuario actual"""
    from flask import session
    import datetime
    
    usuario_id = session.get('usuario_id', 'anonimo')
    
    # Parámetros para navegación de meses
    try:
        año = int(request.args.get('year', datetime.datetime.now().year))
        mes = int(request.args.get('month', datetime.datetime.now().month))
    except:
        año = datetime.datetime.now().year
        mes = datetime.datetime.now().month
    
    # Validar rango de mes/año
    if mes < 1:
        mes = 1
        año -= 1
    if mes > 12:
        mes = 12
        año += 1
    
    # Obtener eventos del usuario para este mes
    fecha_inicio_mes = datetime.datetime(año, mes, 1)
    if mes == 12:
        fecha_fin_mes = datetime.datetime(año + 1, 1, 1) - datetime.timedelta(seconds=1)
    else:
        fecha_fin_mes = datetime.datetime(año, mes + 1, 1) - datetime.timedelta(seconds=1)
    
    eventos_mes = EventoCalendario.query.filter(
        EventoCalendario.usuario_id == usuario_id,
        EventoCalendario.fecha_inicio >= fecha_inicio_mes,
        EventoCalendario.fecha_inicio <= fecha_fin_mes
    ).all()
    
    # Obtener próximos eventos (desde hoy hasta 7 días después)
    ahora = datetime.datetime.now()
    hoy_inicio = datetime.datetime(ahora.year, ahora.month, ahora.day, 0, 0, 0)
    proximos_eventos_temp = EventoCalendario.query.filter(
        EventoCalendario.usuario_id == usuario_id,
        EventoCalendario.fecha_inicio >= hoy_inicio,
        EventoCalendario.fecha_inicio <= ahora + datetime.timedelta(days=7),
        EventoCalendario.completado == False
    ).order_by(EventoCalendario.fecha_inicio).all()
    
    # Obtener eventos que necesitan notificación
    eventos_notificacion_temp = EventoCalendario.query.filter(
        EventoCalendario.usuario_id == usuario_id,
        EventoCalendario.debe_notificar == True
    ).all()
    
    # Serializar próximos eventos
    proximos_eventos = []
    for evento in proximos_eventos_temp:
        proximos_eventos.append({
            'id': evento.id,
            'titulo': evento.titulo,
            'descripcion': evento.descripcion,
            'fecha_inicio': evento.fecha_inicio.isoformat(),
            'fecha_inicio_formato': evento.fecha_inicio.strftime('%H:%M - %d/%m/%Y'),
            'fecha_fin': evento.fecha_fin.isoformat() if evento.fecha_fin else None,
            'categoria': evento.categoria,
            'notificacion_minutos': evento.notificacion_minutos,
            'completado': evento.completado
        })
    
    # Serializar eventos de notificación
    eventos_notificacion = []
    for evento in eventos_notificacion_temp:
        eventos_notificacion.append({
            'id': evento.id,
            'titulo': evento.titulo,
            'descripcion': evento.descripcion,
            'fecha_inicio': evento.fecha_inicio.isoformat(),
            'categoria': evento.categoria,
            'notificacion_minutos': evento.notificacion_minutos
        })
    
    # Mapeo de eventos por día
    eventos_por_dia = {}
    for evento in eventos_mes:
        dia = evento.fecha_inicio.day
        if dia not in eventos_por_dia:
            eventos_por_dia[dia] = []
        eventos_por_dia[dia].append({
            'id': evento.id,
            'titulo': evento.titulo,
            'descripcion': evento.descripcion,
            'fecha_inicio': evento.fecha_inicio.isoformat(),
            'fecha_fin': evento.fecha_fin.isoformat() if evento.fecha_fin else None,
            'categoria': evento.categoria,
            'notificacion_minutos': evento.notificacion_minutos,
            'completado': evento.completado
        })
    
    # Generar matriz del calendario
    cal = cal_module.monthcalendar(año, mes)
    
    # Nombres de meses y días
    meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
             'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    dias_semana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    
    mes_nombre = meses[mes - 1]
    mes_anterior = {'año': año if mes > 1 else año - 1, 'mes': mes - 1 if mes > 1 else 12}
    mes_siguiente = {'año': año if mes < 12 else año + 1, 'mes': mes + 1 if mes < 12 else 1}
    
    return render_template('calendario.html',
        año=año,
        mes=mes,
        mes_nombre=mes_nombre,
        dias_semana=dias_semana,
        calendario=cal,
        eventos_por_dia=eventos_por_dia,
        proximos_eventos=proximos_eventos,
        eventos_notificacion=eventos_notificacion,
        mes_anterior=mes_anterior,
        mes_siguiente=mes_siguiente,
        usuario_id=usuario_id
    )

@solicitudes_bp.route('/evento/crear', methods=['POST'])
def crear_evento():
    """Crea un nuevo evento"""
    from flask import session
    import datetime
    
    usuario_id = session.get('usuario_id', 'anonimo')
    
    try:
        titulo = request.form.get('titulo', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        fecha_inicio_str = request.form.get('fecha_inicio')
        fecha_fin_str = request.form.get('fecha_fin')
        categoria = request.form.get('categoria', 'personal')
        color = request.form.get('color', 'primary')
        ubicacion = request.form.get('ubicacion', '').strip()
        notificacion_minutos = int(request.form.get('notificacion_minutos', 15))
        
        if not titulo or not fecha_inicio_str:
            return jsonify({'error': 'Título y fecha requeridos'}), 400
        
        # Parsear fechas
        fecha_inicio = datetime.datetime.fromisoformat(fecha_inicio_str)
        fecha_fin = datetime.datetime.fromisoformat(fecha_fin_str) if fecha_fin_str else None
        
        # Crear evento
        evento = EventoCalendario(
            usuario_id=usuario_id,
            titulo=titulo,
            descripcion=descripcion,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            categoria=categoria,
            color=color,
            ubicacion=ubicacion,
            notificacion_minutos=notificacion_minutos
        )
        
        db.session.add(evento)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'evento': evento.to_dict(),
            'message': 'Evento creado exitosamente'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@solicitudes_bp.route('/evento/<int:evento_id>/actualizar', methods=['POST'])
def actualizar_evento(evento_id):
    """Actualiza un evento existente"""
    from flask import session
    
    usuario_id = session.get('usuario_id', 'anonimo')
    evento = EventoCalendario.query.filter_by(id=evento_id, usuario_id=usuario_id).first()
    
    if not evento:
        return jsonify({'error': 'Evento no encontrado'}), 404
    
    try:
        evento.titulo = request.form.get('titulo', evento.titulo)
        evento.descripcion = request.form.get('descripcion', evento.descripcion)
        evento.categoria = request.form.get('categoria', evento.categoria)
        evento.color = request.form.get('color', evento.color)
        evento.ubicacion = request.form.get('ubicacion', evento.ubicacion)
        evento.notificacion_minutos = int(request.form.get('notificacion_minutos', evento.notificacion_minutos))
        
        if request.form.get('fecha_inicio'):
            evento.fecha_inicio = datetime.datetime.fromisoformat(request.form.get('fecha_inicio'))
        if request.form.get('fecha_fin'):
            evento.fecha_fin = datetime.datetime.fromisoformat(request.form.get('fecha_fin'))
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'evento': evento.to_dict(),
            'message': 'Evento actualizado exitosamente'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@solicitudes_bp.route('/evento/<int:evento_id>/eliminar', methods=['POST', 'DELETE'])
def eliminar_evento(evento_id):
    """Elimina un evento"""
    from flask import session
    
    usuario_id = session.get('usuario_id', 'anonimo')
    evento = EventoCalendario.query.filter_by(id=evento_id, usuario_id=usuario_id).first()
    
    if not evento:
        return jsonify({'error': 'Evento no encontrado'}), 404
    
    try:
        db.session.delete(evento)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Evento eliminado exitosamente'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@solicitudes_bp.route('/evento/<int:evento_id>/completar', methods=['POST'])
def completar_evento(evento_id):
    """Marca un evento como completado"""
    from flask import session
    
    usuario_id = session.get('usuario_id', 'anonimo')
    evento = EventoCalendario.query.filter_by(id=evento_id, usuario_id=usuario_id).first()
    
    if not evento:
        return jsonify({'error': 'Evento no encontrado'}), 404
    
    try:
        evento.completado = not evento.completado
        db.session.commit()
        
        return jsonify({
            'success': True,
            'completado': evento.completado,
            'message': f'Evento marcado como {"completado" if evento.completado else "pendiente"}'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@solicitudes_bp.route('/evento/<int:evento_id>/notificacion-enviada', methods=['POST'])
def marcar_notificacion_enviada(evento_id):
    """Marca que la notificación del evento fue enviada"""
    from flask import session
    
    usuario_id = session.get('usuario_id', 'anonimo')
    evento = EventoCalendario.query.filter_by(id=evento_id, usuario_id=usuario_id).first()
    
    if not evento:
        return jsonify({'error': 'Evento no encontrado'}), 404
    
    try:
        evento.notificacion_enviada = True
        db.session.commit()
        
        return jsonify({'success': True}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@solicitudes_bp.route('/evento/<int:evento_id>/posponer', methods=['POST'])
def posponer_evento(evento_id):
    """Pospone la hora de inicio/fin del evento en N minutos (por defecto 5)"""
    from flask import session
    import datetime
    
    usuario_id = session.get('usuario_id', 'anonimo')
    evento = EventoCalendario.query.filter_by(id=evento_id, usuario_id=usuario_id).first()
    if not evento:
        return jsonify({'error': 'Evento no encontrado'}), 404
    
    try:
        minutos = request.form.get('minutos') or request.json.get('minutos') if request.is_json else None
        try:
            minutos = int(minutos) if minutos is not None else 5
        except:
            minutos = 5
        
        delta = datetime.timedelta(minutes=minutos)
        evento.fecha_inicio = evento.fecha_inicio + delta
        if evento.fecha_fin:
            evento.fecha_fin = evento.fecha_fin + delta
        
        # Permitir que vuelva a notificar según nueva hora
        evento.notificacion_enviada = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Evento pospuesto {minutos} minutos',
            'fecha_inicio': evento.fecha_inicio.isoformat(),
            'fecha_fin': evento.fecha_fin.isoformat() if evento.fecha_fin else None
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@solicitudes_bp.route('/eventos/proximos')
def obtener_proximos_eventos():
    """API para obtener próximos eventos (AJAX) - incluye eventos de hoy"""
    from flask import session
    import datetime
    
    usuario_id = session.get('usuario_id', 'anonimo')
    ahora = datetime.datetime.now()
    hoy_inicio = datetime.datetime(ahora.year, ahora.month, ahora.day, 0, 0, 0)
    
    proximos = EventoCalendario.query.filter(
        EventoCalendario.usuario_id == usuario_id,
        EventoCalendario.fecha_inicio >= hoy_inicio,
        EventoCalendario.fecha_inicio <= ahora + datetime.timedelta(days=7),
        EventoCalendario.completado == False
    ).order_by(EventoCalendario.fecha_inicio).all()
    
    return jsonify([evento.to_dict() for evento in proximos])

# =========================
#  MÓDULO: LICENCIAS
# =========================

def business_days_between(start_dt, end_dt):
    if isinstance(start_dt, str): start_dt = datetime.datetime.fromisoformat(start_dt)
    if isinstance(end_dt, str):   end_dt   = datetime.datetime.fromisoformat(end_dt)
    if end_dt < start_dt: return 0
    days = 0; cur = start_dt
    while cur.date() <= end_dt.date():
        if cur.weekday() < 5:  # 0-4 = lun-vie
            days += 1
        cur += datetime.timedelta(days=1)
    return max(days - 1, 0)

def add_business_days(start_dt, n):
    if isinstance(start_dt, str): start_dt = datetime.datetime.fromisoformat(start_dt)
    cur = start_dt; added = 0
    while added < n:
        cur += datetime.timedelta(days=1)
        if cur.weekday() < 5:
            added += 1
    return cur

def init_licencias_schema():
    conn = get_sqlite()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS licencias (
        id TEXT PRIMARY KEY,
        consecutivo INTEGER,
        tipo TEXT, objeto TEXT, modalidad TEXT, direccion TEXT,
        chip TEXT, matricula TEXT, clasificacion_suelo TEXT,
        uso TEXT, uso_otro TEXT, area_const FLOAT, area_lote FLOAT,
        solicitante TEXT, tipo_doc_solicitante TEXT, doc_solicitante TEXT,
        responsable TEXT, matricula_prof TEXT, tipo_vivienda TEXT, bic TEXT,
        valor FLOAT, estado TEXT, observaciones TEXT,
        creado_por TEXT, creado_en TEXT, actualizado_en TEXT,
        eliminado INTEGER DEFAULT 0,
        acta_fecha TEXT, acta_path TEXT, acta_vence TEXT, respuesta_acta_fecha TEXT
    )""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS licencias_archivos (
        id TEXT PRIMARY KEY, licencia_id TEXT, filename TEXT, path TEXT,
        uploaded_en TEXT, uploaded_por TEXT,
        FOREIGN KEY(licencia_id) REFERENCES licencias(id))""")
        
    cur.execute("""CREATE TABLE IF NOT EXISTS licencias_log (
        id TEXT PRIMARY KEY, licencia_id TEXT, evento TEXT, detalle TEXT, ts TEXT, user TEXT,
        FOREIGN KEY(licencia_id) REFERENCES licencias(id))""")
        
    cur.execute("""CREATE TABLE IF NOT EXISTS licencias_seq (k TEXT PRIMARY KEY, n INTEGER)""")
    cur.execute("INSERT OR IGNORE INTO licencias_seq (k, n) VALUES ('seq', 0)")
    conn.commit(); conn.close()

# Run init
try: init_licencias_schema()
except: pass

def next_licencia_consecutivo():
    conn = get_sqlite(); cur = conn.cursor()
    cur.execute("UPDATE licencias_seq SET n = n + 1 WHERE k='seq'")
    conn.commit()
    cur.execute("SELECT n FROM licencias_seq WHERE k='seq'")
    n = cur.fetchone()['n']
    conn.close()
    return n

@solicitudes_bp.route('/licencias', endpoint='licencias_list')
def licencias_list():
    estado = (request.args.get('estado') or '').strip()
    q = (request.args.get('q') or '').strip()
    conn = get_sqlite(); cur = conn.cursor()
    base = "SELECT * FROM licencias WHERE eliminado=0"
    params = []
    if estado:
        base += " AND estado=?"; params.append(estado)
    if q:
        base += " AND (direccion LIKE ? OR solicitante LIKE ? OR doc_solicitante LIKE ? OR chip LIKE ? OR matricula LIKE ?)"
        like = f"%{q}%"; params += [like]*5
    base += " ORDER BY actualizado_en DESC"
    cur.execute(base, params)
    rows = cur.fetchall(); conn.close()
    
    items = []
    now = datetime.datetime.now()
    for r in rows:
        d = dict(r)
        try:
             creado = datetime.datetime.fromisoformat(d['creado_en'])
             dias = business_days_between(creado, now)
        except: dias = 0
        
        if dias <= 30: color = 'success'
        elif dias <= 45: color = 'warning'
        else: color = 'danger'
        d['dias_habiles'] = dias
        d['semaforo_color'] = color
        items.append(d)
        
    return render_template('licencias_list.html', rows=items, estado=estado, q=q)

@solicitudes_bp.route('/licencias/nueva', methods=['GET', 'POST'])
def licencias_nueva():
    if request.method == 'POST':
        f = request.form
        lid = str(uuid.uuid4())
        consec = next_licencia_consecutivo()
        now = datetime.datetime.now().isoformat(timespec='seconds')
        
        try: val = float(f.get('valor','0'))
        except: val = 0.0
        try: ac = float(f.get('area_const','0'))
        except: ac = 0.0
        try: al = float(f.get('area_lote','0'))
        except: al = 0.0

        conn = get_sqlite(); cur = conn.cursor()
        cur.execute("""INSERT INTO licencias (
            id, consecutivo, tipo, objeto, modalidad, direccion, chip, matricula,
            clasificacion_suelo, uso, uso_otro, area_const, area_lote,
            solicitante, tipo_doc_solicitante, doc_solicitante,
            responsable, matricula_prof, tipo_vivienda, bic,
            valor, estado, observaciones, creado_por, creado_en, actualizado_en
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            lid, consec, f.get('tipo'), f.get('objeto'), f.get('modalidad'), f.get('direccion'),
            f.get('chip'), f.get('matricula'), f.get('clasificacion_suelo'), f.get('uso'), f.get('uso_otro'),
            ac, al, f.get('solicitante'), f.get('tipo_doc_solicitante'), f.get('doc_solicitante'),
            f.get('responsable'), f.get('matricula_prof'), f.get('tipo_vivienda'), f.get('bic'),
            val, 'Radicada', f.get('observaciones'), session.get('user',''), now, now
        ))
        cur.execute("INSERT INTO licencias_log (id, licencia_id, evento, detalle, ts, user) VALUES (?,?,?,?,?,?)",
                    (str(uuid.uuid4()), lid, 'Creación', f'Radicada #{consec}', now, session.get('user','')))
        conn.commit(); conn.close()
        
        os.makedirs(os.path.join(current_app.config['UPLOADS_DIR'], 'licencias', lid), exist_ok=True)
        flash(f'Licencia radicada #{consec}', 'success')
        return redirect(url_for('solicitudes.licencias_detalle', licencia_id=lid))
        
    return render_template('licencias_form.html')

@solicitudes_bp.route('/licencias/<licencia_id>', methods=['GET','POST'])
def licencias_detalle(licencia_id):
    conn = get_sqlite(); cur = conn.cursor()
    cur.execute("SELECT * FROM licencias WHERE id=?", (licencia_id,))
    lic = cur.fetchone()
    if not lic: conn.close(); abort(404)
    
    if request.method == 'POST':
        estado = request.form.get('estado')
        obs = request.form.get('observaciones')
        now = datetime.datetime.now().isoformat(timespec='seconds')
        cur.execute("UPDATE licencias SET estado=?, observaciones=?, actualizado_en=? WHERE id=?",
                    (estado, obs, now, licencia_id))
        cur.execute("INSERT INTO licencias_log (id, licencia_id, evento, detalle, ts, user) VALUES (?,?,?,?,?,?)",
                    (str(uuid.uuid4()), licencia_id, 'Actualización', f"Estado: {estado}", now, session.get('user','')))
        conn.commit(); conn.close()
        flash('Actualizado', 'success')
        return redirect(url_for('solicitudes.licencias_detalle', licencia_id=licencia_id))

    cur.execute("SELECT * FROM licencias_archivos WHERE licencia_id=? ORDER BY uploaded_en DESC", (licencia_id,))
    archs = cur.fetchall()
    cur.execute("SELECT * FROM licencias_log WHERE licencia_id=? ORDER BY ts DESC", (licencia_id,))
    logs = cur.fetchall()
    conn.close()
    
    now_dt = datetime.datetime.now()
    try: creado_dt = datetime.datetime.fromisoformat(lic['creado_en'])
    except: creado_dt = now_dt
    dias = business_days_between(creado_dt, now_dt)
    color = 'success' if dias <= 30 else 'warning' if dias <= 45 else 'danger'
    
    return render_template('licencias_detalle.html', lic=lic, archivos=archs, bitacora=logs,
                           dias_habiles=dias, semaforo_color=color, is_admin=(session.get('user')=='admin'))

@solicitudes_bp.route('/licencias/detalle/<licencia_id>')
def licencias_detalle_legacy(licencia_id):
    return redirect(url_for('solicitudes.licencias_detalle', licencia_id=licencia_id))


# --- Endpoints faltantes para licencias_detalle.html ---

@solicitudes_bp.route('/licencias/<licencia_id>/pdf', endpoint='licencias_pdf')
def licencias_pdf(licencia_id):
    """Genera PDF de la licencia usando formato oficial de Alcaldía"""
    import os
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle, Paragraph
    from reportlab.lib.utils import ImageReader
    from PyPDF2 import PdfReader, PdfWriter
    from io import BytesIO
    import datetime
    
    try:
        conn = get_sqlite()
        cur = conn.cursor()
        
        # Obtener datos de la licencia
        cur.execute("SELECT * FROM licencias WHERE id=?", (licencia_id,))
        lic = cur.fetchone()
        if not lic:
            conn.close()
            abort(404)
        
        consec = lic['consecutivo'] or 'N/A'
        fecha_hoy = datetime.datetime.now().strftime("%d de %B de %Y").replace(
            "January", "enero").replace("February", "febrero").replace("March", "marzo"
        ).replace("April", "abril").replace("May", "mayo").replace("June", "junio"
        ).replace("July", "julio").replace("August", "agosto").replace("September", "septiembre"
        ).replace("October", "octubre").replace("November", "noviembre").replace("December", "diciembre")
        
        # ============ CREAR OVERLAY CON CONTENIDO ============
        overlay_buffer = BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=letter)
        w, h = letter  # 612 x 792
        
        # Estilos para el contenido
        styles = getSampleStyleSheet()
        
        # Estilo para header de sección
        header_section_style = ParagraphStyle(
            'HeaderSection',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1a472a'),
            spaceAfter=2,
            alignment=1,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para títulos del documento
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#1a472a'),
            spaceAfter=4,
            alignment=1,
            fontName='Helvetica-Bold'
        )
        
        subtitle_date_style = ParagraphStyle(
            'SubtitleDate',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#666666'),
            spaceAfter=6,
            alignment=1
        )
        
        cell_label_style = ParagraphStyle(
            'CellLabel',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#2d5016'),
            fontName='Helvetica-Bold',
            alignment=0
        )
        
        cell_value_style = ParagraphStyle(
            'CellValue',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#333333'),
            alignment=0
        )
        
        section_header_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.white,
            fontName='Helvetica-Bold',
            alignment=1,
            backColor=colors.HexColor('#558b2f')
        )
        
        # Margen y posición inicial
        margin = 60
        y_position = h - 150  # Debajo del logo oficial
        
        # ============ HEADER DE SECCIÓN ============
        header1 = Paragraph("SECRETARÍA DE PLANEACIÓN Y OBRAS PÚBLICAS", header_section_style)
        h1_w, h1_h = header1.wrap(w - 2*margin, 30)
        header1.drawOn(c, margin, y_position - h1_h)
        y_position -= (h1_h + 2)
        
        header2 = Paragraph("RADICACIÓN DE LICENCIAS URBANÍSTICAS", header_section_style)
        h2_w, h2_h = header2.wrap(w - 2*margin, 30)
        header2.drawOn(c, margin, y_position - h2_h)
        y_position -= (h2_h + 15)
        
        # ============ TÍTULO Y FECHA DEL DOCUMENTO ============
        title_para = Paragraph(f"LICENCIA #{consec:03d}", title_style)
        title_width, title_height = title_para.wrap(w - 2*margin, 50)
        title_para.drawOn(c, margin, y_position - title_height)
        y_position -= (title_height + 6)
        
        date_para = Paragraph(f"Expedido: {fecha_hoy}", subtitle_date_style)
        date_width, date_height = date_para.wrap(w - 2*margin, 30)
        date_para.drawOn(c, margin, y_position - date_height)
        y_position -= (date_height + 15)
        
        # ============ TABLA DE DATOS ============
        table_data = [
            # SECCIÓN 1: EXPEDIENTE
            [Paragraph('INFORMACIÓN DEL EXPEDIENTE', section_header_style), Paragraph('', section_header_style)],
            [Paragraph('Tipo de Licencia', cell_label_style), Paragraph(lic['tipo'] or 'N/A', cell_value_style)],
            [Paragraph('Modalidad', cell_label_style), Paragraph(lic['modalidad'] or 'N/A', cell_value_style)],
            [Paragraph('Objeto', cell_label_style), Paragraph(lic['objeto'] or 'N/A', cell_value_style)],
            [Paragraph('Estado del Trámite', cell_label_style), Paragraph(lic['estado'] or 'N/A', cell_value_style)],
            
            # SECCIÓN 2: INMUEBLE
            [Paragraph('INFORMACIÓN DEL INMUEBLE', section_header_style), Paragraph('', section_header_style)],
            [Paragraph('Dirección', cell_label_style), Paragraph(lic['direccion'] or 'N/A', cell_value_style)],
            [Paragraph('CHIP/Lote', cell_label_style), Paragraph(lic['chip'] or 'N/A', cell_value_style)],
            [Paragraph('Matrícula', cell_label_style), Paragraph(lic['matricula'] or 'N/A', cell_value_style)],
            [Paragraph('Clasificación Suelo', cell_label_style), Paragraph(lic['clasificacion_suelo'] or 'N/A', cell_value_style)],
            [Paragraph('Uso', cell_label_style), Paragraph(lic['uso'] or 'N/A', cell_value_style)],
            [Paragraph('Área Construida (m²)', cell_label_style), Paragraph(str(lic['area_const'] or 0), cell_value_style)],
            [Paragraph('Área del Lote (m²)', cell_label_style), Paragraph(str(lic['area_lote'] or 0), cell_value_style)],
            
            # SECCIÓN 3: SOLICITANTE
            [Paragraph('INFORMACIÓN DEL SOLICITANTE', section_header_style), Paragraph('', section_header_style)],
            [Paragraph('Nombre', cell_label_style), Paragraph(lic['solicitante'] or 'N/A', cell_value_style)],
            [Paragraph('Tipo de Documento', cell_label_style), Paragraph(lic['tipo_doc_solicitante'] or 'N/A', cell_value_style)],
            [Paragraph('Número de Documento', cell_label_style), Paragraph(lic['doc_solicitante'] or 'N/A', cell_value_style)],
        ]
        
        table = Table(table_data, colWidths=[1.8*72, 3.2*72])
        table.setStyle(TableStyle([
            # Encabezados de sección (verdes oscuros, centrados, span completo)
            ('SPAN', (0, 0), (-1, 0)),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#558b2f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            ('SPAN', (0, 5), (-1, 5)),
            ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#558b2f')),
            ('TEXTCOLOR', (0, 5), (-1, 5), colors.white),
            ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 5), (-1, 5), 9),
            ('ALIGN', (0, 5), (-1, 5), 'CENTER'),
            
            ('SPAN', (0, 13), (-1, 13)),
            ('BACKGROUND', (0, 13), (-1, 13), colors.HexColor('#558b2f')),
            ('TEXTCOLOR', (0, 13), (-1, 13), colors.white),
            ('FONTNAME', (0, 13), (-1, 13), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 13), (-1, 13), 9),
            ('ALIGN', (0, 13), (-1, 13), 'CENTER'),
            
            # Columna izquierda (labels): fondo verde muy claro
            ('BACKGROUND', (0, 1), (0, 4), colors.HexColor('#e8f5e9')),
            ('BACKGROUND', (0, 6), (0, 12), colors.HexColor('#e8f5e9')),
            ('BACKGROUND', (0, 14), (0, -1), colors.HexColor('#e8f5e9')),
            
            # Columna derecha (valores): fondo blanco
            ('BACKGROUND', (1, 1), (1, 4), colors.white),
            ('BACKGROUND', (1, 6), (1, 12), colors.white),
            ('BACKGROUND', (1, 14), (1, -1), colors.white),
            
            # Estilos generales
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ]))
        
        # Dibujar tabla centrada
        table_width, table_height = table.wrap(w - 2*margin, 600)
        table_x = (w - table_width) / 2
        table.drawOn(c, table_x, y_position - table_height)
        
        # FOOTER - Posicionado arriba de la franja verde del formato oficial
        footer_y = 82
        
        c.setFont("Helvetica", 6)
        c.setFillColor(colors.HexColor('#333333'))
        c.drawCentredString(w/2, footer_y, "Documento generado automáticamente por el Sistema de Gestión de Licencias Urbanísticas")
        
        footer_y -= 8
        c.setFont("Helvetica", 5)
        c.setFillColor(colors.HexColor('#666666'))
        c.drawCentredString(w/2, footer_y, "Validez de este certificado: A partir de la fecha de expedición. Para trámites posteriores, consulte en nuestras oficinas.")
        
        footer_y -= 8
        c.drawCentredString(w/2, footer_y, "Centro de Atención: Dirección de la Alcaldía (Carrera 7 No 4-14) | Horario: Lunes a Viernes 8:00 AM - 5:00 PM")
        
        c.save()
        overlay_buffer.seek(0)
        
        # ============ COMBINAR CON FORMATO OFICIAL ============
        formato_path = os.path.join(str(current_app.config['BASE_DIR']), 'datos', 'FORMATO.pdf')
        
        if os.path.exists(formato_path):
            # Usar formato oficial como base
            formato_pdf = PdfReader(formato_path)
            overlay_pdf = PdfReader(overlay_buffer)
            
            output = PdfWriter()
            base_page = formato_pdf.pages[0]
            overlay_page = overlay_pdf.pages[0]
            
            base_page.merge_page(overlay_page)
            output.add_page(base_page)
            
            final_buffer = BytesIO()
            output.write(final_buffer)
            final_buffer.seek(0)
        else:
            # Si no existe FORMATO.pdf, usar el overlay directamente
            final_buffer = overlay_buffer
        
        conn.close()
        
        return send_file(
            final_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"Licencia_{consec:03d}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
        )
    except Exception as e:
        flash(f'Error generando PDF: {str(e)}', 'error')
        return redirect(url_for('solicitudes.licencias_detalle', licencia_id=licencia_id))


@solicitudes_bp.route('/licencias/<licencia_id>/consecutivo', methods=['POST'], endpoint='licencias_set_consecutivo')
def licencias_set_consecutivo(licencia_id):
    """Asigna consecutivo a la licencia"""
    try:
        cons = request.form.get('consecutivo', '').strip()
        conn = get_sqlite()
        cur = conn.cursor()
        cur.execute("UPDATE licencias SET consecutivo=? WHERE id=?", (cons, licencia_id))
        conn.commit()
        conn.close()
        flash('Consecutivo actualizado', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('solicitudes.licencias_detalle', licencia_id=licencia_id))


@solicitudes_bp.route('/licencias/<licencia_id>/eliminar', methods=['POST'], endpoint='licencias_eliminar')
def licencias_eliminar(licencia_id):
    """Marca la licencia como eliminada"""
    try:
        conn = get_sqlite()
        cur = conn.cursor()
        cur.execute("UPDATE licencias SET eliminado=1 WHERE id=?", (licencia_id,))
        conn.commit()
        conn.close()
        flash('Licencia eliminada', 'success')
        return redirect(url_for('solicitudes.licencias_list'))
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('solicitudes.licencias_detalle', licencia_id=licencia_id))


@solicitudes_bp.route('/licencias/<licencia_id>/acta', endpoint='licencias_descargar_acta')
def licencias_descargar_acta(licencia_id):
    """Descarga el acta de la licencia"""
    try:
        conn = get_sqlite()
        cur = conn.cursor()
        cur.execute("SELECT * FROM licencias WHERE id=?", (licencia_id,))
        lic = cur.fetchone()
        conn.close()
        
        if not lic or not lic['acta_path']:
            flash('Acta no disponible', 'warning')
            return redirect(url_for('solicitudes.licencias_detalle', licencia_id=licencia_id))
        
        acta_path = lic['acta_path']
        if os.path.exists(acta_path):
            return send_file(acta_path, as_attachment=True, download_name=f"acta_{licencia_id}.pdf")
        else:
            flash('Archivo no encontrado', 'danger')
            return redirect(url_for('solicitudes.licencias_detalle', licencia_id=licencia_id))
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('solicitudes.licencias_detalle', licencia_id=licencia_id))


@solicitudes_bp.route('/licencias/<licencia_id>/acta-subir', methods=['POST'], endpoint='licencias_subir_acta')
def licencias_subir_acta(licencia_id):
    """Sube el acta de la licencia"""
    try:
        if 'acta' not in request.files:
            flash('No se envió archivo', 'danger')
            return redirect(url_for('solicitudes.licencias_detalle', licencia_id=licencia_id))
        
        file = request.files['acta']
        if file.filename == '':
            flash('Archivo vacío', 'danger')
            return redirect(url_for('solicitudes.licencias_detalle', licencia_id=licencia_id))
        
        filename = secure_filename(file.filename)
        upload_dir = current_app.config['UPLOADS_DIR'] / 'licencias'
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, f"{licencia_id}_{filename}")
        file.save(filepath)
        
        conn = get_sqlite()
        cur = conn.cursor()
        cur.execute("UPDATE licencias SET acta_path=? WHERE id=?", (filepath, licencia_id))
        conn.commit()
        conn.close()
        
        flash('Acta subida correctamente', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    
    return redirect(url_for('solicitudes.licencias_detalle', licencia_id=licencia_id))


@solicitudes_bp.route('/licencias/<licencia_id>/archivos-subir', methods=['POST'], endpoint='licencias_subir')
def licencias_subir(licencia_id):
    """Sube archivos a la licencia"""
    try:
        if 'archivos' not in request.files:
            flash('No se envió archivo', 'danger')
            return redirect(url_for('solicitudes.licencias_detalle', licencia_id=licencia_id))
        
        files = request.files.getlist('archivos')
        upload_dir = current_app.config['UPLOADS_DIR'] / 'licencias'
        os.makedirs(upload_dir, exist_ok=True)
        
        conn = get_sqlite()
        cur = conn.cursor()
        
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(upload_dir, f"{licencia_id}_{filename}")
                file.save(filepath)
                
                file_id = str(uuid.uuid4())
                cur.execute("""INSERT INTO licencias_archivos 
                    (id, licencia_id, filename, filepath, uploaded_en)
                    VALUES (?, ?, ?, ?, ?)""",
                    (file_id, licencia_id, filename, filepath, datetime.datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        flash(f'{len(files)} archivo(s) subido(s) correctamente', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    
    return redirect(url_for('solicitudes.licencias_detalle', licencia_id=licencia_id))


@solicitudes_bp.route('/licencias/archivo/<archivo_id>', endpoint='licencias_archivo_descargar')
def licencias_archivo_descargar(archivo_id):
    """Descarga un archivo de la licencia"""
    try:
        conn = get_sqlite()
        cur = conn.cursor()
        cur.execute("SELECT filepath FROM licencias_archivos WHERE id=?", (archivo_id,))
        arch = cur.fetchone()
        conn.close()
        
        if not arch or not os.path.exists(arch['filepath']):
            flash('Archivo no encontrado', 'danger')
            return redirect(url_for('solicitudes.licencias_list'))
        
        return send_file(arch['filepath'], as_attachment=True)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('solicitudes.licencias_list'))
