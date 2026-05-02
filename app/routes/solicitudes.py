import os
import csv
import uuid
import json
import datetime
import datetime as dt
from datetime import timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, session, abort, current_app, jsonify
from werkzeug.utils import secure_filename
from app.utils import get_sqlite, dias_restantes, color_semaforo_dias, admin_required, load_plan_desarrollo, is_admin, current_session_user, current_session_secretaria
from app import db

solicitudes_bp = Blueprint('solicitudes', __name__)

# ─────────────────────────────────────────────────────────────────────────────
# CSV: columnas y migración automática
# ─────────────────────────────────────────────────────────────────────────────

_CSV_HEADERS = [
    'municipio', 'nit', 'fecha', 'secretaria', 'objeto',
    'justificacion', 'valor', 'meta_producto', 'eje', 'sector',
    'codigo_bpim', 'estado', 'creado_por'
]


def _migrar_csv_si_necesario(path):
    """
    Garantiza que el CSV tenga la columna 'creado_por'.
    Si el archivo no existe, lo crea con el header correcto.
    Si existe pero no tiene 'creado_por', agrega la columna conservando todos
    los datos existentes (las filas antiguas quedan con creado_por vacío).
    """
    str_path = str(path)
    try:
        if not os.path.exists(str_path):
            os.makedirs(os.path.dirname(str_path), exist_ok=True)
            with open(str_path, 'w', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow(_CSV_HEADERS)
            return

        with open(str_path, 'r', encoding='utf-8') as f:
            rows = list(csv.reader(f))

        if not rows:
            with open(str_path, 'w', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow(_CSV_HEADERS)
            return

        if 'creado_por' not in rows[0]:
            rows[0].append('creado_por')
            for i in range(1, len(rows)):
                rows[i].append('')   # solicitudes antiguas sin autor
            with open(str_path, 'w', newline='', encoding='utf-8') as f:
                csv.writer(f).writerows(rows)

    except Exception as e:
        print(f"[solicitudes] Error en migración CSV: {e}")


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

    # Garantizar que el CSV tiene la columna creado_por antes de cualquier lectura
    _migrar_csv_si_necesario(path)

    if request.method == 'POST':
        raw_val = request.form.get('valor','').strip()
        try:
            num = int(raw_val.replace('.', ''))
            valor_formatted = '$ ' + '{:,.0f}'.format(num).replace(',', '.')
        except ValueError:
            valor_formatted = raw_val

        # Registrar quién crea la solicitud
        autor = session.get('user', '')

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
            'nuevo',   # Estado inicial
            autor      # ← quién creó la solicitud
        ]

        try:
            with open(str(path), 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
            flash('✅ Solicitud guardada correctamente.', 'success')
        except Exception as e:
            flash(f'Error guardando solicitud: {e}', 'danger')

        return redirect(url_for('solicitudes.index'))

    # Load Plan de Desarrollo data
    plan_list = load_plan_desarrollo()

    # ─────────────────────────────────────────────────────────────────────
    # Cargar solicitudes con filtro correcto:
    #   Admin  → ve TODAS las solicitudes de todos los usuarios.
    #   Normal → ve SOLO las solicitudes que él mismo creó (creado_por).
    #   Las solicitudes antiguas sin creado_por solo las ve el admin.
    # ─────────────────────────────────────────────────────────────────────
    user_solicitudes = []
    _admin_user   = is_admin()
    _usuario_actual = current_session_user()   # session['user']

    try:
        if os.path.exists(str(path)):
            with open(str(path), 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for csv_idx, row in enumerate(reader):
                    creado_por = row.get('creado_por', '').strip()

                    if not _admin_user:
                        # Usuario normal: solo ve sus propias solicitudes
                        if creado_por != _usuario_actual:
                            continue

                    user_solicitudes.append({
                        '_csv_idx':    csv_idx,          # ← índice real en el CSV (0-based)
                        'municipio':   row.get('municipio', ''),
                        'nit':         row.get('nit', ''),
                        'fecha':       row.get('fecha', ''),
                        'secretaria':  row.get('secretaria', ''),
                        'objeto':      row.get('objeto', ''),
                        'justificacion': row.get('justificacion', ''),
                        'valor':       row.get('valor', ''),
                        'meta_producto': row.get('meta_producto', ''),
                        'eje':         row.get('eje', ''),
                        'sector':      row.get('sector', ''),
                        'codigo_bpim': row.get('codigo_bpim', ''),
                        'estado':      row.get('estado', 'borrador'),
                        'creado_por':  creado_por,
                    })
    except Exception as e:
        print(f"Error cargando solicitudes: {e}")

    return render_template(
        'solicitudes_modern.html',
        secretarias=secretarias,
        plan_list=plan_list,
        user_solicitudes=user_solicitudes,
        today=dt.date.today().isoformat(),
        is_admin=_admin_user
    )


@solicitudes_bp.route('/solicitudes/editar', methods=['POST'], endpoint='editar_solicitud')
def editar_solicitud():
    """Edita una solicitud existente en el CSV (usa índice real del CSV)."""
    path = current_app.config['SOLICITUDES_PATH']

    try:
        indice = int(request.form.get('indice', -1))

        # Leer todas las filas
        with open(str(path), 'r', encoding='utf-8') as f:
            rows = list(csv.reader(f))

        # rows[0] = header; rows[indice+1] = fila de datos con índice 'indice'
        if indice < 0 or indice >= len(rows) - 1:
            flash('❌ Solicitud no encontrada', 'danger')
            return redirect(url_for('solicitudes.index'))

        fila_actual = rows[indice + 1]

        # Formatear valor
        raw_val = request.form.get('valor', '').strip()
        try:
            num = int(raw_val.replace('$', '').replace('.', '').replace(',', '').strip())
            valor_formatted = '$ ' + '{:,.0f}'.format(num).replace(',', '.')
        except ValueError:
            valor_formatted = raw_val

        # Siempre marcamos como editado para reactivar el flujo hacia certificados
        nuevo_estado = 'editado'

        # Preservar 'creado_por' (columna 12) — no sobrescribir al editar
        creado_por_original = fila_actual[12] if len(fila_actual) > 12 else ''

        rows[indice + 1] = [
            request.form.get('municipio', fila_actual[0] if fila_actual else '').strip(),
            request.form.get('nit',       fila_actual[1] if len(fila_actual) > 1 else '').strip(),
            request.form.get('fecha', ''),
            request.form.get('secretaria', ''),
            request.form.get('objeto', '').strip(),
            request.form.get('justificacion', '').strip(),
            valor_formatted,
            request.form.get('meta_producto', ''),
            request.form.get('eje',         fila_actual[8]  if len(fila_actual) > 8  else ''),
            request.form.get('sector',      fila_actual[9]  if len(fila_actual) > 9  else ''),
            request.form.get('codigo_bpim', fila_actual[10] if len(fila_actual) > 10 else ''),
            nuevo_estado,
            creado_por_original,   # ← preservar autoría original
        ]

        with open(str(path), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
            f.flush()
            os.fsync(f.fileno())

        flash('✅ Solicitud actualizada correctamente', 'success')
    except Exception as e:
        flash(f'❌ Error actualizando solicitud: {e}', 'danger')

    return redirect(url_for('solicitudes.index'))


@solicitudes_bp.route('/solicitudes/enviar_certificado', methods=['POST'], endpoint='enviar_certificado')
def enviar_certificado():
    """Marca una solicitud como lista para generar certificado (usa índice real del CSV)."""
    path = current_app.config['SOLICITUDES_PATH']

    try:
        indice = int(request.form.get('indice', -1))

        with open(str(path), 'r', encoding='utf-8') as f:
            rows = list(csv.reader(f))

        if indice < 0 or indice >= len(rows) - 1:
            flash('❌ Solicitud no encontrada', 'danger')
            return redirect(url_for('solicitudes.index'))

        row_index = indice + 1

        # Actualizar estado a "pendiente" (columna 11), preservar las demás columnas
        if len(rows[row_index]) > 11:
            rows[row_index][11] = 'pendiente'
        else:
            while len(rows[row_index]) < 12:
                rows[row_index].append('')
            rows[row_index][11] = 'pendiente'

        # Asegurar que la columna creado_por (12) exista y se preserve
        if len(rows[row_index]) < 13:
            rows[row_index].append('')

        with open(str(path), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
            f.flush()
            os.fsync(f.fileno())

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
    # Control de acceso: admin ve todo; usuarios normales solo sus solicitudes
    if not is_admin():
        base += " AND creado_por=?"; params.append(current_session_user())
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
    
    hoy = datetime.datetime.now()

    # Días del mes anterior para rellenar la primera semana
    primer_dia = datetime.date(año, mes, 1)
    ultimo_prev = primer_dia - datetime.timedelta(days=1)
    prev_last_day = ultimo_prev.day  # último día del mes anterior

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
        usuario_id=usuario_id,
        now_day=hoy.day,
        now_mes=hoy.month,
        now_año=hoy.year,
        prev_last_day=prev_last_day,
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

# Rutas de licencias movidas a app/routes/licencias_bp.py
