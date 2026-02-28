"""
API Endpoints para Actas CMGR, Damnificados y Registro de Daños
Blueprint: riesgo_actas_api  (prefix /api/actas)
"""
from flask import Blueprint, request, jsonify, session, current_app
from datetime import datetime, timedelta
import json
import logging
import os

logger = logging.getLogger(__name__)

riesgo_actas_api = Blueprint('riesgo_actas_api', __name__, url_prefix='/api/actas')


# ── lazy imports ────────────────────────────────────────────────────────────

def _db():
    from app import db
    return db


def _models():
    from app.models.riesgo_actas import ActaCMGR, Damnificado, RegistroDano
    return ActaCMGR, Damnificado, RegistroDano


def _usuario():
    return session.get('user', 'Sistema')


def _check_actas_perm():
    """Devuelve (True, None) o (False, Response 403) si no hay permiso."""
    from app.utils import can_risk_submodule
    if not can_risk_submodule('actas'):
        return False, (jsonify({
            'error': 'Acceso denegado',
            'mensaje': 'No tienes permisos para el submódulo Actas CMGR.'
        }), 403)
    return True, None


def _filtro_actas(query, Model):
    """Filtra por usuario_creador salvo admin."""
    rol     = session.get('role', '')
    usuario = session.get('user', '')
    if rol == 'admin':
        return query
    return query.filter(Model.usuario_creador == usuario)


# ============================================================================
# ACTAS CMGR
# ============================================================================

@riesgo_actas_api.route('/cmgr', methods=['GET'])
def listar_actas():
    """GET /api/actas/cmgr?page=1&limit=20&q=texto&desde=YYYY-MM-DD&hasta=YYYY-MM-DD"""
    ok, err = _check_actas_perm()
    if not ok:
        return err
    try:
        ActaCMGR, _, _ = _models()
        page  = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        q     = request.args.get('q', '').strip()
        desde = request.args.get('desde', '')
        hasta = request.args.get('hasta', '')

        query = _filtro_actas(ActaCMGR.query, ActaCMGR)

        if q:
            query = query.filter(
                ActaCMGR.numero_acta.ilike(f'%{q}%') |
                ActaCMGR.tema_principal.ilike(f'%{q}%')
            )
        if desde:
            try:
                query = query.filter(ActaCMGR.fecha >= datetime.strptime(desde, '%Y-%m-%d').date())
            except ValueError:
                pass
        if hasta:
            try:
                query = query.filter(ActaCMGR.fecha <= datetime.strptime(hasta, '%Y-%m-%d').date())
            except ValueError:
                pass

        total  = query.count()
        actas  = query.order_by(ActaCMGR.fecha.desc()).offset((page - 1) * limit).limit(limit).all()

        return jsonify({
            'total': total,
            'page':  page,
            'items': [a.to_dict() for a in actas]
        })
    except Exception as e:
        logger.error(f"listar_actas: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@riesgo_actas_api.route('/cmgr', methods=['POST'])
def crear_acta():
    """POST /api/actas/cmgr  — crea nueva acta"""
    ok, err = _check_actas_perm()
    if not ok:
        return err
    try:
        db = _db()
        ActaCMGR, _, _ = _models()
        data = request.get_json(force=True) or {}

        acta = ActaCMGR()
        acta.fecha          = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        acta.tema_principal = data.get('tema_principal', '')
        acta.asistentes     = json.dumps(data.get('asistentes', []), ensure_ascii=False)
        acta.acuerdos       = data.get('acuerdos', '')
        acta.compromisos    = json.dumps(data.get('compromisos', []), ensure_ascii=False)
        acta.resumen        = data.get('resumen', '')
        acta.observaciones  = data.get('observaciones', '')
        acta.usuario_creador = _usuario()

        db.session.add(acta)
        db.session.flush()          # get id
        acta.generar_numero()       # ACTA-2026-001
        db.session.commit()

        return jsonify({'ok': True, 'acta': acta.to_dict()}), 201
    except KeyError as ke:
        return jsonify({'error': f'Campo requerido: {ke}'}), 400
    except Exception as e:
        logger.error(f"crear_acta: {e}", exc_info=True)
        _db().session.rollback()
        return jsonify({'error': str(e)}), 500


@riesgo_actas_api.route('/cmgr/<int:acta_id>', methods=['GET'])
def obtener_acta(acta_id):
    try:
        ActaCMGR, _, _ = _models()
        acta = ActaCMGR.query.get_or_404(acta_id)
        return jsonify(acta.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@riesgo_actas_api.route('/cmgr/<int:acta_id>', methods=['PUT'])
def actualizar_acta(acta_id):
    try:
        db = _db()
        ActaCMGR, _, _ = _models()
        acta = ActaCMGR.query.get_or_404(acta_id)
        data = request.get_json(force=True) or {}

        if 'fecha' in data:
            acta.fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        if 'tema_principal' in data:
            acta.tema_principal = data['tema_principal']
        if 'asistentes' in data:
            acta.asistentes = json.dumps(data['asistentes'], ensure_ascii=False)
        if 'acuerdos' in data:
            acta.acuerdos = data['acuerdos']
        if 'compromisos' in data:
            acta.compromisos = json.dumps(data['compromisos'], ensure_ascii=False)
        if 'resumen' in data:
            acta.resumen = data['resumen']
        if 'observaciones' in data:
            acta.observaciones = data['observaciones']

        acta.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'ok': True, 'acta': acta.to_dict()})
    except Exception as e:
        logger.error(f"actualizar_acta: {e}", exc_info=True)
        _db().session.rollback()
        return jsonify({'error': str(e)}), 500


