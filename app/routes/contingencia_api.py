"""
API de Planes de Contingencia - CRUD y generación de PDF
Soporta 6 tipos de eventos con plantillas dinámicas
"""
from flask import Blueprint, request, jsonify, send_file, current_app
from datetime import datetime
import json
import os
import io
import logging
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PyPDF2 import PdfReader, PdfWriter
from app.utils.pdf_plans_generator import PDFPlanContingenciaOficial
from app.utils.contingencia_helpers import get_datos_supata, get_plantilla_por_tipo

logger = logging.getLogger(__name__)

# ✅ LAZY IMPORTS
def get_db():
    from app import db
    return db

def get_models():
    from app.models.plan_contingencia import PlanContingencia
    return PlanContingencia


def _get_oficial(plan):
    """Devuelve la estructura oficial almacenada en multimedia_embed.plan_oficial."""
    try:
        base = json.loads(plan.multimedia_embed) if plan.multimedia_embed else {}
    except Exception:
        base = {}
    return base.get('plan_oficial', {})


def _save_oficial(plan, payload):
    """Guarda la estructura oficial en multimedia_embed.plan_oficial."""
    try:
        base = json.loads(plan.multimedia_embed) if plan.multimedia_embed else {}
    except Exception:
        base = {}
    base['plan_oficial'] = payload
    plan.multimedia_embed = json.dumps(base)

contingencia_api = Blueprint('contingencia_api', __name__, url_prefix='/api/contingencia')

# ============================================================================
# DATOS PREDEFINIDOS POR TIPO DE EVENTO
# ============================================================================

TIPOS_EVENTOS = {
    'Lluvias': {
        'icon': 'cloud-rain',
        'color': '#2563eb',
        'umbrales': {
            'verde': '0-50 mm/24h',
            'amarillo': '51-100 mm/24h',
            'naranja': '101-150 mm/24h',
            'rojo': '> 150 mm/24h'
        },
        'sectores': ['Salud', 'Logística', 'Seguridad', 'Tránsito', 'WASH', 'Comunicaciones']
    },
    'Incendios': {
        'icon': 'fire',
        'color': '#dc2626',
        'umbrales': {
            'verde': 'Índice < 15 (Bajo)',
            'amarillo': 'Índice 15-30 (Moderado)',
            'naranja': 'Índice 30-45 (Alto)',
            'rojo': 'Índice > 45 (Crítico)'
        },
        'sectores': ['Logística', 'Seguridad', 'WASH', 'Salud', 'Comunicaciones']
    },
    'Eventos_masivos': {
        'icon': 'people-fill',
        'color': '#7c3aed',
        'umbrales': {
            'verde': '< 1000 personas',
            'amarillo': '1000-5000 personas',
            'naranja': '5000-10000 personas',
            'rojo': '> 10000 personas'
        },
        'sectores': ['Seguridad', 'Salud', 'Tránsito', 'Comunicaciones', 'Logística']
    },
    'Deslizamientos': {
        'icon': 'exclamation-triangle',
        'color': '#ea580c',
        'umbrales': {
            'verde': 'Estable',
            'amarillo': 'Riesgo bajo',
            'naranja': 'Riesgo moderado',
            'rojo': 'Riesgo alto inminente'
        },
        'sectores': ['Seguridad', 'Logística', 'Salud', 'Comunicaciones']
    },
    'Sequia': {
        'icon': 'sun-fill',
        'color': '#f59e0b',
        'umbrales': {
            'verde': 'Precipitación normal',
            'amarillo': 'Déficit 10-25%',
            'naranja': 'Déficit 25-50%',
            'rojo': 'Déficit > 50%'
        },
        'sectores': ['Salud', 'WASH', 'Logística', 'Comunicaciones']
    },
    'Derrames': {
        'icon': 'exclamation-diamond',
        'color': '#059669',
        'umbrales': {
            'verde': 'Sin incidente',
            'amarillo': 'Derrame < 50 litros',
            'naranja': 'Derrame 50-500 litros',
            'rojo': 'Derrame > 500 litros'
        },
        'sectores': ['Seguridad', 'WASH', 'Salud', 'Logística', 'Comunicaciones']
    }
}

