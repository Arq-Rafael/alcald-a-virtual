"""
API Endpoints para Gestión Arbórea - Gestión del Riesgo
IMPORTACIONES LAZY PARA EVITAR CIRCULAR IMPORTS
"""
from flask import Blueprint, request, jsonify, send_file, render_template, current_app, session
from app.utils import is_admin, current_session_user
from datetime import datetime, timedelta
import json
import os
import math
import io
import logging
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PyPDF2 import PdfReader, PdfWriter

logger = logging.getLogger(__name__)

# ✅ LAZY IMPORTS - Se cargan cuando se necesitan dentro de las funciones
def get_db():
    """Retorna la instancia de base de datos"""
    from app import db
    return db

def get_models():
    """Retorna los modelos"""
    from app.models.riesgo_arborea import RadicadoArborea, ArbolEspecie
    return RadicadoArborea, ArbolEspecie

riesgo_api = Blueprint('riesgo_api', __name__, url_prefix='/api/riesgo')


# ── Helpers de seguridad ──────────────────────────────────────────────────────

def _es_planeacion() -> bool:
    usuario = session.get('user', '')
    return usuario.endswith('.planeacion')


def _filtro_por_usuario(query, Model):
    """
    Aplica filtro de visibilidad sobre una query de RadicadoArborea.
    - Admin: ve todo.
    - Planeación (.planeacion): ve TODOS los radicados.
    - Regular: solo sus propios.
    """
    usuario = session.get('user', '')
    rol     = session.get('role', '')
    if rol == 'admin':
        return query
    if _es_planeacion():
        return query   # planeación ve todo
    return query.filter(Model.usuario_creador == usuario)


def _check_submodule(submodule: str):
    """Retorna (True, None) si el usuario puede acceder al submódulo,
    o (False, Response 403) si no puede."""
    from app.utils import can_risk_submodule
    if not can_risk_submodule(submodule):
        return False, (jsonify({
            'error': 'Acceso denegado',
            'mensaje': f'No tienes permisos para el submódulo: {submodule}'
        }), 403)
    return True, None

# ============================================================================
# ESPECIES - Autocomplete y catálogo
# ============================================================================

