from flask import (Blueprint, Response, session, redirect, url_for,
                   current_app, flash, render_template, jsonify, request)
import os, json, uuid, re
from datetime import datetime
from app.utils import get_sqlite

licencias_bp = Blueprint('licencias', __name__)

# ─── Mapas ──────────────────────────────────────────────────────────────────

_TIPO_COD = {
    'Licencia de Construcción': 'LC',
    'Licencia de Parcelación': 'LP',
    'Licencia de Subdivisión': 'LS',
    'Reconocimiento de Edificación': 'RE',
}

_KNOWN_RADS = {
    4:  'SPO-LC-25777010000000-24032026-004',
    6:  'SPO-RE-25777010000000-24032026-006',
    7:  'SPO-LS-25777000100000-25032026-007',
    8:  'SPO-LS-25777010000000-25032026-008',
    9:  'SPO-LS-25777000200000-25032026-009',
    10: 'SPO-LC-25777010000000-26032026-010',
    11: 'SPO-LC-25777000100000-13042026-011',
    12: 'SPO-LC-25777000100000-13042026-012',
    13: 'SPO-LC-25777010000000-20042026-013',
    14: 'SPO-LP-25777000100000-20042026-014',
    15: 'SPO-LS-25777000100000-22042026-015',
}

# ─── Helpers de acceso ──────────────────────────────────────────────────────

def _puede_acceder():
    if not session.get('user'):
        return False
    role       = session.get('role', '').lower()
    secretaria = session.get('secretaria', '').lower()
    usuario    = session.get('user', '').lower()
    return (role == 'admin'
            or 'planeacion' in secretaria
            or 'planeacion' in role
            or '(planeacion)' in usuario)

def _guard():
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    if not _puede_acceder():
        flash('El módulo de Licencias es exclusivo del área de Planeación.', 'warning')
        return redirect(url_for('main.dashboard'))
    return None

def _html_dir():
    return os.path.join(str(current_app.config['BASE_DIR']),
                        'documentos_generados', 'licencias')

def _uploads_dir():
    base = current_app.config.get('UPLOADS_DIR')
    if base:
        return str(base)
    return os.path.join(str(current_app.config.get('BASE_DIR', '')), 'uploads')

# ─── Migración y schema ──────────────────────────────────────────────────────

def _migrate_bp():
    """Agrega columna radicado_str si no existe y rellena registros conocidos."""
    try:
        conn = get_sqlite()
        cols = [r[1] for r in conn.execute("PRAGMA table_info(licencias)").fetchall()]
        if 'radicado_str' not in cols:
            conn.execute("ALTER TABLE licencias ADD COLUMN radicado_str TEXT")
            conn.commit()
        for consec, rad_str in _KNOWN_RADS.items():
            conn.execute(
                "UPDATE licencias SET radicado_str=? WHERE consecutivo=? "
                "AND (radicado_str IS NULL OR radicado_str='')",
                (rad_str, consec))
        conn.commit()
        conn.close()
    except Exception:
        pass

# ─── Construcción de pkg (formato localStorage) ──────────────────────────────

def _pkg_from_db(consecutivo):
    """Devuelve dict en formato pkg para inyectar en localStorage del HTML."""
    try:
        conn = get_sqlite()
        row = conn.execute("""
            SELECT consecutivo, radicado_str, tipo, modalidad, solicitante, direccion,
                   matricula, chip, area_const, uso, creado_en,
                   doc_solicitante, tipo_doc_solicitante
            FROM licencias
            WHERE consecutivo=? AND (eliminado IS NULL OR eliminado=0)
        """, (consecutivo,)).fetchone()
        conn.close()
        if not row:
            return None
        r = dict(row)
        mod = _TIPO_COD.get(r.get('tipo', ''), 'LC')
        rad_str = r.get('radicado_str') or _KNOWN_RADS.get(consecutivo, f'SPO-{mod}-{consecutivo:03d}')
        return {
            'radicado': rad_str,
            'fecha': r['creado_en'][:10] if r.get('creado_en') else '',
            'mod': mod, 'modLabel': r.get('tipo', ''),
            'subMod': r.get('modalidad') or '',
            'debida': True,
            'sol': {
                'nombre': r.get('solicitante') or '',
                'tipoDoc': r.get('tipo_doc_solicitante') or '',
                'cedula': r.get('doc_solicitante') or '',
                'tel': '', 'email': '', 'calidad': '', 'propietarios': []
            },
            'predio': {
                'nombre': r.get('direccion') or '',
                'matricula': r.get('matricula') or '',
                'catastral': r.get('chip') or '',
                'vereda': '',
                'area': str(r['area_const']) if r.get('area_const') else '',
                'uso': r.get('uso') or ''
            },
            'proyecto': {}, 'docs': [], 'func': '', 'obs': ''
        }
    except Exception:
        return None

