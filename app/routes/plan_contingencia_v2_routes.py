"""
Rutas para gestión de Planes de Contingencia V2
Estructura completa con auto-población de datos de Supatá
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_file, current_app, session
from datetime import datetime
import json
import os
import io
import base64
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from PyPDF2 import PdfReader, PdfWriter

contingencia_bp = Blueprint('contingencia', __name__, url_prefix='/gestion-riesgo')

# Datos de Supatá - Auto-población
SUPATA_DATA = {
    "municipio": "Supatá",
    "departamento": "Cundinamarca",
    "poblacion_total": 6428,
    "altitud": 1798,
    "clima_municipio": "Bosque húmedo premontano",
    "temperatura_promedio": "12-16°C",
    "organismos_emergencia": [
        {"nombre": "Bomberos", "tipo": "Incendios", "telefono": "119"},
        {"nombre": "Cruz Roja", "tipo": "Emergencias", "telefono": "01800 5198534"},
        {"nombre": "Policía", "tipo": "Seguridad", "telefono": "123"},
    ]
}


@contingencia_bp.route('/planes-contingencia-v2', methods=['GET'])
def listar_planes():
    """Muestra el historial de planes creados"""
    es_admin = str(session.get('user_role', '')).lower() == 'admin'
    return render_template('plan_contingencia_lista.html', 
                         planes=[],
                         supata_info=SUPATA_DATA,
                         es_admin=es_admin)


@contingencia_bp.route('/planes-contingencia-v2/crear', methods=['GET', 'POST'])
def crear_plan():
    """Crea un nuevo plan de contingencia con datos de Supatá pre-poblados"""
    
    if request.method == 'POST':
        try:
            # Recopilar datos del formulario
            datos_plan = {
                'numero_plan': request.form.get('numero_plan', ''),
                'nombre_plan': request.form.get('nombre_plan', ''),
                'tipo_evento': request.form.get('tipo_evento', ''),
                'municipio': SUPATA_DATA['municipio'],
                'departamento': SUPATA_DATA['departamento'],
                'poblacion_municipio': SUPATA_DATA['poblacion_total'],
            }
            
            # Por ahora solo retornamos un JSON de éxito
            # En el futuro se guardará en base de datos
            return jsonify({
                "status": "success", 
                "message": "Plan creado correctamente",
                "plan_id": 1,
                "datos": datos_plan
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error al crear plan: {str(e)}"
            }), 400
    
    # GET: Mostrar formulario
    return render_template('plan_contingencia_crear.html', 
                         supata_info=SUPATA_DATA)


@contingencia_bp.route('/planes-contingencia-v2/<int:id>', methods=['GET'])
def ver_plan(id):
    """Ver detalle completo del plan en formato de vista previa"""
    # Retorna una página HTML que carga el plan desde localStorage del navegador
    return render_template('plan_contingencia_ver.html',
                         plan_id=id,
                         supata_info=SUPATA_DATA)


@contingencia_bp.route('/planes-contingencia-v2/editar/<int:id>', methods=['GET', 'POST'])
def editar_plan(id):
    """Editar un plan de contingencia existente"""
    if request.method == 'POST':
        try:
            # Los datos se guardan vía JavaScript en localStorage
            return jsonify({
                "status": "success",
                "message": "Plan actualizado correctamente"
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error al actualizar: {str(e)}"
            }), 400
    
    return render_template('plan_contingencia_editar.html',
                         plan_id=id,
                         supata_info=SUPATA_DATA)


@contingencia_bp.route('/planes-contingencia-v2/descargar-pdf/<int:plan_id>', methods=['POST'])
def descargar_pdf(plan_id):
    """Genera y descarga el PDF del plan con formato oficial"""
    try:
        # Recibir los datos del plan desde el cliente
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Generar PDF usando reportlab con formato profesional
        pdf_buffer = _generar_pdf_profesional(data)
        
        # Combinar con el formato oficial si existe
        pdf_final = _combinar_con_formato_oficial(pdf_buffer, data)
        
        nombre_archivo = (data.get('nombre_plan', 'Plan-Contingencia') or 'Plan-Contingencia').replace(' ', '-') + '.pdf'
        
        return send_file(
            pdf_final,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=nombre_archivo
        )
    except Exception as e:
        print(f"Error generando PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def _combinar_con_formato_oficial(pdf_buffer, plan):
    """Combina el PDF generado con el FORMATO.pdf oficial de la Alcaldía"""
    try:
        # Ruta del formato oficial
        formato_path = os.path.join(current_app.config.get('DATA_DIR', os.path.join(current_app.root_path, 'datos')), 'FORMATO.pdf')
        
        if not os.path.exists(formato_path):
            print(f"ADVERTENCIA: {formato_path} no encontrado. Devolviendo PDF sin formato oficial")
            pdf_buffer.seek(0)
            return pdf_buffer
        
        # Leer el PDF generado y el formato oficial
        overlay_pdf = PdfReader(pdf_buffer)
        template_pdf = PdfReader(formato_path)
        output = PdfWriter()
        
        # Combinar cada página del overlay con el formato
        for page_num in range(len(overlay_pdf.pages)):
            # Usar la primera página del formato como template
            template_page = PdfReader(formato_path).pages[0]
            overlay_page = overlay_pdf.pages[page_num]
            
            # Mergear el contenido sobre el formato
            template_page.merge_page(overlay_page)
            output.add_page(template_page)
        
        # Escribir el PDF final
        final_buffer = io.BytesIO()
        output.write(final_buffer)
        final_buffer.seek(0)
        
        return final_buffer
        
    except Exception as e:
        print(f"Error al combinar con formato oficial: {str(e)}")
        import traceback
        traceback.print_exc()
        # Si hay error, devolver el PDF sin formato
        pdf_buffer.seek(0)
        return pdf_buffer


def _generar_pdf_profesional(plan):
    """Genera un PDF profesional del plan de contingencia con formato oficial"""
    
    # Colores oficiales
    COLOR_PRIMARY = HexColor('#1a472a')      # Verde oscuro
    COLOR_SECONDARY = HexColor('#2d5016')    # Verde intermedio
    COLOR_ACCENT = HexColor('#7cb342')       # Verde claro
    COLOR_TEXT = HexColor('#333333')
    
    pdf_buffer = io.BytesIO()
    
    # Crear documento con márgenes ajustados para respetar el formato oficial
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=0.85*inch,
        leftMargin=0.85*inch,
        topMargin=1.8*inch,  # Más espacio arriba para el logo y header
        bottomMargin=1*inch,  # Más espacio abajo para el footer
        title=plan.get('nombre_plan', 'Plan de Contingencia')
    )
    
    # Obtener estilos
    styles = getSampleStyleSheet()
    
    # Crear estilos personalizados
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,  # Reducido de 24
        textColor=COLOR_PRIMARY,
        spaceAfter=4,  # Reducido
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitulo_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=12,  # Reducido de 14
        textColor=COLOR_SECONDARY,
        spaceAfter=8,  # Reducido
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    seccion_style = ParagraphStyle(
        'CustomSection',
        parent=styles['Heading2'],
        fontSize=11,  # Reducido de 12
        textColor=colors.white,
        backColor=COLOR_PRIMARY,
        spaceAfter=8,  # Reducido
        spaceBefore=4,  # Reducido
        leftIndent=8,
        rightIndent=8,
        topPadding=5,  # Reducido
        bottomPadding=5,  # Reducido
        fontName='Helvetica-Bold'
    )
    
    campo_label_style = ParagraphStyle(
        'FieldLabel',
        parent=styles['Normal'],
        fontSize=9,  # Reducido de 10
        textColor=COLOR_PRIMARY,
        fontName='Helvetica-Bold',
        spaceAfter=1  # Reducido de 2
    )
    
    campo_value_style = ParagraphStyle(
        'FieldValue',
        parent=styles['Normal'],
        fontSize=9,  # Mantiene el tamaño
        textColor=COLOR_TEXT,
        fontName='Helvetica',
        spaceAfter=6,  # Reducido de 8
        alignment=TA_JUSTIFY,
        leftIndent=12
    )
    
    # Contenido del documento
    contenido = []
    
    # ========== PORTADA (más compacta) ==========
    contenido.append(Spacer(1, 0.1*inch))
    contenido.append(Paragraph("PLAN DE CONTINGENCIA", titulo_style))
    contenido.append(Spacer(1, 0.1*inch))
    
    nombre_plan = plan.get('nombre_plan', 'Sin nombre')
    contenido.append(Paragraph(nombre_plan, subtitulo_style))
    contenido.append(Spacer(1, 0.2*inch))
    
    # Información básica en portada
    info_portada_data = [
        ["MUNICIPIO:", plan.get('municipio', 'Supatá')],
        ["DEPARTAMENTO:", plan.get('departamento', 'Cundinamarca')],
        ["TIPO DE EVENTO:", plan.get('tipo_evento', 'N/A')],
        ["NÚMERO DEL PLAN:", plan.get('numero_plan', 'N/A')],
        ["FECHA DE CREACIÓN:", plan.get('fecha_creacion', datetime.now().isoformat())[:10]],
    ]
    
    tabla_portada = Table(info_portada_data, colWidths=[2*inch, 3.5*inch])
    tabla_portada.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), COLOR_PRIMARY),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, HexColor('#f0f0f0')]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    contenido.append(tabla_portada)
    contenido.append(PageBreak())
    
    # ========== CONTENIDO ==========
    
    # 1. INTRODUCCIÓN
    contenido.append(Paragraph("1. INTRODUCCIÓN", seccion_style))
    contenido.extend(_agregar_campo(plan, 'introduccion_descripcion', 'Descripción del Evento', campo_label_style, campo_value_style))
    contenido.extend(_agregar_campo(plan, 'introduccion_justificacion', 'Justificación del Plan', campo_label_style, campo_value_style))
    contenido.extend(_agregar_campo(plan, 'introduccion_contexto', 'Contexto General', campo_label_style, campo_value_style))
    contenido.append(Spacer(1, 0.15*inch))
    
    # 2. OBJETIVOS Y ALCANCE
    contenido.append(Paragraph("2. OBJETIVOS Y ALCANCE", seccion_style))
    contenido.extend(_agregar_campo(plan, 'objetivo_general', 'Objetivo General', campo_label_style, campo_value_style))
    contenido.extend(_agregar_campo(plan, 'alcance_evento', 'Descripción del Evento', campo_label_style, campo_value_style))
    contenido.extend(_agregar_campo(plan, 'alcance_ubicacion', 'Ubicación Geográfica', campo_label_style, campo_value_style))
    contenido.extend(_agregar_campo(plan, 'alcance_duracion', 'Duración del Evento', campo_label_style, campo_value_style))
    contenido.extend(_agregar_campo(plan, 'alcance_aforo', 'Aforo Estimado', campo_label_style, campo_value_style))
    contenido.append(Spacer(1, 0.15*inch))
    
    # 3. MARCO NORMATIVO
    contenido.append(PageBreak())
    contenido.append(Paragraph("3. MARCO NORMATIVO", seccion_style))
    contenido.extend(_agregar_campo(plan, 'marco_normativo', 'Normatividad Aplicable', campo_label_style, campo_value_style))
    contenido.append(Spacer(1, 0.15*inch))
    
    # 4. ORGANIZACIÓN
    contenido.append(Paragraph("4. ORGANIZACIÓN Y RESPONSABILIDADES", seccion_style))
    contenido.extend(_agregar_campo(plan, 'coordinador_general', 'Coordinador General del Plan', campo_label_style, campo_value_style))
    contenido.extend(_agregar_campo(plan, 'pmu_ubicacion', 'Ubicación del PMU', campo_label_style, campo_value_style))
    contenido.extend(_agregar_campo(plan, 'organismos_apoyo', 'Organismos de Apoyo', campo_label_style, campo_value_style))
    contenido.append(Spacer(1, 0.15*inch))
    
    # 5. ANÁLISIS DE AMENAZAS
    contenido.append(Paragraph("5. ANÁLISIS DE AMENAZAS", seccion_style))
    contenido.extend(_agregar_campo(plan, 'descripcion_escenario', 'Descripción del Escenario', campo_label_style, campo_value_style))
    contenido.extend(_agregar_campo(plan, 'amenazas_identificadas', 'Amenazas Identificadas', campo_label_style, campo_value_style))
    contenido.extend(_agregar_campo(plan, 'vulnerabilidades', 'Vulnerabilidades', campo_label_style, campo_value_style))
    contenido.append(Spacer(1, 0.15*inch))
    
    # 6. MEDIDAS DE REDUCCIÓN
    contenido.append(PageBreak())
    contenido.append(Paragraph("6. MEDIDAS DE REDUCCIÓN DEL RIESGO", seccion_style))
    contenido.extend(_agregar_campo(plan, 'medidas_seguridad', 'Medidas de Seguridad', campo_label_style, campo_value_style))
    contenido.extend(_agregar_campo(plan, 'adecuacion_lugar', 'Adecuación del Lugar', campo_label_style, campo_value_style))
    contenido.extend(_agregar_campo(plan, 'capacitacion_personal', 'Capacitación del Personal', campo_label_style, campo_value_style))
    contenido.append(Spacer(1, 0.15*inch))
    
    # 7. RESPUESTA Y EVACUACIÓN
    contenido.append(Paragraph("7. PROCEDIMIENTOS DE RESPUESTA", seccion_style))
    contenido.extend(_agregar_campo(plan, 'procedimiento_general', 'Procedimiento General', campo_label_style, campo_value_style))
    contenido.extend(_agregar_campo(plan, 'rutas_evacuacion', 'Rutas de Evacuación', campo_label_style, campo_value_style))
    contenido.extend(_agregar_campo(plan, 'puntos_encuentro', 'Puntos de Encuentro', campo_label_style, campo_value_style))
    contenido.extend(_agregar_campo(plan, 'capacidad_rutas', 'Capacidad de Rutas', campo_label_style, campo_value_style))
    contenido.extend(_agregar_campo(plan, 'recursos_disponibles', 'Recursos Disponibles', campo_label_style, campo_value_style))
    contenido.append(Spacer(1, 0.15*inch))
    
    # 8. ACTUALIZACIÓN
    contenido.append(PageBreak())
    contenido.append(Paragraph("8. ACTUALIZACIÓN DEL PLAN", seccion_style))
    contenido.extend(_agregar_campo(plan, 'responsable_actualizacion', 'Responsable de Actualización', campo_label_style, campo_value_style))
    contenido.extend(_agregar_campo(plan, 'frecuencia_actualizacion', 'Frecuencia de Actualización', campo_label_style, campo_value_style))
    contenido.append(Spacer(1, 0.15*inch))
    
    # 9. OBSERVACIONES Y ANEXOS
    contenido.append(Paragraph("9. ANEXOS Y OBSERVACIONES", seccion_style))
    
    # Agregar imágenes anexas si existen
    anexos_imagenes = plan.get('anexos_imagenes', [])
    if anexos_imagenes and isinstance(anexos_imagenes, list) and len(anexos_imagenes) > 0:
        contenido.append(Paragraph("ANEXOS VISUALES", campo_label_style))
        contenido.append(Spacer(1, 0.1*inch))
        
        for idx, anexo in enumerate(anexos_imagenes, 1):
            try:
                # Título del anexo
                descripcion = anexo.get('descripcion', f'Anexo {idx}')
                contenido.append(Paragraph(f"<b>Anexo {idx}:</b> {descripcion}", campo_value_style))
                contenido.append(Spacer(1, 0.05*inch))
                
                # Procesar imagen
                data_base64 = anexo.get('data', '')
                tipo = anexo.get('tipo', '')
                
                # Si es imagen, insertar en PDF
                if data_base64 and tipo.startswith('image'):
                    # Eliminar prefijo data:image/...;base64,
                    if ',' in data_base64:
                        data_base64 = data_base64.split(',', 1)[1]
                    
                    # Decodificar base64
                    imagen_bytes = base64.b64decode(data_base64)
                    imagen_buffer = io.BytesIO(imagen_bytes)
                    
                    # Crear imagen en PDF (con ancho máximo de 5 pulgadas)
                    img = Image(imagen_buffer, width=5*inch, height=3.5*inch)
                    contenido.append(img)
                    contenido.append(Spacer(1, 0.1*inch))
                    
                elif tipo == 'application/pdf':
                    # Si es PDF, solo mencionar
                    nombre_archivo = anexo.get('nombre_archivo', 'documento.pdf')
                    contenido.append(Paragraph(f"📄 <i>Documento PDF adjunto: {nombre_archivo}</i>", campo_value_style))
                    contenido.append(Spacer(1, 0.1*inch))
                
            except Exception as e:
                print(f"Error procesando anexo {idx}: {str(e)}")
                contenido.append(Paragraph(f"<i>[Error al cargar anexo {idx}]</i>", campo_value_style))
        
        contenido.append(Spacer(1, 0.15*inch))
    
    contenido.extend(_agregar_campo(plan, 'observaciones', 'Observaciones Adicionales', campo_label_style, campo_value_style))
    contenido.append(Spacer(1, 0.3*inch))
    
    # Pie de página final - SIEMPRE al final del documento, sin nueva página
    contenido.append(Spacer(1, 0.2*inch))
    pie_text = f"Documento generado automáticamente por el Sistema de Gestión de Riesgo de Desastres<br/>Alcaldía de Supatá, Cundinamarca<br/>Fecha: {datetime.now().strftime('%d de %B de %Y')} - Hora: {datetime.now().strftime('%H:%M:%S')}"
    contenido.append(Paragraph(pie_text, ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=HexColor('#999999'),
        alignment=TA_CENTER,
        spaceBefore=12,
        spaceAfter=12
    )))
    
    # Construir PDF
    doc.build(contenido)
    pdf_buffer.seek(0)
    
    return pdf_buffer


def _agregar_campo(plan, clave, etiqueta, style_label, style_value):
    """Agrega un campo al PDF con etiqueta y valor"""
    valor = plan.get(clave, '')
    if not valor:
        valor = 'No registrado'
    
    # Limpiar HTML si existe
    valor_texto = str(valor).strip()
    
    # Devolver una tupla de elementos en lugar de lista
    elementos = []
    elementos.append(Paragraph(f"<b>{etiqueta}:</b>", style_label))
    elementos.append(Paragraph(valor_texto, style_value))
    return elementos