@riesgo_api.route('/especies/search', methods=['GET'])
def buscar_especies():
    """
    Busca especies por nombre común. 
    GET /api/riesgo/especies/search?q=roble
    """
    try:
        _, ArbolEspecie = get_models()
        q = request.args.get('q', '').strip().lower()
        
        if not q or len(q) < 2:
            return jsonify([])
        
        # Buscar especies que coincidan con el nombre común
        especies = ArbolEspecie.query.filter(
            ArbolEspecie.nombre_comun.ilike(f'%{q}%')
        ).limit(10).all()
        
        resultado = [{
            'id': e.id,
            'nombre_comun': e.nombre_comun,
            'nombre_cientifico': e.nombre_cientifico,
            'forma_copa': e.forma_copa,
            'edad_promedio_anos': e.edad_promedio_anos,
            'dap_promedio_cm': e.dap_promedio_cm,
            'coeficiente_compensacion': e.coeficiente_compensacion,
            'es_nativa': e.es_nativa,
            'categoria': e.categoria
        } for e in especies]
        
        return jsonify(resultado)
    except Exception as e:
        logger.error(f"Error buscar_especies: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@riesgo_api.route('/especies/<int:especie_id>', methods=['GET'])
def obtener_especie(especie_id):
    """Obtiene datos completos de una especie por ID"""
    try:
        _, ArbolEspecie = get_models()
        especie = ArbolEspecie.query.get_or_404(especie_id)
        return jsonify(especie.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@riesgo_api.route('/especies', methods=['GET'])
def listar_especies():
    """Lista todas las especies (con paginación opcional)"""
    try:
        _, ArbolEspecie = get_models()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Flask-SQLAlchemy 3+: usar db.paginate
        db = get_db()
        pagination = db.paginate(ArbolEspecie.query, page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'especies': [e.to_dict() for e in pagination.items]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# RADICADOS - CRUD y cálculos
# ============================================================================

@riesgo_api.route('/arborea', methods=['POST'])
def crear_radicado():
    """
    Crea un nuevo radicado de intervención arbórea.
    Persiste en base de datos, calcula compensación, genera número.
    POST /api/riesgo/arborea
    """
    ok, err = _check_submodule('arborea')
    if not ok:
        return err
    data = request.get_json()
    db = get_db()
    RadicadoArborea, _ = get_models()
    
    try:
        # Crear radicado
        radicado = RadicadoArborea()
        
        # Generar número
        radicado.generar_numero_radicado()
        
        # Llenar datos solicitante
        radicado.solicitante_nombre = data.get('solicitante_nombre')
        radicado.solicitante_documento = data.get('solicitante_documento')
        radicado.solicitante_contacto = data.get('solicitante_contacto')
        radicado.solicitante_correo = data.get('solicitante_correo')
        radicado.solicitante_rol = data.get('solicitante_rol', 'Propietario')
        
        # Ubicación
        radicado.ubicacion_vereda_sector = data.get('ubicacion_vereda_sector')
        radicado.ubicacion_direccion = data.get('ubicacion_direccion')
        radicado.ubicacion_lat = float(data.get('ubicacion_lat')) if data.get('ubicacion_lat') else None
        radicado.ubicacion_lng = float(data.get('ubicacion_lng')) if data.get('ubicacion_lng') else None
        radicado.matricula_catastral = data.get('matricula_catastral')
        
        # Árbol - datos iniciales
        radicado.arbol_especie_comun = data.get('arbol_especie_comun')
        radicado.arbol_especie_cientifico = data.get('arbol_especie_cientifico')
        radicado.arbol_dap_cm = float(data.get('arbol_dap_cm')) if data.get('arbol_dap_cm') else None
        radicado.arbol_altura_m = float(data.get('arbol_altura_m')) if data.get('arbol_altura_m') else None
        radicado.arbol_copa_m = float(data.get('arbol_copa_m')) if data.get('arbol_copa_m') else None
        radicado.arbol_fitosanitario = data.get('arbol_fitosanitario')
        radicado.arbol_inclinacion_raices = data.get('arbol_inclinacion_raices')
        radicado.arbol_afectacion = data.get('arbol_afectacion')
        radicado.arbol_riesgo_inicial = data.get('arbol_riesgo_inicial')
        
        # Solicitud
        radicado.tipo_solicitud = data.get('tipo_solicitud', 'Poda')
        radicado.motivo_solicitud = data.get('motivo_solicitud')
        radicado.usuario_creador = session.get('user', 'Sistema')

        # Auto-calcular criticidad y SLA
        radicado.calcular_criticidad()
        radicado.calcular_vencimiento_sla()

        # Registrar estado inicial en historial
        radicado.historial_estados = json.dumps([{
            'estado': 'Radicada',
            'fecha': datetime.utcnow().isoformat(),
            'usuario': radicado.usuario_creador,
            'observacion': 'Radicado creado'
        }])
        
        # Visita técnica (si viene en el mismo request)
        if data.get('visita_fecha'):
            radicado.visita_fecha = datetime.fromisoformat(data.get('visita_fecha'))
        radicado.visita_tecnico = data.get('visita_tecnico')
        radicado.visita_riesgo_final = data.get('visita_riesgo_final')
        radicado.visita_observaciones = data.get('visita_observaciones')
        
        # Dictamen y permiso
        radicado.dictamen_decision = data.get('dictamen_decision')
        radicado.permiso_vigencia_dias = int(data.get('permiso_vigencia_dias', 15)) if data.get('permiso_vigencia_dias') else 15
        radicado.permiso_fecha_emision = datetime.utcnow()
        radicado.permiso_obligaciones = data.get('permiso_obligaciones')
        radicado.permiso_firmante1 = data.get('permiso_firmante1')
        radicado.permiso_firmante2 = data.get('permiso_firmante2')
        
        # Calcular fecha límite automáticamente
        radicado.calcular_fecha_limite()
        
        # Compensación
        radicado.compensacion_metodo = data.get('compensacion_metodo', 'Automático')
        radicado.compensacion_coeficiente = float(data.get('compensacion_coeficiente', 1.0)) if data.get('compensacion_coeficiente') else 1.0
        radicado.compensacion_especie_recomendada = data.get('compensacion_especie_recomendada')
        radicado.compensacion_sitio = data.get('compensacion_sitio')
        radicado.compensacion_plazo = data.get('compensacion_plazo')
        
        # Calcular compensación automáticamente
        if radicado.compensacion_metodo == 'Automático':
            radicado.calcular_compensacion_automatica()
        
        # Determinar estado
        if radicado.dictamen_decision:
            radicado.estado = 'Aprobada' if radicado.dictamen_decision == 'Aprobado' else 'Negada'
        else:
            radicado.estado = 'Radicada'
        
        # Guardar en base de datos
        db.session.add(radicado)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'id': radicado.id,
            'numero_radicado': radicado.numero_radicado,
            'estado': radicado.estado,
            # Solicitante
            'solicitante_nombre': radicado.solicitante_nombre,
            'solicitante_documento': radicado.solicitante_documento,
            'solicitante_contacto': radicado.solicitante_contacto,
            'solicitante_correo': radicado.solicitante_correo,
            'solicitante_rol': radicado.solicitante_rol,
            # Ubicación
            'ubicacion_direccion': radicado.ubicacion_direccion,
            'ubicacion_vereda_sector': radicado.ubicacion_vereda_sector,
            'ubicacion_lat': radicado.ubicacion_lat,
            'ubicacion_lng': radicado.ubicacion_lng,
            'matricula_catastral': radicado.matricula_catastral,
            # Árbol
            'arbol_especie_comun': radicado.arbol_especie_comun,
            'arbol_especie_cientifico': radicado.arbol_especie_cientifico,
            'arbol_dap_cm': radicado.arbol_dap_cm,
            'arbol_altura_m': radicado.arbol_altura_m,
            'arbol_copa_m': radicado.arbol_copa_m,
            'arbol_fitosanitario': radicado.arbol_fitosanitario,
            'arbol_inclinacion_raices': radicado.arbol_inclinacion_raices,
            'arbol_riesgo_inicial': radicado.arbol_riesgo_inicial,
            # Solicitud
            'tipo_solicitud': radicado.tipo_solicitud,
            'motivo_solicitud': radicado.motivo_solicitud,
            # Compensación y permiso
            'compensacion_metodo': radicado.compensacion_metodo,
            'compensacion_coeficiente': radicado.compensacion_coeficiente,
            'compensacion_arboles_plantar': radicado.compensacion_arboles_plantar,
            'permiso_fecha_limite': radicado.permiso_fecha_limite.isoformat() if radicado.permiso_fecha_limite else None,
            'created_at': radicado.created_at.isoformat(),
            'mensaje': f'Radicado {radicado.numero_radicado} creado exitosamente'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error crear_radicado: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'mensaje': 'Error al crear radicado'
        }), 400


@riesgo_api.route('/arborea/<int:radicado_id>', methods=['GET'])
def obtener_radicado(radicado_id):
    """Obtiene un radicado completo por ID"""
    ok, err = _check_submodule('arborea')
    if not ok:
        return err
    try:
        logger.info(f"[GET] Obteniendo radicado ID: {radicado_id}")
        RadicadoArborea, _ = get_models()
        radicado = RadicadoArborea.query.get_or_404(radicado_id)

        # Verificar propiedad: solo el dueño, admin o planeación pueden leerlo
        usuario = session.get('user', '')
        rol     = session.get('role', '')
        es_dueno = radicado.usuario_creador == usuario
        es_planeacion_y_pendiente = _es_planeacion() and radicado.estado == 'En revisión Planeación'
        if rol != 'admin' and not es_dueno and not es_planeacion_y_pendiente:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        
        logger.info(f"[GET] Radicado encontrado: {radicado.numero_radicado}")
        
        # Parsear JSON fields
        archivos_radicacion = json.loads(radicado.archivos_radicacion) if radicado.archivos_radicacion else []
        archivos_visita = json.loads(radicado.archivos_visita) if radicado.archivos_visita else []
        archivos_compensacion = json.loads(radicado.archivos_compensacion) if radicado.archivos_compensacion else []
        calculo = json.loads(radicado.compensacion_calculo_json) if radicado.compensacion_calculo_json else {}
        
        response = {
            'success': True,
            'radicado': {
                'id': radicado.id,
                'numero_radicado': radicado.numero_radicado,
                'solicitante_nombre': radicado.solicitante_nombre,
                'solicitante_documento': radicado.solicitante_documento,
                'solicitante_contacto': radicado.solicitante_contacto,
                'solicitante_correo': radicado.solicitante_correo,
                'ubicacion_direccion': radicado.ubicacion_direccion,
                'ubicacion_vereda_sector': radicado.ubicacion_vereda_sector,
                'ubicacion_lat': radicado.ubicacion_lat,
                'ubicacion_lng': radicado.ubicacion_lng,
                'matricula_catastral': radicado.matricula_catastral,
                'arbol_especie_comun': radicado.arbol_especie_comun,
                'arbol_especie_cientifico': radicado.arbol_especie_cientifico,
                'arbol_dap_cm': radicado.arbol_dap_cm,
                'arbol_altura_m': radicado.arbol_altura_m,
                'arbol_copa_m': radicado.arbol_copa_m,
                'arbol_fitosanitario': radicado.arbol_fitosanitario,
                'arbol_inclinacion_raices': radicado.arbol_inclinacion_raices,
                'tipo_solicitud': radicado.tipo_solicitud,
                'motivo_solicitud': radicado.motivo_solicitud,
                'estado': radicado.estado,
                'visita_fecha': radicado.visita_fecha.isoformat() if radicado.visita_fecha else None,
                'visita_tecnico': radicado.visita_tecnico,
                'visita_riesgo_final': radicado.visita_riesgo_final,
                'visita_observaciones': radicado.visita_observaciones,
                'diagnostico_recomendaciones': radicado.diagnostico_recomendaciones,
                'dictamen_decision': radicado.dictamen_decision,
                'dictamen_motivo_negacion': radicado.dictamen_motivo_negacion,
                'compensacion_arboles_plantar': radicado.compensacion_arboles_plantar,
                'compensacion_coeficiente': radicado.compensacion_coeficiente,
                'compensacion_calculo': calculo,
                'permiso_fecha_limite': radicado.permiso_fecha_limite.isoformat() if radicado.permiso_fecha_limite else None,
                'permiso_obligaciones': radicado.permiso_obligaciones,
                'permiso_firmante1': radicado.permiso_firmante1,
                'created_at': radicado.created_at.isoformat()
            }
        }
        
        logger.info(f"[GET] Retornando radicado exitosamente")
        return jsonify(response)
    except Exception as e:
        logger.error(f"[GET] Error obteniendo radicado {radicado_id}: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@riesgo_api.route('/arborea', methods=['GET'])
def listar_radicados():
    """
    Lista radicados con filtros opcionales.
    GET /api/riesgo/arborea?estado=Aprobada&page=1
    """
    try:
        RadicadoArborea, _ = get_models()
        estado = request.args.get('estado')
        tipo_solicitud = request.args.get('tipo_solicitud')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = RadicadoArborea.query

        # Control de acceso: admin ve todo; usuarios normales solo sus radicados
        if not is_admin():
            query = query.filter_by(usuario_creador=current_session_user())

        if estado:
            query = query.filter_by(estado=estado)
        if tipo_solicitud:
            query = query.filter_by(tipo_solicitud=tipo_solicitud)
        
        # Ordenar por fecha descending
        query = query.order_by(RadicadoArborea.created_at.desc())
        
        # Flask-SQLAlchemy 3+: usar db.paginate
        db = get_db()
        pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'radicados': [r.to_dict() for r in pagination.items]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@riesgo_api.route('/arborea/<int:radicado_id>/estado', methods=['PATCH'])
def cambiar_estado(radicado_id):
    """
    Cambia el estado de un radicado con validación de rol y registro en historial.
    PATCH /api/riesgo/arborea/<id>/estado
    Body: {"estado": "Visitada", "observacion": "..."}
    """
    RadicadoArborea, _ = get_models()
    db = get_db()
    radicado = RadicadoArborea.query.get_or_404(radicado_id)
    data = request.get_json() or {}
    nuevo_estado = data.get('estado', '').strip()
    observacion  = data.get('observacion', '').strip()
    usuario      = session.get('user', 'Sistema')
    rol          = session.get('role', '')

    if not nuevo_estado:
        return jsonify({'error': 'Se requiere el campo estado'}), 400

    # ─ Transiciones permitidas por rol ───────────────────────────────────
    es_planeacion = _es_planeacion()
    es_admin      = (rol == 'admin')

    # Solo .planeacion puede aprobar/rechazar
    SOLO_PLANEACION = {'Aprobada', 'Rechazada'}
    if nuevo_estado in SOLO_PLANEACION and not es_planeacion and not es_admin:
        return jsonify({'error': 'Solo un usuario de Planeación puede aprobar o rechazar radicados'}), 403

    # Validaciones antes de aprobar
    if nuevo_estado == 'Aprobada':
        faltantes = []
        if not radicado.arbol_especie_comun: faltantes.append('Especie del árbol')
        if not radicado.arbol_dap_cm:        faltantes.append('DAP')
        if not radicado.ubicacion_direccion: faltantes.append('Ubicación')
        if not radicado.dictamen_decision:   faltantes.append('Decisión CMGR')
        if not radicado.permiso_vigencia_dias: faltantes.append('Vigencia del permiso')
        if not radicado.permiso_obligaciones: faltantes.append('Obligaciones especiales')
        if not radicado.compensacion_arboles_plantar: faltantes.append('Compensación (número de árboles)')
        if faltantes:
            return jsonify({
                'error': 'Campos requeridos incompletos',
                'faltantes': faltantes
            }), 422

    try:
        radicado.registrar_cambio_estado(nuevo_estado, usuario, observacion)
        # Si se aprueba, actualizar campos de planeación
        if nuevo_estado in ('Aprobada', 'Rechazada'):
            radicado.planeacion_decision      = nuevo_estado
            radicado.planeacion_usuario       = usuario
            radicado.planeacion_fecha         = datetime.utcnow()
            radicado.planeacion_observaciones = observacion
        db.session.commit()
        return jsonify({
            'success': True,
            'estado': nuevo_estado,
            'radicado': radicado.to_dict()
        })
    except Exception as ex:
        db.session.rollback()
        logger.error(f'Error cambiar_estado {radicado_id}: {ex}', exc_info=True)
        return jsonify({'error': str(ex)}), 500

# ============================================================================

def _render_pdf(template_name, context, filename="documento.pdf"):
    """Renderiza un PDF usando el formato oficial FORMATO.pdf como base."""
    try:
        RadicadoArborea, _ = get_models()
        radicado = context['radicado']
        
        # Ruta del formato oficial
        formato_path = os.path.join(current_app.config['DATA_DIR'], 'FORMATO.pdf')
        
        # Crear canvas para el overlay
        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=letter)
        w, h = letter
        margin = 85
        y_position = h - 140  # Comenzar más arriba para mejor uso del espacio
        
        # Estilos
        styles = getSampleStyleSheet()
        style_title = ParagraphStyle(
            'title_arial',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#0f4c81'),
            alignment=0,
            spaceAfter=6
        )
        style_body = ParagraphStyle(
            'body_arial',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=13,
            textColor=colors.HexColor('#3d3d3d'),
            alignment=0,
            spaceAfter=4
        )
        
        # Título del documento
        c.setFont('Helvetica-Bold', 15)
        c.setFillColor(colors.HexColor('#0f4c81'))
        c.drawString(margin, y_position, context.get('titulo', 'Documento'))
        y_position -= 18

        # Metadatos
        c.setFont('Helvetica', 9)
        c.setFillColor(colors.HexColor('#6b7280'))
        meta_text = f"Radicado: {radicado.numero_radicado}   "
        if template_name == 'pdf_informe_arborea.html':
            meta_text += f"Fecha informe: {(radicado.visita_fecha or radicado.updated_at or radicado.created_at).strftime('%Y-%m-%d')}"
        else:
            meta_text += f"Fecha emisión: {(radicado.permiso_fecha_emision or radicado.updated_at or radicado.created_at).strftime('%Y-%m-%d')}"
        c.drawString(margin, y_position, meta_text)
        y_position -= 4
        
        # Línea de acento azul institucional
        c.setStrokeColor(colors.HexColor('#1565c0'))
        c.setLineWidth(2)
        c.line(margin, y_position, margin + (w - 2*margin), y_position)
        c.setLineWidth(1)
        y_position -= 16
        
        # Contenido según template
        if template_name == 'pdf_informe_arborea.html':
            y_position = _render_informe_content(c, radicado, margin, y_position, w, h, style_title, style_body)
        else:
            y_position = _render_dictamen_content(c, radicado, margin, y_position, w, h, style_title, style_body)

        # ── Marca de agua BORRADOR (diagonal) ──────────────────────────────
        if context.get('es_borrador'):
            import math as _math
            c.saveState()
            c.setFillColorRGB(0.85, 0.15, 0.15, alpha=0.13)   # rojo muy tenue
            c.setFont('Helvetica-Bold', 72)
            c.translate(w / 2, h / 2)
            c.rotate(45)
            c.drawCentredString(0, 0, 'BORRADOR')
            c.rotate(-45)
            c.translate(-w / 2, -h / 2)
            c.restoreState()

        c.save()
        overlay_buffer.seek(0)
        
        # Combinar con formato oficial
        if os.path.exists(formato_path):
            template_pdf = PdfReader(formato_path)
            overlay_pdf = PdfReader(overlay_buffer)
            output = PdfWriter()
            
            for page_num in range(len(overlay_pdf.pages)):
                template_page = PdfReader(formato_path).pages[0]
                overlay_page = overlay_pdf.pages[page_num]
                template_page.merge_page(overlay_page)
                output.add_page(template_page)
            
            final_buffer = io.BytesIO()
            output.write(final_buffer)
            final_buffer.seek(0)
            return send_file(final_buffer, mimetype='application/pdf', as_attachment=True, download_name=filename)
        else:
            overlay_buffer.seek(0)
            return send_file(overlay_buffer, mimetype='application/pdf', as_attachment=True, download_name=filename)
    except Exception as e:
        logger.error(f"Error renderizando PDF {template_name}: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def _render_informe_content(c, radicado, margin, y_position, w, h, style_title, style_body):
    """Renderiza el contenido del informe técnico."""

    table_width = w - 2*margin
    COLOR_PRIMARY = '#0f4c81'  # Azul institucional
    COLOR_HEADER_BG = '#1565c0'  # Azul medio institucional
    COLOR_GRID = '#d4d4d8'
    COLOR_TEXT = '#3d3d3d'  # Texto gris oscuro legible
    
    # Datos del Solicitante
    c.setFont('Helvetica-Bold', 10)
    c.setFillColor(colors.HexColor(COLOR_PRIMARY))
    c.drawString(margin, y_position, 'DATOS DEL SOLICITANTE')
    y_position -= 14
    
    data = [
        ['Nombre', radicado.solicitante_nombre or '-'],
        ['Documento', radicado.solicitante_documento or '-'],
        ['Contacto', radicado.solicitante_contacto or '-'],
        ['Correo', radicado.solicitante_correo or '-']
    ]
    table = Table(data, colWidths=[table_width*0.25, table_width*0.75])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(COLOR_HEADER_BG)),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (0, -1), 9),
        ('FONTSIZE', (1, 0), (1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(COLOR_GRID)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),

    ]))
    w_table, h_table = table.wrap(table_width, 150)
    
    if y_position - h_table < 140:
        c.showPage()
        y_position = h - 140
    
    table.drawOn(c, margin, y_position - h_table)
    y_position -= (h_table + 16)
    
    # Ubicación
    c.setFont('Helvetica-Bold', 11)
    c.setFillColor(colors.HexColor(COLOR_PRIMARY))
    c.drawString(margin, y_position, 'Ubicación')
    y_position -= 2
    c.setStrokeColor(colors.HexColor(COLOR_PRIMARY))
    c.line(margin, y_position, margin + table_width, y_position)
    y_position -= 14
    
    data = [
        ['Dirección', radicado.ubicacion_direccion or '-'],
        ['Vereda/Sector', radicado.ubicacion_vereda_sector or '-'],
        ['Matrícula Catastral', radicado.matricula_catastral or '-']
    ]
    table = Table(data, colWidths=[table_width*0.25, table_width*0.75])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(COLOR_HEADER_BG)),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (0, -1), 9),
        ('FONTSIZE', (1, 0), (1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(COLOR_GRID)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),

    ]))
    w_table, h_table = table.wrap(table_width, 150)
    
    if y_position - h_table < 140:
        c.showPage()
        y_position = h - 140
    
    table.drawOn(c, margin, y_position - h_table)
    y_position -= (h_table + 16)
    
    # Árbol
    c.setFont('Helvetica-Bold', 11)
    c.setFillColor(colors.HexColor(COLOR_PRIMARY))
    c.drawString(margin, y_position, 'Datos del Árbol')
    y_position -= 2
    c.setStrokeColor(colors.HexColor(COLOR_PRIMARY))
    c.line(margin, y_position, margin + table_width, y_position)
    y_position -= 14
    
    data = [
        ['Especie (común)', radicado.arbol_especie_comun or '-'],
        ['Especie (científica)', radicado.arbol_especie_cientifico or '-'],
        ['DAP (cm)', str(round(radicado.arbol_dap_cm, 1)) if radicado.arbol_dap_cm else '-'],
        ['Altura (m)', str(round(radicado.arbol_altura_m, 1)) if radicado.arbol_altura_m else '-'],
        ['Copa (m)', str(round(radicado.arbol_copa_m, 1)) if radicado.arbol_copa_m else '-'],
        ['Estado Fitosanitario', radicado.arbol_fitosanitario or '-'],
        ['Inclinación/Raíces', radicado.arbol_inclinacion_raices or '-'],
        ['Afectación', radicado.arbol_afectacion or '-'],
        ['Riesgo Inicial', radicado.arbol_riesgo_inicial or '-']
    ]
    table = Table(data, colWidths=[table_width*0.25, table_width*0.75])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(COLOR_HEADER_BG)),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (0, -1), 9),
        ('FONTSIZE', (1, 0), (1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(COLOR_GRID)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),

    ]))
    w_table, h_table = table.wrap(table_width, 300)
    
    if y_position - h_table < 140:
        c.showPage()
        y_position = h - 140
    
    table.drawOn(c, margin, y_position - h_table)
    y_position -= (h_table + 16)
    
    # Visita Técnica
    c.setFont('Helvetica-Bold', 11)
    c.setFillColor(colors.HexColor(COLOR_PRIMARY))
    c.drawString(margin, y_position, 'Visita Técnica')
    y_position -= 2
    c.setStrokeColor(colors.HexColor(COLOR_PRIMARY))
    c.line(margin, y_position, margin + table_width, y_position)
    y_position -= 14
    
    data = [
        ['Fecha', (radicado.visita_fecha or radicado.updated_at or radicado.created_at).strftime('%Y-%m-%d')],
        ['Técnico Responsable', radicado.visita_tecnico or '-'],
        ['Riesgo Final', radicado.visita_riesgo_final or '-']
    ]
    table = Table(data, colWidths=[table_width*0.25, table_width*0.75])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(COLOR_HEADER_BG)),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (0, -1), 9),
        ('FONTSIZE', (1, 0), (1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(COLOR_GRID)),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),

    ]))
    w_table, h_table = table.wrap(table_width, 150)
    
    if y_position - h_table < 140:
        c.showPage()
        y_position = h - 140
    
    table.drawOn(c, margin, y_position - h_table)
    y_position -= (h_table + 16)
    
    # Observaciones
    if radicado.visita_observaciones:
        c.setFont('Helvetica-Bold', 11)
        c.setFillColor(colors.HexColor(COLOR_PRIMARY))
        c.drawString(margin, y_position, 'Observaciones')
        y_position -= 2
        c.setStrokeColor(colors.HexColor(COLOR_PRIMARY))
        c.line(margin, y_position, margin + table_width, y_position)
        y_position -= 12
        
        from reportlab.platypus import Paragraph
        style = ParagraphStyle(
            'obs',
            parent=ParagraphStyle('Normal', fontName='Helvetica', fontSize=10, leading=12),
            textColor=colors.HexColor('#2c3e50'),
            alignment=0
        )
        obs_para = Paragraph(radicado.visita_observaciones[:500], style)
        w_obs, h_obs = obs_para.wrap(table_width, 200)
        
        if y_position - h_obs < 80:
            c.showPage()
            y_position = h - 140
        
        obs_para.drawOn(c, margin, y_position - h_obs)
        y_position -= (h_obs + 16)
    
    # Diagnóstico y Recomendaciones
    if radicado.diagnostico_recomendaciones:
        c.setFont('Helvetica-Bold', 11)
        c.setFillColor(colors.HexColor(COLOR_PRIMARY))
        c.drawString(margin, y_position, 'Diagnóstico y Recomendaciones')
        y_position -= 2
        c.setStrokeColor(colors.HexColor(COLOR_PRIMARY))
        c.line(margin, y_position, margin + table_width, y_position)
        y_position -= 12
        
        from reportlab.platypus import Paragraph
        style = ParagraphStyle(
            'diag',
            parent=ParagraphStyle('Normal', fontName='Helvetica', fontSize=10, leading=12),
            textColor=colors.HexColor('#2c3e50'),
            alignment=0
        )
        diag_para = Paragraph(radicado.diagnostico_recomendaciones[:500], style)
        w_diag, h_diag = diag_para.wrap(table_width, 200)
        
        if y_position - h_diag < 80:
            c.showPage()
            y_position = h - 140
        
        diag_para.drawOn(c, margin, y_position - h_diag)
        y_position -= (h_diag + 12)