# ─── Servir HTMLs standalone ─────────────────────────────────────────────────

def _serve(filename, preload_rad=None):
    """Sirve HTML standalone inyectando datos de DB en localStorage + sidebar."""
    path = os.path.join(_html_dir(), filename)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    parts = ['<script>', 'window.__PLATFORM_BACK="/licencias/plataforma";']

    if preload_rad is not None:
        consecutivo = None
        try:
            consecutivo = int(preload_rad)
        except (ValueError, TypeError):
            m = re.search(r'-(\d{1,3})$', str(preload_rad))
            if m:
                consecutivo = int(m.group(1))

        parts.append(f'window.__PRELOAD_RAD="{preload_rad}";')

        if consecutivo:
            pkg = _pkg_from_db(consecutivo)
            if pkg:
                pkg_json = json.dumps(pkg, ensure_ascii=False)
                parts.append(
                    f'try{{localStorage.setItem("spo_rad_{consecutivo}",'
                    f'{repr(pkg_json)});'
                    f'localStorage.setItem("spo_last","{consecutivo}");}}catch(e){{}}'
                )

    parts.append('</script>')
    inject_head = '\n'.join(parts) + '\n'
    content = content.replace('<head>', '<head>\n' + inject_head, 1)

    sidebar = '<script src="/static/js/licencias_sidebar.js"></script>\n'
    content = content.replace('</body>', sidebar + '</body>', 1)

    return Response(content, mimetype='text/html')

# ─── Stats y listado ─────────────────────────────────────────────────────────

def _stats():
    try:
        conn = get_sqlite()
        estados = ['Radicada', 'En revisión', 'Subsanación', 'Aprobada', 'Negada']
        s = {}
        for e in estados:
            row = conn.execute(
                "SELECT COUNT(*) n FROM licencias "
                "WHERE estado=? AND (eliminado IS NULL OR eliminado=0)", (e,)).fetchone()
            s[e] = row['n'] if row else 0
        s['total'] = sum(s.values())
        conn.close()
        return s
    except Exception:
        return {e: 0 for e in ['Radicada', 'En revisión', 'Subsanación', 'Aprobada', 'Negada', 'total']}