# ============================================================================
# CRUD - Planes de Contingencia
# ============================================================================

@contingencia_api.route('/crear', methods=['POST'])
def crear_plan():
    """Crea un nuevo plan de contingencia"""
    data = request.get_json()
    db = get_db()
    PlanContingencia = get_models()
    
    try:
        plan = PlanContingencia()
        plan.generar_numero_plan()
        
        # Identificación
        plan.nombre_plan = data.get('nombre_plan')
        plan.tipo_evento = data.get('tipo_evento')
        plan.version = data.get('version', '1.0')
        
        # Cobertura
        plan.ambito = data.get('ambito')
        plan.municipio = data.get('municipio')
        plan.area_cobertura = data.get('area_cobertura')
        plan.poblacion_objetivo = data.get('poblacion_objetivo', type=int) if data.get('poblacion_objetivo') else None
        
        # Fechas y vigencia
        plan.vigencia_desde = datetime.fromisoformat(data.get('vigencia_desde')).date() if data.get('vigencia_desde') else None
        plan.vigencia_hasta = datetime.fromisoformat(data.get('vigencia_hasta')).date() if data.get('vigencia_hasta') else None
        
        # Responsables
        plan.responsable_principal = data.get('responsable_principal')
        plan.correo_responsable = data.get('correo_responsable')
        plan.telefono_responsable = data.get('telefono_responsable')
        plan.entidad_responsable = data.get('entidad_responsable', 'Alcaldía Municipal')
        
        # Aprobaciones
        plan.numero_resolucion = data.get('numero_resolucion')
        plan.fecha_resolucion = datetime.fromisoformat(data.get('fecha_resolucion')).date() if data.get('fecha_resolucion') else None
        plan.aprobado_por = data.get('aprobado_por')
        
        # Estado
        plan.estado = data.get('estado', 'Borrador')
        plan.usuario_creador = data.get('usuario_creador', 'Sistema')
        
        # Contenido (inicializar vacío o con plantilla)
        plan.descripcion_peligro = data.get('descripcion_peligro', '')
        plan.antecedentes_historicos = data.get('antecedentes_historicos', '')
        plan.supuestos_limitaciones = data.get('supuestos_limitaciones', '')
        plan.puntos_criticos = data.get('puntos_criticos', '[]')
        
        # JSON fields - inicializar con estructura base
        plan.umbrales_alertas = json.dumps(data.get('umbrales_alertas', {}))
        plan.sistema_alerta = json.dumps(data.get('sistema_alerta', {}))
        plan.estructura_organizativa = json.dumps(data.get('estructura_organizativa', {}))
        plan.fase_preparacion = json.dumps(data.get('fase_preparacion', {}))
        plan.fase_alistamiento = json.dumps(data.get('fase_alistamiento', {}))
        plan.fase_respuesta = json.dumps(data.get('fase_respuesta', {}))
        plan.fase_rehabilitacion = json.dumps(data.get('fase_rehabilitacion', {}))
        plan.inventario_recursos = json.dumps(data.get('inventario_recursos', {}))
        plan.albergues = json.dumps(data.get('albergues', []))
        plan.canales_comunicacion = json.dumps(data.get('canales_comunicacion', []))
        plan.protocolos_salud = json.dumps(data.get('protocolos_salud', {}))
        plan.presupuesto_por_fase = json.dumps(data.get('presupuesto_por_fase', {}))
        
        db.session.add(plan)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'id': plan.id,
            'numero_plan': plan.numero_plan,
            'estado': plan.estado,
            'mensaje': f'Plan {plan.numero_plan} creado exitosamente'
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error crear_plan: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'mensaje': 'Error al crear plan'
        }), 400