def _render_dictamen_content(c, radicado, margin, y_position, w, h, style_title, style_body):
    """Renderiza el contenido del dictamen CMGR."""

    table_width = w - 2*margin
    COLOR_PRIMARY = '#0f4c81'  # Azul institucional
    COLOR_HEADER_BG = '#1565c0'  # Azul medio institucional
    COLOR_GRID = '#d4d4d8'
    COLOR_TEXT = '#3d3d3d'  # Texto gris oscuro legible
    
    # Datos del Solicitante
    c.setFont('Helvetica-Bold', 10)
    c.setFillColor(colors.HexColor(COLOR_PRIMARY))
    c.drawString(margin, y_position, 'DATOS DEL SOLICITANTE')
    y_position -= 14
    
    data = [
        ['Nombre', radicado.solicitante_nombre or '-'],
        ['Documento', radicado.solicitante_documento or '-'],
        ['Contacto', radicado.solicitante_contacto or '-']
    ]
    table = Table(data, colWidths=[table_width*0.25, table_width*0.75])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(COLOR_HEADER_BG)),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (0, -1), 9),
        ('FONTSIZE', (1, 0), (1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(COLOR_GRID)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),

    ]))
    w_table, h_table = table.wrap(table_width, 120)
    
    if y_position - h_table < 140:
        c.showPage()
        y_position = h - 140
    
    table.drawOn(c, margin, y_position - h_table)
    y_position -= (h_table + 16)
    
    # Árbol
    c.setFont('Helvetica-Bold', 11)
    c.setFillColor(colors.HexColor(COLOR_PRIMARY))
    c.drawString(margin, y_position, 'Datos del Árbol')
    y_position -= 2
    c.setStrokeColor(colors.HexColor(COLOR_PRIMARY))
    c.line(margin, y_position, margin + table_width, y_position)
    y_position -= 14
    
    data = [
        ['Especie', radicado.arbol_especie_comun or '-'],
        ['DAP (cm)', str(round(radicado.arbol_dap_cm, 1)) if radicado.arbol_dap_cm else '-'],
        ['Ubicación', radicado.ubicacion_direccion or '-']
    ]
    table = Table(data, colWidths=[table_width*0.25, table_width*0.75])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(COLOR_HEADER_BG)),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (0, -1), 9),
        ('FONTSIZE', (1, 0), (1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(COLOR_GRID)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),

    ]))
    w_table, h_table = table.wrap(table_width, 120)
    
    if y_position - h_table < 140:
        c.showPage()
        y_position = h - 140
    
    table.drawOn(c, margin, y_position - h_table)
    y_position -= (h_table + 16)
    
    # DECISIÓN DEL CMGR - Con barra lateral y badge moderno
    c.setFont('Helvetica-Bold', 10)
    c.setFillColor(colors.HexColor(COLOR_PRIMARY))
    c.drawString(margin, y_position, 'DECISIÓN DEL CMGR')
    y_position -= 20
    
    # Badge de decisión moderno con sombra
    if radicado.dictamen_decision == 'Aprobado':
        badge_color = colors.HexColor('#2e7f20')  # Verde institucional
        badge_text = 'APROBADO'
    elif radicado.dictamen_decision == 'Negado':
        badge_color = colors.HexColor('#c72929')  # Rojo institucional
        badge_text = 'NEGADO'
    else:
        badge_color = colors.HexColor('#7a7a7a')  # Gris neutro
        badge_text = 'PENDIENTE'
    
    # Sombra del badge
    c.setFillColor(colors.HexColor('#00000020'))
    c.roundRect(margin + 2, y_position - 26, 150, 30, 4, fill=1, stroke=0)
    # Badge principal
    c.setFillColor(badge_color)
    c.roundRect(margin, y_position - 24, 150, 30, 4, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 13)
    c.drawCentredString(margin + 75, y_position - 15, badge_text)
    
    y_position -= 46
    
    # Vigencia y Obligaciones
    c.setFont('Helvetica-Bold', 10)
    c.setFillColor(colors.HexColor(COLOR_PRIMARY))
    c.drawString(margin, y_position, 'VIGENCIA Y OBLIGACIONES')
    y_position -= 14
    
    data = [
        ['Vigencia', str(radicado.permiso_vigencia_dias) + ' días' if radicado.permiso_vigencia_dias else '-'],
        ['Fecha de emisión', (radicado.permiso_fecha_emision or radicado.updated_at or radicado.created_at).strftime('%Y-%m-%d')],
        ['Fecha límite', radicado.permiso_fecha_limite.strftime('%Y-%m-%d') if radicado.permiso_fecha_limite else '-']
    ]
    table = Table(data, colWidths=[table_width*0.25, table_width*0.75])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(COLOR_HEADER_BG)),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (0, -1), 9),
        ('FONTSIZE', (1, 0), (1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(COLOR_GRID)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),

    ]))
    w_table, h_table = table.wrap(table_width, 120)
    
    if y_position - h_table < 140:
        c.showPage()
        y_position = h - 140
    
    table.drawOn(c, margin, y_position - h_table)
    y_position -= (h_table + 16)
    
    # Obligaciones
    if radicado.permiso_obligaciones:
        c.setFont('Helvetica-Bold', 11)
        c.setFillColor(colors.HexColor(COLOR_PRIMARY))
        c.drawString(margin, y_position, 'Obligaciones Especiales')
        y_position -= 2
        c.setStrokeColor(colors.HexColor(COLOR_PRIMARY))
        c.line(margin, y_position, margin + table_width, y_position)
        y_position -= 12
        
        from reportlab.platypus import Paragraph
        style = ParagraphStyle(
            'obl',
            parent=ParagraphStyle('Normal', fontName='Helvetica', fontSize=10, leading=12),
            textColor=colors.HexColor('#2c3e50'),
            alignment=0
        )
        obl_para = Paragraph(radicado.permiso_obligaciones or '', style)
        w_obl, h_obl = obl_para.wrap(table_width, 9999)

        if y_position - h_obl < 80:
            c.showPage()
            y_position = h - 140

        obl_para.drawOn(c, margin, y_position - h_obl)
        y_position -= (h_obl + 16)
    
    # COMPENSACIÓN
    c.setFont('Helvetica-Bold', 11)
    c.setFillColor(colors.HexColor(COLOR_PRIMARY))
    c.drawString(margin, y_position, 'Compensación Requerida')
    y_position -= 2
    c.setStrokeColor(colors.HexColor(COLOR_PRIMARY))
    c.line(margin, y_position, margin + table_width, y_position)
    y_position -= 14
    
    # Sitio de plantación: usar Paragraph para permitir word-wrap
    data_comp = [
        ['Tipo de solicitud', (radicado.tipo_solicitud or '-').upper()],
        ['Especies a plantar', str(radicado.compensacion_arboles_plantar) if radicado.compensacion_arboles_plantar else '-'],
        ['Especie recomendada', (radicado.compensacion_especie_recomendada or '-').upper()],
        ['Plazo', radicado.compensacion_plazo or '30 días'],
        ['Método de cálculo', radicado.compensacion_metodo or '-'],
    ]
    # Sitio va aparte como Paragraph para no truncar
    sitio_txt = radicado.compensacion_sitio or '-'

    col_w = [table_width*0.30, table_width*0.70]
    table = Table(data_comp, colWidths=col_w)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(COLOR_HEADER_BG)),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(COLOR_GRID)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    w_table, h_table = table.wrap(table_width, 9999)
    if y_position - h_table < 100:
        c.showPage()
        y_position = h - 140
    table.drawOn(c, margin, y_position - h_table)
    y_position -= (h_table + 8)

    # Sitio de plantación (texto largo)
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(colors.HexColor(COLOR_HEADER_BG))
    c.rect(margin, y_position - 18, table_width*0.30, 18, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.drawString(margin + 8, y_position - 13, 'Sitio de plantación')
    # Celda de valor
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor(COLOR_GRID))
    c.rect(margin + table_width*0.30, y_position - 18, table_width*0.70, 18, fill=1, stroke=1)
    style_sitio = ParagraphStyle('sitio', fontName='Helvetica', fontSize=9,
                                  textColor=colors.HexColor('#2c3e50'), leading=11)
    para_sitio = Paragraph(sitio_txt, style_sitio)
    w_s, h_s = para_sitio.wrap(table_width*0.70 - 16, 9999)
    # Si cabe en 18pt ponemos inline, si no extendemos
    if h_s <= 18:
        para_sitio.drawOn(c, margin + table_width*0.30 + 8, y_position - 15)
        y_position -= (18 + 12)
    else:
        c.rect(margin + table_width*0.30, y_position - h_s - 4, table_width*0.70, h_s + 8, fill=1, stroke=1)
        para_sitio.drawOn(c, margin + table_width*0.30 + 8, y_position - h_s)
        y_position -= (h_s + 16)
    
    # Pie
    if y_position < 80:
        c.showPage()
        y_position = h - 140
    
    # ── BLOQUE DE FIRMAS (siempre en nueva página) ────────────────────────
    c.showPage()
    y_position = h - 140

    c.setFont('Helvetica-Bold', 10)
    c.setFillColor(colors.HexColor(COLOR_PRIMARY))
    c.drawString(margin, y_position, 'FIRMAS DE APROBACIÓN')
    y_position -= 28

    col_w = (table_width - 40) / 2
    firma_y = y_position

    # Firma izquierda
    c.setStrokeColor(colors.HexColor('#333333'))
    c.setLineWidth(0.8)
    c.line(margin, firma_y, margin + col_w, firma_y)
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(colors.HexColor('#1a1a1a'))
    c.drawCentredString(margin + col_w / 2, firma_y - 14, 'SECRETARIO(A) DE PLANEACIÓN')
    c.drawCentredString(margin + col_w / 2, firma_y - 25, 'Y OBRAS PÚBLICAS')
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.gray)
    c.drawCentredString(margin + col_w / 2, firma_y - 36, 'Alcaldía Municipal de Supatá')

    # Firma derecha
    right_x = margin + col_w + 40
    c.setStrokeColor(colors.HexColor('#333333'))
    c.line(right_x, firma_y, right_x + col_w, firma_y)
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(colors.HexColor('#1a1a1a'))
    c.drawCentredString(right_x + col_w / 2, firma_y - 14, 'COORDINADOR(A) DEL CMGR')
    c.drawCentredString(right_x + col_w / 2, firma_y - 25, 'Comité Municipal de Gestión')
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.gray)
    c.drawCentredString(right_x + col_w / 2, firma_y - 36, 'del Riesgo — Supatá')

    y_position = firma_y - 60

    # ── LEYENDA DE INVALIDEZ ─────────────────────────────────────────────
    c.setFillColor(colors.HexColor('#fef3c7'))
    c.roundRect(margin, y_position - 22, table_width, 26, 4, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(colors.HexColor('#92400e'))
    c.drawCentredString(margin + table_width / 2, y_position - 12,
                        'Este documento no tiene validez sin las firmas originales de los funcionarios designados.')
    y_position -= 38

    c.setFont('Helvetica-Oblique', 8)
    c.setFillColor(colors.gray)
    c.drawString(margin, y_position,
                 'Generado por el Sistema de Gestión Arbórea — Alcaldía Municipal de Supatá')
    c.drawRightString(margin + table_width, y_position,
                      'NIT: 899999398-5 | Carrera 7 N° 4-14 | alcaldia@supata-cundinamarca.gov.co')

    return y_position



@riesgo_api.route('/arborea/<int:radicado_id>/pdf/informe', methods=['GET'])
def pdf_informe(radicado_id):
    """Genera y descarga el PDF del informe técnico (Fase 2)."""
    try:
        RadicadoArborea, _ = get_models()
        radicado = RadicadoArborea.query.get_or_404(radicado_id)
        context = {
            'radicado': radicado,
            'titulo': 'Informe Técnico de Visita',
        }
        filename = f"Informe_{radicado.numero_radicado}.pdf"
        return _render_pdf('pdf_informe_arborea.html', context, filename)
    except Exception as e:
        logger.error(f"Error pdf_informe: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@riesgo_api.route('/arborea/<int:radicado_id>/pdf/dictamen', methods=['GET'])
def pdf_dictamen(radicado_id):
    """
    Genera PDF del dictamen CMGR.
    - borrador=1 en query param → siempre permitido (sin bloqueo).
    - Sin borrador → solo si Planeación ya aprobó (estado='Aprobada').
    """
    try:
        RadicadoArborea, _ = get_models()
        radicado = RadicadoArborea.query.get_or_404(radicado_id)

        es_borrador = request.args.get('borrador', '0') == '1'

        if not es_borrador and radicado.estado != 'Aprobada':
            return jsonify({
                'error': 'PDF final bloqueado',
                'mensaje': 'El PDF final solo se puede generar después del Visto Bueno de Planeación. '
                           'Usa ?borrador=1 para descargar una vista previa sin validez oficial.'
            }), 403

        titulo = 'Vista Previa – Dictamen CMGR (BORRADOR)' if es_borrador else 'Permiso – Dictamen CMGR'
        context = {
            'radicado': radicado,
            'titulo': titulo,
            'es_borrador': es_borrador,
        }
        prefijo = 'BORRADOR_' if es_borrador else ''
        filename = f"{prefijo}Dictamen_{radicado.numero_radicado}.pdf"
        return _render_pdf('pdf_dictamen_arborea.html', context, filename)
    except Exception as e:
        logger.error(f"Error pdf_dictamen: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@riesgo_api.route('/arborea/<int:radicado_id>', methods=['PUT'])
def actualizar_radicado(radicado_id):
    """Actualiza un radicado existente"""
    RadicadoArborea, _ = get_models()
    db = get_db()
    radicado = RadicadoArborea.query.get_or_404(radicado_id)
    data = request.get_json()
    
    try:
        # ── Visita técnica (Fase 2) ──────────────────────────────────────
        fase2_actualizada = False
        if 'visita_fecha' in data:
            radicado.visita_fecha = datetime.fromisoformat(data['visita_fecha'])
            fase2_actualizada = True
        if 'visita_tecnico' in data:
            radicado.visita_tecnico = data['visita_tecnico']
        if 'visita_riesgo_final' in data:
            radicado.visita_riesgo_final = data['visita_riesgo_final']
        if 'visita_observaciones' in data:
            radicado.visita_observaciones = data['visita_observaciones']
        if 'diagnostico_recomendaciones' in data:
            radicado.diagnostico_recomendaciones = data['diagnostico_recomendaciones']
        if 'arbol_fitosanitario' in data:
            radicado.arbol_fitosanitario = data['arbol_fitosanitario']
        if 'arbol_inclinacion_raices' in data:
            radicado.arbol_inclinacion_raices = data['arbol_inclinacion_raices']
        if 'arbol_afectacion' in data:
            radicado.arbol_afectacion = data['arbol_afectacion']

        # Transición de estado: Radicada → Visitada al guardar Fase 2
        if fase2_actualizada and radicado.estado == 'Radicada':
            radicado.estado = 'Visitada'

        # ── Fase actual del wizard ────────────────────────────────────────
        if 'fase_actual' in data:
            radicado.fase_actual = int(data['fase_actual'])

        # ── Dictamen y permiso (Fase 3) ───────────────────────────────────
        if 'dictamen_decision' in data:
            radicado.dictamen_decision = data['dictamen_decision']
            if data['dictamen_decision'] == 'Aprobado':
                # Requiere visto bueno Planeación → estado intermedio
                radicado.estado = 'En revisión Planeación'
                radicado.fase_actual = 4
            elif data['dictamen_decision'] == 'Negado':
                radicado.estado = 'Negada'
                radicado.fase_actual = 3

        if 'permiso_vigencia_dias' in data:
            radicado.permiso_vigencia_dias = data['permiso_vigencia_dias']
            radicado.permiso_fecha_emision = datetime.utcnow()
            radicado.calcular_fecha_limite()

        if 'permiso_obligaciones' in data:
            radicado.permiso_obligaciones = data['permiso_obligaciones']
        if 'permiso_firmante1' in data:
            radicado.permiso_firmante1 = data['permiso_firmante1']

        # ── Compensación ──────────────────────────────────────────────────
        if 'compensacion_coeficiente' in data:
            radicado.compensacion_coeficiente = data['compensacion_coeficiente']
        if 'compensacion_metodo' in data:
            radicado.compensacion_metodo = data['compensacion_metodo']
        if 'compensacion_especie_recomendada' in data:
            radicado.compensacion_especie_recomendada = data['compensacion_especie_recomendada']
        if 'compensacion_sitio' in data:
            radicado.compensacion_sitio = data['compensacion_sitio']

        # Recalcular compensación automática
        if radicado.compensacion_metodo == 'Automático' and radicado.arbol_dap_cm and radicado.compensacion_coeficiente:
            radicado.calcular_compensacion_automatica()

        radicado.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'radicado': radicado.to_dict(),   # ← full payload para actualizar radicadoActual en JS
            'numero_radicado': radicado.numero_radicado,
            'estado': radicado.estado,
            'mensaje': 'Radicado actualizado exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error actualizar_radicado: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'mensaje': 'Error al actualizar radicado'
        }), 400


@riesgo_api.route('/arborea/<int:radicado_id>', methods=['DELETE'])
def eliminar_radicado(radicado_id):
    """Elimina un radicado. Solo el administrador puede eliminar."""
    RadicadoArborea, _ = get_models()
    db = get_db()

    # Verificar sesión activa
    if not session.get('user'):
        return jsonify({'success': False, 'mensaje': 'Sesión no válida'}), 401

    # Solo admin puede eliminar cualquier radicado
    if session.get('role') != 'admin':
        return jsonify({
            'success': False,
            'mensaje': 'Solo el administrador puede eliminar radicados'
        }), 403

    radicado = RadicadoArborea.query.get_or_404(radicado_id)
    
    try:
        db.session.delete(radicado)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': f'Radicado {radicado.numero_radicado} eliminado'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error eliminar_radicado: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'mensaje': 'Error al eliminar radicado'
        }), 400