def _licencias_recientes(limit=60):
    try:
        conn = get_sqlite()
        rows = conn.execute("""
            SELECT id, consecutivo, radicado_str, tipo, modalidad, solicitante, direccion,
                   estado, creado_en, area_const, creado_por
            FROM licencias
            WHERE eliminado IS NULL OR eliminado=0
            ORDER BY creado_en DESC LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []

# ─── Rutas de vista ──────────────────────────────────────────────────────────

@licencias_bp.route('/licencias')
def landing():
    g = _guard()
    if g: return g
    _migrate_bp()
    return render_template('licencias_landing.html')


@licencias_bp.route('/licencias/plataforma')
def plataforma():
    g = _guard()
    if g: return g
    _migrate_bp()
    return render_template('licencias_plataforma.html',
                           stats=_stats(),
                           licencias=_licencias_recientes(),
                           usuario=session.get('user', ''))


@licencias_bp.route('/licencias/radicar')
def radicar():
    g = _guard()
    if g: return g
    return _serve('html_radicacion_supata_con_valla_y_vecinos_v2.html')


@licencias_bp.route('/licencias/acta')
@licencias_bp.route('/licencias/acta/<radicado>')
def acta(radicado=None):
    g = _guard()
    if g: return g
    return _serve('acta_observaciones_supata.html', radicado)


@licencias_bp.route('/licencias/subsanacion')
@licencias_bp.route('/licencias/subsanacion/<radicado>')
def subsanacion(radicado=None):
    g = _guard()
    if g: return g
    return _serve('html3_revision_subsanacion_supata.html', radicado)


@licencias_bp.route('/licencias/liquidador')
@licencias_bp.route('/licencias/liquidador/<int:consecutivo>')
def liquidador(consecutivo=None):
    g = _guard()
    if g: return g
    if consecutivo:
        try:
            conn = get_sqlite()
            row = conn.execute(
                "SELECT estado FROM licencias "
                "WHERE consecutivo=? AND (eliminado IS NULL OR eliminado=0)",
                (consecutivo,)).fetchone()
            conn.close()
            if not row:
                flash('No se encontró el expediente solicitado.', 'warning')
                return redirect(url_for('licencias.plataforma'))
            if row['estado'] != 'Aprobada':
                flash(
                    f'El liquidador solo está disponible para expedientes Aprobados. '
                    f'Estado actual: {row["estado"]}.', 'warning')
                return redirect(url_for('licencias.plataforma'))
        except Exception:
            pass
    return _serve('liquidador_delineacion_supata.html', consecutivo)


@licencias_bp.route('/licencias/archivos/<path:filepath>')
def serve_archivo(filepath):
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    from flask import send_from_directory
    return send_from_directory(_uploads_dir(), filepath)


# ─── API JSON ────────────────────────────────────────────────────────────────

@licencias_bp.route('/licencias/api/stats')
def api_stats():
    if not _puede_acceder():
        return jsonify({'error': 'forbidden'}), 403
    return jsonify(_stats())


@licencias_bp.route('/licencias/api/lista')
def api_lista():
    if not _puede_acceder():
        return jsonify({'error': 'forbidden'}), 403
    return jsonify(_licencias_recientes(100))


@licencias_bp.route('/licencias/api/radicado/<int:consecutivo>')
def api_radicado(consecutivo):
    if not _puede_acceder():
        return jsonify({'error': 'forbidden'}), 403
    try:
        conn = get_sqlite()
        row = conn.execute("""
            SELECT id, consecutivo, radicado_str, tipo, modalidad, solicitante,
                   direccion, matricula, chip, area_const, uso, estado, creado_en
            FROM licencias
            WHERE consecutivo=? AND (eliminado IS NULL OR eliminado=0)
        """, (consecutivo,)).fetchone()
        conn.close()
        if not row:
            return jsonify({'error': 'no encontrado'}), 404
        r = dict(row)
        pkg = _pkg_from_db(consecutivo)
        return jsonify({
            'pkg': pkg,
            'db': {
                'id': r['id'], 'consecutivo': consecutivo,
                'estado': r.get('estado', ''),
                'solicitante': r.get('solicitante', ''),
                'radicado_str': r.get('radicado_str') or '',
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@licencias_bp.route('/licencias/api/guardar', methods=['POST'])
def api_guardar():
    """Guarda radicado desde HTML de radicación en la BD."""
    if not _puede_acceder():
        return jsonify({'error': 'forbidden'}), 403
    data = request.get_json(silent=True) or {}
    pkg  = data.get('pkg', {})
    try:
        consecutivo = int(data.get('consecutivo', 0))
    except Exception:
        return jsonify({'error': 'consecutivo inválido'}), 400
    if not consecutivo:
        return jsonify({'error': 'datos incompletos'}), 400

    sol    = pkg.get('sol', {})
    predio = pkg.get('predio', {})
    rad_str  = pkg.get('radicado', '')
    tipo     = pkg.get('modLabel', '')
    modalidad = pkg.get('subMod', '')

    try:
        conn = get_sqlite()
        existing = conn.execute(
            'SELECT id, radicado_str FROM licencias WHERE consecutivo=?',
            (consecutivo,)).fetchone()

        if existing:
            if not existing['radicado_str'] and rad_str:
                conn.execute('UPDATE licencias SET radicado_str=? WHERE consecutivo=?',
                             (rad_str, consecutivo))
                conn.commit()
            conn.close()
            return jsonify({'ok': True, 'id': existing['id'], 'nuevo': False})

        area = None
        try:
            v = predio.get('area', '')
            if v:
                area = float(str(v).replace(',', '.').replace('m2', '').strip())
        except Exception:
            pass

        lid = str(uuid.uuid4())
        conn.execute("""
            INSERT INTO licencias
              (id, consecutivo, radicado_str, tipo, modalidad, solicitante, direccion,
               matricula, chip, area_const, uso, estado, creado_en, creado_por, eliminado)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)
        """, (lid, consecutivo, rad_str, tipo, modalidad,
              sol.get('nombre', ''), predio.get('nombre', ''),
              predio.get('matricula', ''), predio.get('catastral', ''),
              area, predio.get('uso', ''), 'Radicada',
              pkg.get('fecha', datetime.now().date().isoformat()),
              session.get('user', 'sistema')))
        conn.execute("""
            INSERT INTO licencias_log (id,licencia_id,evento,detalle,ts,user)
            VALUES (?,?,?,?,?,?)
        """, (str(uuid.uuid4()), lid, 'Creado',
              'Radicado desde formulario HTML',
              datetime.now().isoformat(), session.get('user', 'sistema')))
        conn.commit(); conn.close()
        return jsonify({'ok': True, 'id': lid, 'nuevo': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@licencias_bp.route('/licencias/api/eliminar/<licencia_id>', methods=['POST'])
def api_eliminar(licencia_id):
    if not _puede_acceder():
        return jsonify({'error': 'forbidden'}), 403
    try:
        conn = get_sqlite()
        conn.execute("UPDATE licencias SET eliminado=1 WHERE id=?", (licencia_id,))
        conn.execute(
            "INSERT INTO licencias_log (id,licencia_id,evento,detalle,ts,user) VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4()), licencia_id, 'Eliminada', 'Eliminada desde plataforma',
             datetime.now().isoformat(), session.get('user', '')))
        conn.commit(); conn.close()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@licencias_bp.route('/licencias/api/estado/<licencia_id>', methods=['POST'])
def api_estado(licencia_id):
    if not _puede_acceder():
        return jsonify({'error': 'forbidden'}), 403
    data  = request.get_json(silent=True) or {}
    nuevo = data.get('estado', '').strip()
    validos = ['Radicada', 'En revisión', 'Subsanación', 'Aprobada', 'Negada']
    if nuevo not in validos:
        return jsonify({'error': 'estado inválido'}), 400
    try:
        conn = get_sqlite()
        conn.execute("UPDATE licencias SET estado=?, actualizado_en=? WHERE id=?",
                     (nuevo, datetime.now().isoformat(), licencia_id))
        conn.execute(
            "INSERT INTO licencias_log (id,licencia_id,evento,detalle,ts,user) VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4()), licencia_id, 'Cambio estado',
             f'-> {nuevo}', datetime.now().isoformat(), session.get('user', '')))
        conn.commit(); conn.close()
        return jsonify({'ok': True, 'estado': nuevo})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@licencias_bp.route('/licencias/api/upload/<licencia_id>', methods=['POST'])
def api_upload(licencia_id):
    if not _puede_acceder():
        return jsonify({'error': 'forbidden'}), 403
    from werkzeug.utils import secure_filename
    f = request.files.get('file')
    if not f or not f.filename:
        return jsonify({'error': 'sin archivo'}), 400
    filename = secure_filename(f.filename)
    dest_dir = os.path.join(_uploads_dir(), 'licencias', licencia_id)
    os.makedirs(dest_dir, exist_ok=True)
    f.save(os.path.join(dest_dir, filename))
    rel = f'licencias/{licencia_id}/{filename}'
    conn = get_sqlite()
    fid = str(uuid.uuid4())
    conn.execute("""
        INSERT INTO licencias_archivos (id,licencia_id,filename,path,uploaded_en,uploaded_por)
        VALUES (?,?,?,?,?,?)
    """, (fid, licencia_id, filename, rel,
          datetime.now().isoformat(), session.get('user', '')))
    conn.commit(); conn.close()
    return jsonify({'ok': True, 'id': fid, 'filename': filename, 'path': rel})


@licencias_bp.route('/licencias/api/archivos/<licencia_id>')
def api_archivos(licencia_id):
    if not _puede_acceder():
        return jsonify({'error': 'forbidden'}), 403
    try:
        conn = get_sqlite()
        rows = conn.execute("""
            SELECT id, filename, path, uploaded_en, uploaded_por
            FROM licencias_archivos WHERE licencia_id=?
            ORDER BY uploaded_en DESC
        """, (licencia_id,)).fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