@contingencia_api.route('/<int:plan_id>', methods=['GET'])
def obtener_plan(plan_id):
    """Obtiene un plan completo por ID"""
    try:
        PlanContingencia = get_models()
        plan = PlanContingencia.query.get_or_404(plan_id)
        
        # Parsear JSON fields
        parsed_data = plan.parse_json_fields()
        
        result = plan.to_dict()
        result.update(parsed_data)
        result.update({
            'descripcion_peligro': plan.descripcion_peligro,
            'antecedentes_historicos': plan.antecedentes_historicos,
            'poblacion_expuesta': plan.poblacion_expuesta,
            'activos_expuestos': plan.activos_expuestos,
            'supuestos_limitaciones': plan.supuestos_limitaciones,
            'puntos_criticos': json.loads(plan.puntos_criticos) if plan.puntos_criticos else [],
            'rutas_abastecimiento': plan.rutas_abastecimiento,
            'vocerías': plan.vocerías,
            'formatos_boletines': plan.formatos_boletines,
            'grupos_vulnerables': plan.grupos_vulnerables,
            'kits_humanitarios': plan.kits_humanitarios,
            'fuentes_financiamiento': plan.fuentes_financiamiento,
            'instituciones_participantes': plan.instituciones_participantes,
            'indicadores_activacion': plan.indicadores_activacion,
            'cronograma_simulacros': plan.cronograma_simulacros,
            'lecciones_aprendidas': plan.lecciones_aprendidas,
            'archivos_anexos': json.loads(plan.archivos_anexos) if plan.archivos_anexos else [],
            'multimedia_embed': json.loads(plan.multimedia_embed) if plan.multimedia_embed else {},
            'plan_oficial': _get_oficial(plan),
        })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@contingencia_api.route('', methods=['GET'])
def listar_planes():
    """Lista planes con filtros opcionales"""
    try:
        PlanContingencia = get_models()
        tipo_evento = request.args.get('tipo_evento')
        estado = request.args.get('estado')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        per_page = max(1, min(per_page, 100))
        
        query = PlanContingencia.query
        
        if tipo_evento:
            query = query.filter_by(tipo_evento=tipo_evento)
        if estado:
            query = query.filter_by(estado=estado)
        
        query = query.order_by(PlanContingencia.created_at.desc())
        
        db = get_db()
        pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'planes': [p.to_dict() for p in pagination.items]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@contingencia_api.route('/<int:plan_id>', methods=['PUT'])
def actualizar_plan(plan_id):
    """Actualiza un plan existente"""
    PlanContingencia = get_models()
    db = get_db()
    plan = PlanContingencia.query.get_or_404(plan_id)
    data = request.get_json()
    
    try:
        # Actualizar campos simples
        if 'nombre_plan' in data:
            plan.nombre_plan = data['nombre_plan']
        if 'descripcion_peligro' in data:
            plan.descripcion_peligro = data['descripcion_peligro']
        if 'antecedentes_historicos' in data:
            plan.antecedentes_historicos = data['antecedentes_historicos']
        if 'supuestos_limitaciones' in data:
            plan.supuestos_limitaciones = data['supuestos_limitaciones']
        if 'estado' in data:
            plan.estado = data['estado']
        if 'responsable_principal' in data:
            plan.responsable_principal = data['responsable_principal']
        
        # Actualizar campos JSON
        json_fields = [
            'umbrales_alertas', 'sistema_alerta', 'estructura_organizativa',
            'fase_preparacion', 'fase_alistamiento', 'fase_respuesta',
            'fase_rehabilitacion', 'inventario_recursos', 'albergues',
            'canales_comunicacion', 'protocolos_salud', 'presupuesto_por_fase'
        ]
        
        for field in json_fields:
            if field in data:
                setattr(plan, field, json.dumps(data[field]))
        
        plan.updated_at = datetime.utcnow()
        plan.usuario_modificador = data.get('usuario_modificador', 'Sistema')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'numero_plan': plan.numero_plan,
            'estado': plan.estado,
            'mensaje': 'Plan actualizado exitosamente'
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error actualizar_plan: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'mensaje': 'Error al actualizar plan'
        }), 400


@contingencia_api.route('/<int:plan_id>', methods=['DELETE'])
def eliminar_plan(plan_id):
    """Elimina un plan"""
    PlanContingencia = get_models()
    db = get_db()
    plan = PlanContingencia.query.get_or_404(plan_id)
    
    try:
        db.session.delete(plan)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': f'Plan {plan.numero_plan} eliminado'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@contingencia_api.route('/<int:plan_id>/estado', methods=['PUT'])