@riesgo_actas_api.route('/cmgr/<int:acta_id>', methods=['DELETE'])
def eliminar_acta(acta_id):
    try:
        db = _db()
        ActaCMGR, _, _ = _models()
        acta = ActaCMGR.query.get_or_404(acta_id)
        db.session.delete(acta)
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        _db().session.rollback()
        return jsonify({'error': str(e)}), 500


@riesgo_actas_api.route('/cmgr/<int:acta_id>/pdf', methods=['POST'])
def adjuntar_pdf_acta(acta_id):
    """POST /api/actas/cmgr/<id>/pdf  — adjunta archivo PDF/DOCX"""
    try:
        db = _db()
        ActaCMGR, _, _ = _models()
        acta = ActaCMGR.query.get_or_404(acta_id)

        if 'file' not in request.files:
            return jsonify({'error': 'No file'}), 400

        archivo = request.files['file']
        uploads = current_app.config.get('UPLOADS_DIR', 'uploads')
        destino = os.path.join(str(uploads), 'actas_cmgr')
        os.makedirs(destino, exist_ok=True)

        nombre = f"acta_{acta_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{archivo.filename}"
        ruta = os.path.join(destino, nombre)
        archivo.save(ruta)

        acta.archivo_pdf = f"actas_cmgr/{nombre}"
        db.session.commit()
        return jsonify({'ok': True, 'archivo_pdf': acta.archivo_pdf})
    except Exception as e:
        _db().session.rollback()
        return jsonify({'error': str(e)}), 500


# ── Alerta mensual ───────────────────────────────────────────────────────────