# ============================================================================
# CÁLCULOS - Compensación y validaciones
# ============================================================================

@riesgo_api.route('/calcular-compensacion', methods=['POST'])
def calcular_compensacion():
    """
    Calcula número de árboles a plantar.
    POST /api/riesgo/calcular-compensacion
    {
        "dap_cm": 45,
        "coeficiente": 1.5
    }
    Retorna: {"arboles_plantar": 7, "formula": "ceil((DAP/10)*coef)"}
    """
    data = request.get_json()
    
    dap = data.get('dap_cm', 0)
    coef = data.get('coeficiente', 1.0)
    
    if dap <= 0:
        return jsonify({
            'success': False,
            'error': 'DAP debe ser mayor a 0'
        }), 400
    
    # Aplicar fórmula: ceil((DAP/10)*coeficiente)
    arboles = max(1, math.ceil((dap / 10) * coef))
    
    return jsonify({
        'success': True,
        'dap_cm': dap,
        'coeficiente': coef,
        'formula': 'ceil((DAP/10)*coef)',
        'arboles_plantar': arboles,
        'detalles': f'({dap}/10)*{coef} = {dap/10 * coef} ≈ {arboles} árboles'
    }), 200


# ============================================================================
# VALIDACIONES
# ============================================================================

@riesgo_api.route('/validar-vigencia', methods=['POST'])
def validar_vigencia():
    """
    Valida que la vigencia no exceda 15 días.
    POST /api/riesgo/validar-vigencia
    {"vigencia_dias": 20}
    """
    data = request.get_json()
    vigencia = data.get('vigencia_dias', 0)
    
    es_valida = vigencia > 0 and vigencia <= 15
    
    return jsonify({
        'valida': es_valida,
        'vigencia_dias': vigencia,
        'maximo_permitido': 15,
        'mensaje': 'Vigencia válida' if es_valida else f'Vigencia debe ser entre 1 y 15 días'
    }), 200