def actualizar_estado(plan_id):
    """Actualiza el estado del plan y registra aprobación si aplica"""
    PlanContingencia = get_models()
    db = get_db()
    plan = PlanContingencia.query.get_or_404(plan_id)
    data = request.get_json() or {}
    
    try:
        nuevo_estado = data.get('estado')
        if not nuevo_estado:
            return jsonify({'success': False, 'error': 'Falta estado'}), 400
        
        estados_validos = {'Borrador', 'En_revision', 'Aprobado', 'Aprobado_Comite'}
        if nuevo_estado not in estados_validos:
            return jsonify({'success': False, 'error': 'Estado no válido'}), 400
        
        plan.estado = nuevo_estado
        
        # Si se aprueba, registrar resolución y aprobador
        if nuevo_estado in {'Aprobado', 'Aprobado_Comite'}:
            plan.aprobado_por = data.get('aprobado_por') or plan.aprobado_por or 'Comité de Gestión del Riesgo'
            if data.get('numero_resolucion'):
                plan.numero_resolucion = data.get('numero_resolucion')
            if data.get('fecha_resolucion'):
                try:
                    plan.fecha_resolucion = datetime.fromisoformat(data.get('fecha_resolucion')).date()
                except Exception:
                    plan.fecha_resolucion = datetime.utcnow().date()
            else:
                plan.fecha_resolucion = datetime.utcnow().date()
        
        plan.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'id': plan.id,
            'numero_plan': plan.numero_plan,
            'estado': plan.estado
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# RUTAS OFICIALES (formato Word institucional)
# ============================================================================


@contingencia_api.route('/<int:plan_id>/seccion/<seccion>', methods=['PUT'])
def actualizar_seccion_oficial(plan_id, seccion):
    """Guarda una sección oficial dentro de multimedia_embed.plan_oficial."""
    PlanContingencia = get_models()
    db = get_db()
    plan = PlanContingencia.query.get_or_404(plan_id)
    data = request.get_json() or {}

    try:
        oficial = _get_oficial(plan)
        oficial[seccion] = data
        _save_oficial(plan, oficial)
        plan.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'plan_oficial': oficial})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@contingencia_api.route('/<int:plan_id>/oficial', methods=['GET'])
def obtener_plan_oficial(plan_id):
    PlanContingencia = get_models()
    plan = PlanContingencia.query.get_or_404(plan_id)
    return jsonify({'plan_oficial': _get_oficial(plan)})


@contingencia_api.route('/datos-municipio', methods=['GET'])
def datos_municipio_supata():
    return jsonify(get_datos_supata())


@contingencia_api.route('/plantilla/<tipo_evento>/<seccion>', methods=['GET'])
def plantilla_por_tipo(tipo_evento, seccion):
    return jsonify(get_plantilla_por_tipo(tipo_evento, seccion) or {})


# ============================================================================
# GENERACIÓN DE PDF CON PORTADA Y TOC
# ============================================================================