@riesgo_actas_api.route('/cmgr/alerta-mensual', methods=['GET'])
def alerta_mensual():
    """
    GET /api/actas/cmgr/alerta-mensual
    Retorna si el mes actual NO tiene acta y si el usuario es de Planeación.
    Solo relevante para usuarios (planeacion) o admin.
    """
    try:
        ActaCMGR, _, _ = _models()
        usuario = _usuario()
        rol     = session.get('role', '')
        es_planeacion = '(planeacion)' in usuario.lower() or rol == 'admin'

        if not es_planeacion:
            return jsonify({'alerta': False, 'razon': 'no-planeacion'})

        hoy     = datetime.utcnow().date()
        inicio  = hoy.replace(day=1)
        tiene_acta = ActaCMGR.query.filter(
            ActaCMGR.fecha >= inicio,
            ActaCMGR.fecha <= hoy
        ).count() > 0

        return jsonify({
            'alerta':    not tiene_acta,
            'mes':       hoy.strftime('%B %Y'),
            'tiene_acta': tiene_acta
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# DAMNIFICADOS
# ============================================================================

@riesgo_actas_api.route('/damnificados', methods=['GET'])
def listar_damnificados():
    """GET /api/actas/damnificados?page=1&estado=Pendiente&vereda=&q="""
    ok, err = _check_actas_perm()
    if not ok:
        return err
    try:
        _, Damnificado, _ = _models()
        page   = int(request.args.get('page', 1))
        limit  = int(request.args.get('limit', 20))
        estado = request.args.get('estado', '')
        vereda = request.args.get('vereda', '')
        q      = request.args.get('q', '').strip()

        query = _filtro_actas(Damnificado.query, Damnificado)

        if estado:
            query = query.filter(Damnificado.estado_ayuda == estado)
        if vereda:
            query = query.filter(Damnificado.vereda.ilike(f'%{vereda}%'))
        if q:
            query = query.filter(
                Damnificado.nombre.ilike(f'%{q}%') |
                Damnificado.documento.ilike(f'%{q}%')
            )

        total = query.count()
        items = query.order_by(Damnificado.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

        # Resumen por estado
        from sqlalchemy import func
        resumen = {
            'Pendiente':   Damnificado.query.filter_by(estado_ayuda='Pendiente').count(),
            'En proceso':  Damnificado.query.filter_by(estado_ayuda='En proceso').count(),
            'Atendido':    Damnificado.query.filter_by(estado_ayuda='Atendido').count(),
        }

        return jsonify({
            'total':   total,
            'page':    page,
            'resumen': resumen,
            'items':   [d.to_dict() for d in items]
        })
    except Exception as e:
        logger.error(f"listar_damnificados: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@riesgo_actas_api.route('/damnificados', methods=['POST'])
def crear_damnificado():
    ok, err = _check_actas_perm()
    if not ok:
        return err
    try:
        db = _db()
        _, Damnificado, _ = _models()
        data = request.get_json(force=True) or {}

        d = Damnificado()
        d.nombre          = data.get('nombre', '').strip()
        d.documento       = data.get('documento', '')
        d.contacto        = data.get('contacto', '')
        d.vereda          = data.get('vereda', '')
        d.tipo_afectacion = data.get('tipo_afectacion', '')
        d.descripcion     = data.get('descripcion', '')
        d.evidencia       = json.dumps(data.get('evidencia', []), ensure_ascii=False)
        d.estado_ayuda    = data.get('estado_ayuda', 'Pendiente')
        d.observaciones   = data.get('observaciones', '')
        d.usuario_creador = _usuario()

        if not d.nombre:
            return jsonify({'error': 'nombre requerido'}), 400

        db.session.add(d)
        db.session.commit()
        return jsonify({'ok': True, 'damnificado': d.to_dict()}), 201
    except Exception as e:
        _db().session.rollback()
        return jsonify({'error': str(e)}), 500


@riesgo_actas_api.route('/damnificados/<int:dam_id>', methods=['GET'])
def obtener_damnificado(dam_id):
    _, Damnificado, _ = _models()
    d = Damnificado.query.get_or_404(dam_id)
    return jsonify(d.to_dict())


@riesgo_actas_api.route('/damnificados/<int:dam_id>', methods=['PUT'])
def actualizar_damnificado(dam_id):
    try:
        db = _db()
        _, Damnificado, _ = _models()
        d    = Damnificado.query.get_or_404(dam_id)
        data = request.get_json(force=True) or {}

        for campo in ('nombre', 'documento', 'contacto', 'vereda',
                      'tipo_afectacion', 'descripcion', 'estado_ayuda', 'observaciones'):
            if campo in data:
                setattr(d, campo, data[campo])

        if 'evidencia' in data:
            d.evidencia = json.dumps(data['evidencia'], ensure_ascii=False)

        d.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'ok': True, 'damnificado': d.to_dict()})
    except Exception as e:
        _db().session.rollback()
        return jsonify({'error': str(e)}), 500


@riesgo_actas_api.route('/damnificados/<int:dam_id>', methods=['DELETE'])
def eliminar_damnificado(dam_id):
    try:
        db = _db()
        _, Damnificado, _ = _models()
        d = Damnificado.query.get_or_404(dam_id)
        db.session.delete(d)
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        _db().session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# REGISTRO DE DAÑOS
# ============================================================================

@riesgo_actas_api.route('/danos', methods=['GET'])
def listar_danos():
    """GET /api/actas/danos?tipo=&criticidad=&estado=&vereda=&mapa=1"""
    try:
        _, _, RegistroDano = _models()
        tipo       = request.args.get('tipo', '')
        criticidad = request.args.get('criticidad', '')
        estado     = request.args.get('estado', '')
        vereda     = request.args.get('vereda', '')
        mapa       = request.args.get('mapa', '0') == '1'   # solo registros con coordenadas
        page       = int(request.args.get('page', 1))
        limit      = int(request.args.get('limit', 50))

        query = _filtro_actas(RegistroDano.query, RegistroDano)

        if tipo:
            query = query.filter(RegistroDano.tipo == tipo)
        if criticidad:
            query = query.filter(RegistroDano.criticidad == criticidad)
        if estado:
            query = query.filter(RegistroDano.estado == estado)
        if vereda:
            query = query.filter(RegistroDano.vereda.ilike(f'%{vereda}%'))
        if mapa:
            query = query.filter(RegistroDano.lat.isnot(None), RegistroDano.lng.isnot(None))

        total = query.count()
        items = (query.order_by(RegistroDano.prioridad.asc(), RegistroDano.created_at.desc())
                 .offset((page - 1) * limit).limit(limit).all())

        # Totales por criticidad para tarjetas de resumen
        resumen_criticidad = {}
        for c in ('Baja', 'Media', 'Alta', 'Crítica'):
            resumen_criticidad[c] = RegistroDano.query.filter_by(criticidad=c).count()

        return jsonify({
            'total':              total,
            'page':               page,
            'resumen_criticidad': resumen_criticidad,
            'items':              [r.to_dict() for r in items]
        })
    except Exception as e:
        logger.error(f"listar_danos: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@riesgo_actas_api.route('/danos', methods=['POST'])
def crear_dano():
    ok, err = _check_actas_perm()
    if not ok:
        return err
    try:
        db = _db()
        _, _, RegistroDano = _models()
        data = request.get_json(force=True) or {}

        r = RegistroDano()
        r.tipo            = data.get('tipo', 'Otro')
        r.descripcion     = data.get('descripcion', '')
        r.vereda          = data.get('vereda', '')
        r.direccion       = data.get('direccion', '')
        r.lat             = data.get('lat')
        r.lng             = data.get('lng')
        r.criticidad      = data.get('criticidad', 'Media')
        r.costo_estimado  = data.get('costo_estimado')
        r.prioridad       = int(data.get('prioridad', 3))
        r.estado          = data.get('estado', 'Reportado')
        r.evidencia       = json.dumps(data.get('evidencia', []), ensure_ascii=False)
        r.usuario_creador = _usuario()

        db.session.add(r)
        db.session.commit()
        return jsonify({'ok': True, 'dano': r.to_dict()}), 201
    except Exception as e:
        _db().session.rollback()
        return jsonify({'error': str(e)}), 500


@riesgo_actas_api.route('/danos/<int:dano_id>', methods=['GET'])
def obtener_dano(dano_id):
    _, _, RegistroDano = _models()
    r = RegistroDano.query.get_or_404(dano_id)
    return jsonify(r.to_dict())


@riesgo_actas_api.route('/danos/<int:dano_id>', methods=['PUT'])
def actualizar_dano(dano_id):
    try:
        db = _db()
        _, _, RegistroDano = _models()
        r    = RegistroDano.query.get_or_404(dano_id)
        data = request.get_json(force=True) or {}

        for campo in ('tipo', 'descripcion', 'vereda', 'direccion',
                      'criticidad', 'costo_estimado', 'prioridad', 'estado'):
            if campo in data:
                setattr(r, campo, data[campo])

        if 'lat' in data:
            r.lat = data['lat']
        if 'lng' in data:
            r.lng = data['lng']
        if 'evidencia' in data:
            r.evidencia = json.dumps(data['evidencia'], ensure_ascii=False)

        r.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'ok': True, 'dano': r.to_dict()})
    except Exception as e:
        _db().session.rollback()
        return jsonify({'error': str(e)}), 500


@riesgo_actas_api.route('/danos/<int:dano_id>', methods=['DELETE'])
def eliminar_dano(dano_id):
    try:
        db = _db()
        _, _, RegistroDano = _models()
        r = RegistroDano.query.get_or_404(dano_id)
        db.session.delete(r)
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        _db().session.rollback()
        return jsonify({'error': str(e)}), 500


@riesgo_actas_api.route('/danos/mapa', methods=['GET'])
def danos_mapa():
    """
    GET /api/actas/danos/mapa — GeoJSON para el mapa de riesgos.
    Solo registros con coordenadas.
    """
    try:
        _, _, RegistroDano = _models()
        registros = RegistroDano.query.filter(
            RegistroDano.lat.isnot(None),
            RegistroDano.lng.isnot(None)
        ).all()

        color_map = {
            'Crítica': '#dc2626',
            'Alta':    '#ea580c',
            'Media':   '#ca8a04',
            'Baja':    '#16a34a',
        }

        features = []
        for r in registros:
            features.append({
                'type': 'Feature',
                'geometry': {'type': 'Point', 'coordinates': [r.lng, r.lat]},
                'properties': {
                    'id':          r.id,
                    'tipo':        r.tipo,
                    'criticidad':  r.criticidad,
                    'estado':      r.estado,
                    'vereda':      r.vereda,
                    'descripcion': (r.descripcion or '')[:120],
                    'color':       color_map.get(r.criticidad, '#6b7280'),
                }
            })

        return jsonify({'type': 'FeatureCollection', 'features': features})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# STATS GENERALES (actas + damnificados + daños)
# ============================================================================

@riesgo_actas_api.route('/stats', methods=['GET'])
def stats_actas():
    """GET /api/actas/stats — métricas para el dashboard de Actas CMGR"""
    try:
        ActaCMGR, Damnificado, RegistroDano = _models()

        hoy    = datetime.utcnow().date()
        inicio = hoy.replace(day=1)

        return jsonify({
            'actas_total':        ActaCMGR.query.count(),
            'actas_mes':          ActaCMGR.query.filter(ActaCMGR.fecha >= inicio).count(),
            'damnificados_total': Damnificado.query.count(),
            'damnificados_pendientes': Damnificado.query.filter_by(estado_ayuda='Pendiente').count(),
            'damnificados_en_proceso': Damnificado.query.filter_by(estado_ayuda='En proceso').count(),
            'damnificados_atendidos':  Damnificado.query.filter_by(estado_ayuda='Atendido').count(),
            'danos_total':        RegistroDano.query.count(),
            'danos_criticos':     RegistroDano.query.filter_by(criticidad='Crítica').count(),
            'danos_altos':        RegistroDano.query.filter_by(criticidad='Alta').count(),
            'danos_sin_resolver': RegistroDano.query.filter(
                RegistroDano.estado.notin_(['Resuelto'])
            ).count(),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
