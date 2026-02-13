"""
API Endpoints para Gestión Arbórea - Gestión del Riesgo
IMPORTACIONES LAZY PARA EVITAR CIRCULAR IMPORTS
"""
from flask import Blueprint, request, jsonify, send_file, render_template, current_app
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
        radicado.usuario_creador = data.get('usuario_creador', 'Sistema')
        
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
            'compensacion_arboles_plantar': radicado.compensacion_arboles_plantar,
            'permiso_fecha_limite': radicado.permiso_fecha_limite.isoformat() if radicado.permiso_fecha_limite else None,
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
    try:
        logger.info(f"[GET] Obteniendo radicado ID: {radicado_id}")
        RadicadoArborea, _ = get_models()
        radicado = RadicadoArborea.query.get_or_404(radicado_id)
        
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


# ============================================================================
# PDF - Generación de informe técnico y dictamen
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
            textColor=colors.HexColor('#2d5016'),
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
        c.setFillColor(colors.HexColor('#2d5016'))
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
        
        # Línea de acento verde institucional
        c.setStrokeColor(colors.HexColor('#7cb342'))
        c.setLineWidth(2)
        c.line(margin, y_position, margin + (w - 2*margin), y_position)
        c.setLineWidth(1)
        y_position -= 16
        
        # Contenido según template
        if template_name == 'pdf_informe_arborea.html':
            y_position = _render_informe_content(c, radicado, margin, y_position, w, h, style_title, style_body)
        else:
            y_position = _render_dictamen_content(c, radicado, margin, y_position, w, h, style_title, style_body)
        
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
    COLOR_PRIMARY = '#2d5016'  # Verde institucional oscuro
    COLOR_HEADER_BG = '#5a8a3a'  # Verde medio profesional
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
    COLOR_PRIMARY = '#2d5016'  # Verde institucional oscuro
    COLOR_HEADER_BG = '#5a8a3a'  # Verde medio profesional
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
        obl_para = Paragraph(radicado.permiso_obligaciones[:400], style)
        w_obl, h_obl = obl_para.wrap(table_width, 150)
        
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
    
    data = [
        ['Árboles a plantar', str(radicado.compensacion_arboles_plantar) if radicado.compensacion_arboles_plantar else '-'],
        ['Especie recomendada', radicado.compensacion_especie_recomendada or '-'],
        ['Sitio de plantación', radicado.compensacion_sitio or '-'],
        ['Plazo', radicado.compensacion_plazo or '30 días'],
        ['Método de cálculo', radicado.compensacion_metodo or '-']
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
    
    if y_position - h_table < 100:
        c.showPage()
        y_position = h - 140
    
    table.drawOn(c, margin, y_position - h_table)
    y_position -= (h_table + 12)
    
    # Pie
    if y_position < 80:
        c.showPage()
        y_position = h - 140
    
    c.setFont('Helvetica-Oblique', 8)
    c.setFillColor(colors.gray)
    c.drawString(margin, y_position, f'Generado automáticamente por el Sistema de Gestión Arbórea — {radicado.usuario_creador or "admin"}')
    
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
    """Genera y descarga el PDF del dictamen CMGR (Fase 3)."""
    try:
        RadicadoArborea, _ = get_models()
        radicado = RadicadoArborea.query.get_or_404(radicado_id)
        context = {
            'radicado': radicado,
            'titulo': 'Permiso – Dictamen CMGR',
        }
        filename = f"Dictamen_{radicado.numero_radicado}.pdf"
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
        # Actualizar campos de visita técnica
        if 'visita_fecha' in data:
            radicado.visita_fecha = datetime.fromisoformat(data['visita_fecha'])
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
        
        # Actualizar campos de dictamen y permiso
        if 'dictamen_decision' in data:
            radicado.dictamen_decision = data['dictamen_decision']
            # Actualizar estado según decisión
            if data['dictamen_decision'] == 'Aprobado':
                radicado.estado = 'Aprobada'
            elif data['dictamen_decision'] == 'Negado':
                radicado.estado = 'Negada'
        
        if 'permiso_vigencia_dias' in data:
            radicado.permiso_vigencia_dias = data['permiso_vigencia_dias']
            radicado.permiso_fecha_emision = datetime.utcnow()
            radicado.calcular_fecha_limite()
        
        if 'permiso_obligaciones' in data:
            radicado.permiso_obligaciones = data['permiso_obligaciones']
        
        # Actualizar campos de compensación
        if 'compensacion_coeficiente' in data:
            radicado.compensacion_coeficiente = data['compensacion_coeficiente']
        if 'compensacion_metodo' in data:
            radicado.compensacion_metodo = data['compensacion_metodo']
        if 'compensacion_especie_recomendada' in data:
            radicado.compensacion_especie_recomendada = data['compensacion_especie_recomendada']
        if 'compensacion_sitio' in data:
            radicado.compensacion_sitio = data['compensacion_sitio']
        
        # Recalcular compensación si es automático
        if radicado.compensacion_metodo == 'Automático' and radicado.arbol_dap_cm and radicado.compensacion_coeficiente:
            radicado.calcular_compensacion_automatica()
        
        radicado.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
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
    """Elimina un radicado (solo admin)"""
    RadicadoArborea, _ = get_models()
    db = get_db()
    
    # Verificar permisos (simplificado)
    usuario_actual = request.headers.get('X-Usuario-Actual')
    if usuario_actual != 'admin':
        return jsonify({
            'success': False,
            'mensaje': 'No tienes permisos para eliminar radicados'
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