def _render_plan_pdf(plan, filename="plan_contingencia.pdf"):
    """Genera PDF profesional del plan usando formato oficial de Alcaldía"""
    try:
        # Convertir modelo ORM a diccionario para el generador
        plan_dict = {
            'numero_plan': plan.numero_plan,
            'tipo_evento': plan.tipo_evento.replace('_', ' '),
            'descripcion': plan.descripcion_peligro or 'No especificado',
            'cobertura': plan.ambito or 'Municipal',
            'responsable_plan': plan.responsable_principal or 'No especificado',
            'escenario': plan.antecedentes_historicos or 'Descripción del escenario no disponible',
            'estado': (plan.estado or 'Borrador'),
            'aprobado_por': plan.aprobado_por or '',
            'numero_resolucion': plan.numero_resolucion or '',
            'fecha_resolucion': plan.fecha_resolucion.strftime('%Y-%m-%d') if plan.fecha_resolucion else '',
            'umbrales': [],
            'roles': [],
            'fases': [],
            'recursos_disponibles': [],
            'albergues': [],
            'comunicaciones': 'Plan de comunicaciones',
            'salud': 'Atención en salud',
            'presupuesto': [],
            'presupuesto_total': 0,
            'elaborado_por': plan.responsable_principal or '',
            'revisado_por': '',
            'aprobado_por': plan.aprobado_por or ''
        }
        
        # Usar el nuevo generador profesional
        generador = PDFPlanContingenciaOficial(plan_dict, current_app)
        pdf_buffer = generador.generar()
        
        if not pdf_buffer:
            logger.warning("El generador retornó None")
            return None
        
        return pdf_buffer
    
    except Exception as e:
        logger.error(f"Error generando PDF: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return None
        return None


def _add_section_title(c, title, color_primary, color_accent, y_position=None):
    """Agrega título de sección con línea decorativa"""
    w, h = letter
    if y_position is None:
        y_position = h - 80
    
    c.setFont('Helvetica-Bold', 14)
    c.setFillColor(colors.HexColor(color_primary))
    c.drawString(60, y_position, title)
    
    # Línea decorativa
    c.setStrokeColor(colors.HexColor(color_accent))
    c.setLineWidth(1.5)
    c.line(60, y_position - 5, w - 60, y_position - 5)


def _add_text_section(c, subtitle, content, y_pos, color_text):
    """Agrega sección de texto con subtítulo"""
    c.setFont('Helvetica-Bold', 11)
    c.setFillColor(colors.HexColor(color_text))
    c.drawString(80, y_pos, subtitle)
    
    c.setFont('Helvetica', 10)
    c.setFillColor(colors.HexColor(color_text))
    
    if content:
        style = ParagraphStyle(
            'body',
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor(color_text),
            alignment=0
        )
        
        para = Paragraph(content[:300] if len(content) > 300 else content, style)
        w, h = letter
        para.wrapOn(c, w - 160, 150)
        para.drawOn(c, 80, y_pos - 120)


def _apply_table_style(table, color_header):
    """Aplica estilo estándar a tablas"""
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(color_header)),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2c3e50')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d4d4d8')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))


@contingencia_api.route('/<int:plan_id>/pdf', methods=['GET'])
def descargar_pdf(plan_id):
    """Descarga PDF del plan"""
    try:
        PlanContingencia = get_models()
        plan = PlanContingencia.query.get_or_404(plan_id)
        
        pdf_buffer = _render_plan_pdf(plan)
        
        if pdf_buffer:
            filename = f"Plan_Contingencia_{plan.numero_plan}.pdf"
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
        else:
            return jsonify({'error': 'No se pudo generar el PDF'}), 500
    except Exception as e:
        logger.error(f"Error descargando PDF: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@contingencia_api.route('/tipos-eventos', methods=['GET'])
def obtener_tipos_eventos():
    """Retorna tipos de eventos disponibles con configuración"""
    return jsonify(TIPOS_EVENTOS), 200


# ============================================================================
# NUEVOS ENDPOINTS PARA AUTOMATIZACIÓN
# ============================================================================

@contingencia_api.route('/cargar-usuarios', methods=['GET'])
def cargar_usuarios():
    """Carga usuarios del sistema para rellenar automáticamente tablas"""
    try:
        from app.models.usuario import Usuario
        from app import db
        
        usuarios = db.session.query(Usuario).filter(
            Usuario.activo == True
        ).all()
        
        usuarios_data = [
            {
                'id': u.id,
                'nombre': u.nombre_completo or u.usuario,
                'email': u.email,
                'cargo': getattr(u, 'rol_descripcion', 'No especificado'),
                'telefono': getattr(u, 'telefono', ''),
                'departamento': getattr(u, 'secretaria', 'No especificado')
            }
            for u in usuarios
        ]
        
        return jsonify({
            'success': True,
            'usuarios': usuarios_data,
            'total': len(usuarios_data)
        }), 200
    except Exception as e:
        logger.error(f"Error cargando usuarios: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'usuarios': []
        }), 500