@riesgo_api.route('/generar-numero-radicado', methods=['POST'])
def generar_numero():
    """Genera un nuevo número de radicado único"""
    RadicadoArborea, _ = get_models()
    db = get_db()
    
    try:
        tipo = request.json.get('tipo', 'AR') if request.json else 'AR'
        
        anio = datetime.utcnow().year
        contador = db.session.query(db.func.count(RadicadoArborea.id)).scalar() + 1
        numero = f"{tipo}-{anio}-{contador:05d}"
        
        return jsonify({
            'numero_radicado': numero,
            'anio': anio,
            'consecutivo': contador
        }), 200
    except Exception as e:
        logger.error(f"Error generar_numero: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ESTADÍSTICAS REALES — para el dashboard del módulo
# ============================================================================

@riesgo_api.route('/stats', methods=['GET'])
def get_stats():
    """
    Retorna KPIs reales del módulo Gestión del Riesgo.
    GET /api/riesgo/stats?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
    """
    try:
        RadicadoArborea, _ = get_models()

        # ── Filtro de usuario (historial propio) ─────────────────────────────
        query_base = _filtro_por_usuario(RadicadoArborea.query, RadicadoArborea)

        # Filtro de fecha opcional
        desde_str = request.args.get('desde', '')
        hasta_str = request.args.get('hasta', '')

        if desde_str:
            try:
                desde_dt = datetime.strptime(desde_str, '%Y-%m-%d')
                query_base = query_base.filter(RadicadoArborea.created_at >= desde_dt)
            except ValueError:
                pass
        if hasta_str:
            try:
                hasta_dt = datetime.strptime(hasta_str, '%Y-%m-%d') + timedelta(days=1)
                query_base = query_base.filter(RadicadoArborea.created_at < hasta_dt)
            except ValueError:
                pass

        total         = query_base.count()
        radicadas     = query_base.filter(RadicadoArborea.estado == 'Radicada').count()
        visitadas     = query_base.filter(RadicadoArborea.estado == 'Visitada').count()
        en_comite     = query_base.filter(RadicadoArborea.estado == 'En revisión Comité').count()
        en_planeacion = query_base.filter(RadicadoArborea.estado == 'En revisión Planeación').count()
        aprobadas     = query_base.filter(RadicadoArborea.estado == 'Aprobada').count()
        negadas       = query_base.filter(RadicadoArborea.estado == 'Negada').count()
        cerradas      = query_base.filter(RadicadoArborea.estado == 'Cerrada').count()
        pendientes    = total - aprobadas - negadas - cerradas

        # Críticos: riesgo final alto o crítico, no resueltos
        criticos = query_base.filter(
            RadicadoArborea.visita_riesgo_final.in_(['Alto', 'Crítico', 'Critico']),
            RadicadoArborea.estado.notin_(['Aprobada', 'Negada', 'Cerrada', 'Rechazada'])
        ).count()

        # Vencidos SLA: radicados activos con más de 15 días sin cierre
        sla_limite = datetime.utcnow() - timedelta(days=15)
        vencidos_sla = query_base.filter(
            RadicadoArborea.estado.notin_(['Aprobada', 'Negada', 'Cerrada', 'Rechazada']),
            RadicadoArborea.created_at < sla_limite
        ).count()

        # Pendientes visita (estado Radicada = todavía no se ha visitado)
        pendientes_visita = radicadas

        # Pendientes comité (visitadas pero no en planeación ni cerradas)
        pendientes_comite = visitadas + en_comite

        return jsonify({
            'arborea': {
                'total':              total,
                'radicadas':          radicadas,
                'en_visita':          visitadas,
                'en_comite':          en_comite,
                'en_planeacion':      en_planeacion,
                'aprobadas':          aprobadas,
                'negadas':            negadas,
                'cerradas':           cerradas,
                'pendientes':         pendientes,
                'criticos':           criticos,
                'vencidos_sla':       vencidos_sla,
                'pendientes_visita':  pendientes_visita,
                'pendientes_comite':  pendientes_comite,
            }
        }), 200
    except Exception as e:
        logger.error(f"Error get_stats: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@riesgo_api.route('/kanban', methods=['GET'])
def get_kanban():
    """
    Retorna radicados agrupados por estado para el tablero Kanban.
    GET /api/riesgo/kanban?limite=10
    Columnas: Radicada | Visitada | En revisión Planeación | Aprobada | Negada/Cerrada
    """
    try:
        RadicadoArborea, _ = get_models()
        limite = int(request.args.get('limite', 10))

        estados_columnas = [
            ('Radicada',                ['Radicada']),
            ('Visita',                  ['Visitada']),
            ('Comité / Planeación',     ['En revisión Comité', 'En revisión Planeación']),
            ('Aprobada',                ['Aprobada']),
            ('Cerrado',                 ['Negada', 'Rechazada', 'Cerrada']),
        ]

        # ── Filtro de usuario (cada uno ve sus radicados) ──────────────────────
        base_q = _filtro_por_usuario(RadicadoArborea.query, RadicadoArborea)

        columnas = []
        for titulo, estados in estados_columnas:
            items = (base_q
                     .filter(RadicadoArborea.estado.in_(estados))
                     .order_by(RadicadoArborea.created_at.desc())
                     .limit(limite).all())
            total_col = (base_q
                         .filter(RadicadoArborea.estado.in_(estados)).count())

            columnas.append({
                'titulo':  titulo,
                'estados': estados,
                'total':   total_col,
                'items': [{
                    'id':               r.id,
                    'numero_radicado':  r.numero_radicado,
                    'solicitante':      r.solicitante_nombre,
                    'tipo_solicitud':   r.tipo_solicitud,
                    'estado':           r.estado,
                    'arbol_especie':    r.arbol_especie_comun,
                    'riesgo':           r.visita_riesgo_final or r.arbol_riesgo_inicial,
                    'vereda':           r.ubicacion_vereda_sector,
                    'dias_abierto':     (datetime.utcnow() - r.created_at).days if r.created_at else 0,
                    'created_at':       r.created_at.isoformat() if r.created_at else None,
                } for r in items]
            })

        return jsonify({'columnas': columnas}), 200
    except Exception as e:
        logger.error(f"Error get_kanban: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# PERMISOS DE SUBMÓDULOS — endpoint para el frontend
# ============================================================================

@riesgo_api.route('/mis-permisos', methods=['GET'])
def mis_permisos():
    """
    GET /api/riesgo/mis-permisos
    Retorna los permisos de submódulos del usuario en sesión.
    Usado por el frontend para mostrar/ocultar tarjetas de acceso rápido.
    """
    if not session.get('user'):
        return jsonify({'error': 'No autenticado'}), 401
    from app.utils import can_risk_submodule
    return jsonify({
        'arborea': can_risk_submodule('arborea'),
        'actas':   can_risk_submodule('actas'),
        'planes':  can_risk_submodule('planes'),
        'usuario': session.get('user', ''),
        'rol':     session.get('role', ''),
        'es_planeacion': _es_planeacion(),
    })


# ============================================================================
# SUBIDA DE FOTOS — desde celular o desktop
# ============================================================================

@riesgo_api.route('/arborea/<int:radicado_id>/foto', methods=['POST'])
def subir_foto(radicado_id):
    """
    Sube una o varias fotos al radicado.
    POST /api/riesgo/arborea/<id>/foto  (multipart/form-data, campo 'foto')
    """
    from werkzeug.utils import secure_filename
    RadicadoArborea, _ = get_models()
    db = get_db()

    if not session.get('user'):
        return jsonify({'success': False, 'mensaje': 'Sesión requerida'}), 401

    radicado = RadicadoArborea.query.get_or_404(radicado_id)

    if 'foto' not in request.files:
        return jsonify({'success': False, 'error': 'No se envió archivo'}), 400

    archivos = request.files.getlist('foto')
    rutas_guardadas = []

    upload_dir = os.path.join(str(current_app.config.get('UPLOADS_DIR', 'uploads')), 'riesgo', str(radicado_id))
    os.makedirs(upload_dir, exist_ok=True)

    for archivo in archivos:
        if archivo.filename == '':
            continue
        ext = os.path.splitext(archivo.filename)[1].lower()
        if ext not in ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic', '.heif'):
            continue
        nombre_seguro = secure_filename(archivo.filename)
        ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
        nombre_final = f"{ts}_{nombre_seguro}"
        ruta_absoluta = os.path.join(upload_dir, nombre_final)
        archivo.save(ruta_absoluta)
        ruta_relativa = f"riesgo/{radicado_id}/{nombre_final}"
        rutas_guardadas.append(ruta_relativa)

    if not rutas_guardadas:
        return jsonify({'success': False, 'error': 'Ningún archivo válido recibido'}), 400

    # Acumular a la lista existente
    fotos_actuales = json.loads(radicado.archivos_fotos) if radicado.archivos_fotos else []
    fotos_actuales.extend(rutas_guardadas)
    radicado.archivos_fotos = json.dumps(fotos_actuales)
    radicado.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'success': True,
        'archivos_subidos': rutas_guardadas,
        'total_fotos': len(fotos_actuales),
        'todas_las_fotos': fotos_actuales
    }), 201


@riesgo_api.route('/arborea/<int:radicado_id>/foto/<path:nombre_foto>', methods=['DELETE'])
def eliminar_foto(radicado_id, nombre_foto):
    """Elimina una foto del radicado."""
    RadicadoArborea, _ = get_models()
    db = get_db()

    if not session.get('user'):
        return jsonify({'success': False}), 401

    radicado = RadicadoArborea.query.get_or_404(radicado_id)
    fotos = json.loads(radicado.archivos_fotos) if radicado.archivos_fotos else []

    ruta_relativa = f"riesgo/{radicado_id}/{nombre_foto}"
    if ruta_relativa in fotos:
        fotos.remove(ruta_relativa)
        radicado.archivos_fotos = json.dumps(fotos)
        db.session.commit()
        # Intentar borrar el archivo físico
        try:
            ruta_abs = os.path.join(str(current_app.config.get('UPLOADS_DIR', 'uploads')), ruta_relativa)
            if os.path.exists(ruta_abs):
                os.remove(ruta_abs)
        except Exception:
            pass
        return jsonify({'success': True, 'total_fotos': len(fotos)}), 200

    return jsonify({'success': False, 'error': 'Foto no encontrada'}), 404


@riesgo_api.route('/uploads/riesgo/<int:radicado_id>/<path:nombre_foto>', methods=['GET'])
def servir_foto(radicado_id, nombre_foto):
    """Sirve una foto del radicado."""
    upload_dir = os.path.join(str(current_app.config.get('UPLOADS_DIR', 'uploads')), 'riesgo', str(radicado_id))
    return send_file(os.path.join(upload_dir, nombre_foto))


# ============================================================================
# APROBACIÓN PLANEACIÓN — Fase 4
# ============================================================================

@riesgo_api.route('/arborea/<int:radicado_id>/planeacion', methods=['PUT'])
def aprobar_planeacion(radicado_id):
    """
    Planeación aprueba o rechaza el dictamen del CMGR.
    Solo usuarios con '(planeacion)' en el nombre o admin.
    PUT /api/riesgo/arborea/<id>/planeacion
    {
        "decision": "Aprobada" | "Rechazada",
        "observaciones": "..."
    }
    """
    RadicadoArborea, _ = get_models()
    db = get_db()

    usuario = session.get('user', '')
    rol     = session.get('role', '')

    # Verificar permiso: solo planeación o admin
    es_planeacion = '(planeacion)' in usuario.lower() or rol == 'admin'
    if not es_planeacion:
        return jsonify({'success': False, 'mensaje': 'Solo Planeación puede realizar esta acción'}), 403

    radicado = RadicadoArborea.query.get_or_404(radicado_id)
    data = request.get_json() or {}

    decision = data.get('decision')
    if decision not in ('Aprobada', 'Rechazada'):
        return jsonify({'success': False, 'error': 'decision debe ser Aprobada o Rechazada'}), 400

    try:
        radicado.planeacion_decision      = decision
        radicado.planeacion_usuario       = usuario
        radicado.planeacion_fecha         = datetime.utcnow()
        radicado.planeacion_observaciones = data.get('observaciones', '')
        radicado.fase_actual              = 5 if decision == 'Aprobada' else 3

        if decision == 'Aprobada':
            radicado.estado = 'Aprobada'
        else:
            radicado.estado = 'En revisión Planeación'  # vuelve a revisión

        radicado.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'radicado': radicado.to_dict(),
            'mensaje': f'Radicado {radicado.numero_radicado} {decision.lower()} por Planeación'
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error aprobar_planeacion: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@riesgo_api.route('/arborea/pendientes-planeacion', methods=['GET'])
def pendientes_planeacion():
    """
    Lista los radicados pendientes de visto bueno de Planeación.
    Solo accesible por Planeación/admin.
    """
    usuario = session.get('user', '')
    rol     = session.get('role', '')
    es_planeacion = '(planeacion)' in usuario.lower() or rol == 'admin'
    if not es_planeacion:
        return jsonify({'success': False, 'mensaje': 'Acceso denegado'}), 403

    RadicadoArborea, _ = get_models()
    pendientes = RadicadoArborea.query.filter_by(estado='En revisión Planeación').order_by(
        RadicadoArborea.updated_at.desc()
    ).all()

    return jsonify({
        'total': len(pendientes),
        'radicados': [r.to_dict() for r in pendientes]
    }), 200