@contingencia_api.route('/datos-sugeridos/<tipo_evento>', methods=['GET'])
def obtener_datos_sugeridos(tipo_evento):
    """Retorna datos sugeridos según el tipo de evento para auto-relleno"""
    try:
        if tipo_evento not in TIPOS_EVENTOS:
            return jsonify({'error': 'Tipo de evento no válido'}), 400
        
        evento_config = TIPOS_EVENTOS[tipo_evento]
        
        # Obtener descripciones y antecedentes según el tipo
        datos_sugeridos = {
            'tipo_evento': tipo_evento,
            'nombre_evento': tipo_evento.replace('_', ' '),
            'icono': evento_config.get('icon'),
            'color': evento_config.get('color'),
            'umbrales': evento_config.get('umbrales', {}),
            'sectores_recomendados': evento_config.get('sectores', []),
            'descripcion_base': _obtener_descripcion_base(tipo_evento),
            'antecedentes': _obtener_antecedentes(tipo_evento),
            'recursos_minimos': _obtener_recursos_minimos(tipo_evento)
        }
        
        return jsonify(datos_sugeridos), 200
    except Exception as e:
        logger.error(f"Error obteniendo datos sugeridos: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# FUNCIONES AUXILIARES PARA AUTO-RELLENO
# ============================================================================

def _obtener_descripcion_base(tipo_evento):
    """Retorna una descripción base según el tipo de evento"""
    descripciones = {
        'Lluvias': 'Plan de contingencia para eventos de lluvias extremas. Incluye medidas de prevención, alerta temprana y respuesta de emergencia.',
        'Incendios': 'Plan de contingencia para incendios forestales y urbanos. Incluye evacuación, control de propagación y atención de afectados.',
        'Eventos_masivos': 'Plan de contingencia para eventos masivos. Incluye control de multitudes, seguridad y atención de emergencias médicas.',
        'Deslizamientos': 'Plan de contingencia para deslizamientos de tierra. Incluye monitoreo geotécnico, evacuación y rehabilitación.',
        'Sequía': 'Plan de contingencia para períodos de sequía. Incluye racionamiento de agua, atención agrícola y protección de ecosistemas.',
        'Epidemias': 'Plan de contingencia para brotes epidemiológicos. Incluye aislamiento, tratamiento y comunicación de riesgos.'
    }
    return descripciones.get(tipo_evento, 'Plan de contingencia para ' + tipo_evento)


def _obtener_antecedentes(tipo_evento):
    """Retorna antecedentes históricos según el tipo de evento"""
    antecedentes_dict = {
        'Lluvias': 'Se han registrado eventos de lluvias intensas en la región con impactos en infraestructura vial e inmuebles.',
        'Incendios': 'Se han presentado varios incendios en zonas boscosas y urbanas con pérdidas materiales significativas.',
        'Eventos_masivos': 'La región alberga eventos culturales, deportivos y religiosos con alta concentración de personas.',
        'Deslizamientos': 'Existen zonas de alto riesgo por deslizamientos en laderas de la región.',
        'Sequía': 'Se ha registrado disminución de precipitaciones que afecta fuentes de agua.',
        'Epidemias': 'La región es susceptible a brotes de enfermedades transmisibles según datos epidemiológicos.'
    }
    return antecedentes_dict.get(tipo_evento, 'Se han reportado eventos de este tipo en la región.')


def _obtener_recursos_minimos(tipo_evento):
    """Retorna recursos mínimos necesarios según el tipo de evento"""
    recursos = {
        'Lluvias': ['Bombas de achique', 'Personal de rescate', 'Movilización', 'Albergues'],
        'Incendios': ['Equipos de bomberos', 'Vehículos', 'Personal capacitado', 'Agua'],
        'Eventos_masivos': ['Personal de seguridad', 'Servicios médicos', 'Movilización', 'Puntos de control'],
        'Deslizamientos': ['Equipos de excavación', 'Personal técnico', 'Albergues', 'Servicios médicos'],
        'Sequía': ['Sistemas de abastecimiento', 'Agua', 'Asistencia agrícola', 'Información'],
        'Epidemias': ['Kits médicos', 'Aislamiento', 'Información', 'Servicios de salud']
    }
    return recursos.get(tipo_evento, [])
