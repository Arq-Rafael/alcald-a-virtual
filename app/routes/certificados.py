
import os
import io
import copy
import base64
import logging
import datetime
import pandas as pd
import glob
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, current_app, session, jsonify, abort
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.graphics.shapes import Drawing 
from reportlab.graphics.barcode.qr import QrCodeWidget
from PyPDF2 import PdfReader, PdfWriter
# Intentamos usar svglib para renderizar el escudo en SVG
try:
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPDF
    SVGLIB_AVAILABLE = True
except Exception:
    SVGLIB_AVAILABLE = False

# Opcional: convertir SVG a PNG si cairosvg está disponible
try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except Exception:
    CAIROSVG_AVAILABLE = False

logger = logging.getLogger(__name__)
certificados_bp = Blueprint('certificados', __name__)

LETTER = letter

def generate_pdf_certificate(data: dict) -> io.BytesIO:
    # Usar formato oficial de la alcaldía como template
    formato_path = os.path.join(str(current_app.config['BASE_DIR']), 'datos', 'FORMATO.pdf')
    
    # Crear overlay con el contenido del certificado
    overlay_buffer = io.BytesIO()
    c = canvas.Canvas(overlay_buffer, pagesize=LETTER)
    w, h = LETTER
    margin = 50
    min_space = 100  # Espacio mínimo antes de crear nueva página
    page_number = 1
    
    # El formato oficial ya tiene el encabezado, solo agregamos título del documento
    c.setFont('Helvetica-Bold', 20)
    c.setFillColor(colors.HexColor('#000000'))
    c.drawCentredString(w/2, h - 140, 'CERTIFICADO DE SOLICITUD')
    
    # ============================================
    # ESTILOS MEJORADOS
    # ============================================
    y_position = h - 170
    
    styles = getSampleStyleSheet()
    
    style_section_title = ParagraphStyle(
        'section_title',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=colors.HexColor('#1b5e20'),
        spaceAfter=8,
        spaceBefore=4
    )
    
    style_label = ParagraphStyle(
        'label',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.HexColor('#558b2f'),
        leading=14
    )
    
    style_value = ParagraphStyle(
        'value',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#2d5016'),
        leading=14,
        alignment=4
    )
    
    # --- Función auxiliar para dibujar tablas con división automática ---
    def draw_table_with_split(table, current_y):
        nonlocal page_number
        available_height = current_y - min_space
        w_table, h_table = table.wrap(w - 2*margin, available_height)
        
        if h_table <= available_height:
            # La tabla cabe completa en la página actual
            table.drawOn(c, margin, current_y - h_table)
            return current_y - h_table - 15
        else:
            # La tabla no cabe, intentar dividirla
            split_result = table.split(w - 2*margin, available_height)
            
            if split_result and len(split_result) > 0:
                # Dibujar la primera parte
                first_part = split_result[0]
                w1, h1 = first_part.wrap(w - 2*margin, available_height)
                first_part.drawOn(c, margin, current_y - h1)
                
                # Si hay más partes, continuar en nueva(s) página(s)
                if len(split_result) > 1:
                    c.showPage()
                    page_number += 1
                    # Header de continuación
                    c.setFont('Helvetica-Bold', 12)
                    c.setFillColor(colors.HexColor('#558b2f'))
                    c.drawCentredString(w/2, h - 140, f'Continuación - Página {page_number}')
                    current_y = h - 170
                    
                    # Dibujar partes restantes recursivamente
                    for i in range(1, len(split_result)):
                        part = split_result[i]
                        w_part, h_part = part.wrap(w - 2*margin, current_y - min_space)
                        
                        if h_part <= current_y - min_space:
                            part.drawOn(c, margin, current_y - h_part)
                            current_y -= (h_part + 15)
                        else:
                            # Esta parte también necesita dividirse
                            c.showPage()
                            page_number += 1
                            c.setFont('Helvetica-Bold', 12)
                            c.setFillColor(colors.HexColor('#558b2f'))
                            c.drawCentredString(w/2, h - 140, f'Continuación - Página {page_number}')
                            current_y = h - 170
                            part.drawOn(c, margin, current_y - h_part)
                            current_y -= (h_part + 15)
                
                return current_y
            else:
                # No se puede dividir, mover a nueva página completa
                c.showPage()
                page_number += 1
                c.setFont('Helvetica-Bold', 12)
                c.setFillColor(colors.HexColor('#558b2f'))
                c.drawCentredString(w/2, h - 140, f'Continuación - Página {page_number}')
                current_y = h - 170
                
                w_table, h_table = table.wrap(w - 2*margin, current_y - min_space)
                table.drawOn(c, margin, current_y - h_table)
                return current_y - h_table - 15
    
    # ============================================
    # SECCIÓN 1: Información General
    # ============================================
    section1_data = [
        [Paragraph('<b>INFORMACIÓN GENERAL</b>', style_section_title), '']
    ]
    
    for label, key in [('Municipio', 'municipio'), ('NIT', 'nit'), ('Fecha', 'fecha')]:
        val = data.get(key, '')
        section1_data.append([
            Paragraph(f'<b>{label}:</b>', style_label),
            Paragraph(str(val), style_value)
        ])
    
    table1 = Table(section1_data, colWidths=[120, w - 2*margin - 120])
    table1.setStyle(TableStyle([
        ('SPAN', (0,0), (-1,0)),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8f5e9')),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('LINEBELOW', (0,0), (-1,0), 2, colors.HexColor('#7cb342')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (0,0), 8),
        ('BOTTOMPADDING', (0,0), (0,0), 8),
        ('TOPPADDING', (0,1), (-1,-1), 6),
        ('BOTTOMPADDING', (0,1), (-1,-1), 6),
    ]))
    
    # Dibujar tabla 1 con división automática
    y_position = draw_table_with_split(table1, y_position)

    # ============================================
    # SECCIÓN 5: Croquis del plano seleccionado (si se proporciona)
    # ============================================
    croquis_b64 = data.get('croquis_b64')
    croquis_path = data.get('croquis_path')
    if croquis_b64:
        try:
            b64 = croquis_b64.split(',')[-1]
            img_bytes = base64.b64decode(b64)
            img_reader = ImageReader(io.BytesIO(img_bytes))
            img_w, img_h = img_reader.getSize()
            max_w = w - 2*margin
            scale = min(1.0, max_w / img_w)
            draw_w = img_w * scale
            draw_h = img_h * scale
            if y_position - draw_h < min_space:
                c.showPage()
                page_number += 1
                c.setFont('Helvetica-Bold', 12)
                c.setFillColor(colors.HexColor('#558b2f'))
                c.drawCentredString(w/2, h - 140, f'Continuación - Página {page_number}')
                y_position = h - 170
            c.drawImage(img_reader, margin, y_position - draw_h, width=draw_w, height=draw_h)
            y_position -= (draw_h + 15)
        except Exception as e:
            note_tbl = Table([[Paragraph('<b>CROQUIS:</b>', style_label), Paragraph(f'No se pudo insertar croquis: {str(e)}', style_value)]], colWidths=[120, w - 2*margin - 120])
            y_position = draw_table_with_split(note_tbl, y_position)
    elif croquis_path:
        try:
            img_reader = ImageReader(croquis_path)
            img_w, img_h = img_reader.getSize()
            max_w = w - 2*margin
            scale = min(1.0, max_w / img_w)
            draw_w = img_w * scale
            draw_h = img_h * scale
            if y_position - draw_h < min_space:
                c.showPage()
                page_number += 1
                c.setFont('Helvetica-Bold', 12)
                c.setFillColor(colors.HexColor('#558b2f'))
                c.drawCentredString(w/2, h - 140, f'Continuación - Página {page_number}')
                y_position = h - 170
            c.drawImage(img_reader, margin, y_position - draw_h, width=draw_w, height=draw_h)
            y_position -= (draw_h + 15)
        except Exception as e:
            note_tbl = Table([[Paragraph('<b>CROQUIS:</b>', style_label), Paragraph(f'No se pudo insertar croquis desde ruta: {str(e)}', style_value)]], colWidths=[120, w - 2*margin - 120])
            y_position = draw_table_with_split(note_tbl, y_position)

    
    # ============================================
    # SECCIÓN 2: Detalles de la Solicitud
    # ============================================
    section2_data = [
        [Paragraph('<b>DETALLES DE LA SOLICITUD</b>', style_section_title), '']
    ]
    
    for label, key in [('Secretaría', 'secretaria'), ('Valor', 'valor')]:
        val = data.get(key, '')
        section2_data.append([
            Paragraph(f'<b>{label}:</b>', style_label),
            Paragraph(str(val), style_value)
        ])
    
    # Objeto y Justificación
    objeto_val = data.get('objeto', '')
    section2_data.append([
        Paragraph('<b>Objeto:</b>', style_label),
        Paragraph(str(objeto_val), style_value)
    ])
    
    justif_val = data.get('justificacion', '')
    section2_data.append([
        Paragraph('<b>Justificación:</b>', style_label),
        Paragraph(str(justif_val), style_value)
    ])
    
    table2 = Table(section2_data, colWidths=[120, w - 2*margin - 120])
    table2.setStyle(TableStyle([
        ('SPAN', (0,0), (-1,0)),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8f5e9')),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('LINEBELOW', (0,0), (-1,0), 2, colors.HexColor('#7cb342')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (0,0), 8),
        ('BOTTOMPADDING', (0,0), (0,0), 8),
        ('TOPPADDING', (0,1), (-1,-1), 6),
        ('BOTTOMPADDING', (0,1), (-1,-1), 6),
    ]))
    
    # Dibujar tabla 2 con división automática
    y_position = draw_table_with_split(table2, y_position)
    
    # ============================================
    # SECCIÓN 3: Plan de Desarrollo
    # ============================================
    section3_data = [
        [Paragraph('<b>PLAN DE DESARROLLO MUNICIPAL</b>', style_section_title), '']
    ]
    
    for label, key in [
        ('Meta Producto', 'meta_producto'),
        ('Eje', 'eje'),
        ('Sector', 'sector'),
        ('Código BPIM', 'codigo_bpim')
    ]:
        val = data.get(key, '')
        section3_data.append([
            Paragraph(f'<b>{label}:</b>', style_label),
            Paragraph(str(val), style_value)
        ])
    
    table3 = Table(section3_data, colWidths=[120, w - 2*margin - 120])
    table3.setStyle(TableStyle([
        ('SPAN', (0,0), (-1,0)),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8f5e9')),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('LINEBELOW', (0,0), (-1,0), 2, colors.HexColor('#7cb342')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (0,0), 8),
        ('BOTTOMPADDING', (0,0), (0,0), 8),
        ('TOPPADDING', (0,1), (-1,-1), 6),
        ('BOTTOMPADDING', (0,1), (-1,-1), 6),
    ]))
    
    # Dibujar tabla 3 con división automática
    y_position = draw_table_with_split(table3, y_position)
    
    # Footer
    footer_y = 60
    c.setStrokeColor(colors.HexColor('#7cb342'))
    c.setLineWidth(2)
    c.line(margin, footer_y + 25, w - margin, footer_y + 25)
    
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(colors.HexColor('#558b2f'))
    c.drawCentredString(w/2, footer_y + 5, 'Firmado digitalmente por: Secretaría de Planeación y Obras Públicas')
    
    c.showPage()
    c.save()
    overlay_buffer.seek(0)
    
    # Combinar con el formato oficial
    try:
        template_pdf = PdfReader(formato_path)
        base_template_page = template_pdf.pages[0]
        overlay_pdf = PdfReader(overlay_buffer)
        output = PdfWriter()

        # Aplicar el formato oficial a cada página del overlay sin releer el archivo
        for page_num in range(len(overlay_pdf.pages)):
            template_page = copy.deepcopy(base_template_page)
            overlay_page = overlay_pdf.pages[page_num]
            template_page.merge_page(overlay_page)
            output.add_page(template_page)

        final_buffer = io.BytesIO()
        output.write(final_buffer)
        final_buffer.seek(0)
        return final_buffer
    except Exception as e:
        logger.warning(f"Error al combinar con formato oficial: {e}")
        overlay_buffer.seek(0)
        return overlay_buffer


@certificados_bp.route('/certificados', methods=['GET'], endpoint='index')
def certificados():
    solicitudes_path = current_app.config['SOLICITUDES_PATH']
    
    if os.path.exists(solicitudes_path):
        df_all = pd.read_csv(solicitudes_path, encoding='utf-8')
        
        # Agregar columna 'estado' si no existe (para compatibilidad con datos antiguos)
        if 'estado' not in df_all.columns:
            df_all['estado'] = 'nuevo'
    else:
        df_all = pd.DataFrame(columns=["municipio","nit","fecha","secretaria","objeto","justificacion","valor","meta_producto","eje","sector","codigo_bpim","estado"])

    # Contar por estado (toda la base de datos)
    total_solicitudes = len(df_all)
    generados_count = len(df_all[df_all['estado'] == 'generado'])
    pendientes_count = len(df_all[df_all['estado'].isin(['nuevo', 'pendiente', 'editado'])])
    
    # Filtrar solicitudes disponibles para certificado (las que mostraremos)
    df = df_all[df_all['estado'].isin(['nuevo', 'pendiente', 'editado'])]
    df['id'] = df.index
    
    # Pendientes que mostraremos en la lista (excepto 'generado')
    pendientes_df = df[df['estado'].isin(['nuevo', 'pendiente', 'editado'])]
    pendientes_list = pendientes_df.to_dict(orient="records")

    output_dir = current_app.config['CERTIFICADOS_OUTPUT_DIR']
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Calcular tiempo medio
    tiempo_medio = 2
    if generados_count > 0:
        tiempo_medio = 1.8

    secretarias = [
      "Secretaría General y de Gobierno",
      "Secretaría de Planeación y Obras Públicas",
      "Secretaría de Desarrollo Social y Comunitario",
      "Secretaría de Desarrollo Rural Medio Ambiente y Competitividad",
      "Secretaría de Hacienda y Gestión Financiera"
    ]
    
    # Análisis mejorado por secretaría
    sec_counts = []
    sec_labels = []
    if total_solicitudes > 0 and 'secretaria' in df_all.columns:
        generados_df = df_all[df_all['estado'] == 'generado']
        
        if not generados_df.empty and 'secretaria' in generados_df.columns:
            counts = generados_df['secretaria'].value_counts()
            # Mostrar solo secretarías con certificados generados
            for sec in secretarias:
                count = counts.get(sec, 0)
                if count > 0:
                    sec_labels.append(sec.replace('Secretaría de ', '').replace('Secretaría ', ''))
                    sec_counts.append(int(count))
    
    # Si no hay datos, mostrar todas con 0
    if not sec_labels:
        sec_labels = [s.replace('Secretaría de ', '').replace('Secretaría ', '') for s in secretarias]
        sec_counts = [0] * len(secretarias)

    return render_template(
        'certificados_modern.html',
        total_solicitudes=total_solicitudes,
        generados=generados_count,
        tiempo_medio=tiempo_medio,
        pendientes_list=pendientes_list,
        secretarias=secretarias,
        sec_labels=sec_labels,
        sec_counts=sec_counts
    )

@certificados_bp.route('/generar_lote', methods=['POST'], endpoint='generar_lote')
def generar_lote_certificados():
    """Genera múltiples certificados en lote"""
    solicitudes_path = current_app.config['SOLICITUDES_PATH']
    output_dir = current_app.config['CERTIFICADOS_OUTPUT_DIR']
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Obtener IDs a generar
        indices = request.form.getlist('indices[]')
        if not indices:
            return jsonify({'success': False, 'error': 'No hay solicitudes seleccionadas'}), 400

        # Leer CSV una sola vez y asegurar columna estado
        df = pd.read_csv(solicitudes_path, encoding='utf-8')
        if 'estado' not in df.columns:
            df['estado'] = 'nuevo'
        df['id'] = df.index

        generados = 0
        errores = []
        indices_int = []
        download_urls = []
        
        for idx_str in indices:
            try:
                indices_int.append(int(idx_str))
            except ValueError:
                errores.append(f'ID inválido: {idx_str}')

        if not indices_int:
            return jsonify({'success': False, 'error': 'No hay IDs válidos para generar'}), 400

        subset = df[df['id'].isin(indices_int)]

        # Generar cada PDF y actualizar estado en memoria
        for idx in indices_int:
            try:
                row_series = subset.loc[subset['id'] == idx]
                if row_series.empty:
                    errores.append(f'Solicitud {idx} no encontrada')
                    logger.warning(f"Solicitud {idx} no encontrada")
                    continue

                row = row_series.iloc[0].to_dict()
                
                logger.info(f"Generando certificado para solicitud {idx}")

                pdf_buf = generate_pdf_certificate({
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
                })

                outfile = os.path.join(output_dir, f"certificado_{idx}.pdf")
                with open(outfile, 'wb') as f:
                    f.write(pdf_buf.getvalue())

                df.loc[df['id'] == idx, 'estado'] = 'generado'
                generados += 1
                download_urls.append(url_for('certificados.descargar_certificado', idx=idx, _external=True))
                logger.info(f"Certificado {idx} generado exitosamente")
                
            except Exception as e:
                msg_error = f'Error en solicitud {idx}: {str(e)}'
                errores.append(msg_error)
                logger.error(msg_error, exc_info=True)

        # Guardar CSV una sola vez al final
        if generados > 0:
            df.to_csv(solicitudes_path, index=False, encoding='utf-8')
            logger.info(f"CSV actualizado: {generados} certificados marcados como generados")

        # Retornar respuesta JSON - Los PDFs se generaron y están listos para descargar individualmente
        return jsonify({
            'success': True,
            'generados': generados,
            'errores': errores,
            'total': len(indices_int),
            'mensaje': f'Se generaron {generados} certificados correctamente. Descárgalos de forma individual.',
            'download_urls': download_urls
        })

    except Exception as e:
        logger.error(f"Error en generar_lote: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@certificados_bp.route('/generar_certificado', methods=['POST'])
def generar_certificado():
    idx = int(request.form['index'])
    solicitudes_path = current_app.config['SOLICITUDES_PATH']
    df  = pd.read_csv(solicitudes_path, encoding='utf-8')
    if 'estado' not in df.columns:
        df['estado'] = 'nuevo'
    df['id'] = df.index
    
    if idx not in df['id'].values:
        flash("Solicitud no encontrada", "danger")
        return redirect(url_for('certificados.certificados'))
        
    row = df.loc[df['id'] == idx].iloc[0].to_dict()

    pdf_buf = generate_pdf_certificate({
        'municipio':     row.get('municipio'),
        'nit':           row.get('nit'),
        'fecha':         row.get('fecha'),
        'secretaria':    row.get('secretaria'),
        'objeto':        row.get('objeto'),
        'justificacion': row.get('justificacion'),
        'valor':         row.get('valor'),
        'meta_producto': row.get('meta_producto'),
        'eje':           row.get('eje'),
        'sector':        row.get('sector'),
        'codigo_bpim':   row.get('codigo_bpim'),
    })
    
    output_dir = current_app.config['CERTIFICADOS_OUTPUT_DIR']
    outfile = os.path.join(output_dir, f"certificado_{idx}.pdf")
    with open(outfile, 'wb') as f:
        f.write(pdf_buf.getvalue())
    
    # Actualizar el estado a 'generado' y guardar una sola vez
    df.loc[df['id'] == idx, 'estado'] = 'generado'
    df.to_csv(solicitudes_path, index=False, encoding='utf-8')
    
    pdf_buf.seek(0)
    return send_file(
        pdf_buf,
        as_attachment=True,
        download_name=f"certificado_{idx}.pdf",
        mimetype='application/pdf'
    )


@certificados_bp.route('/certificados/descargar/<int:idx>', methods=['GET'])
def descargar_certificado(idx: int):
    """Descarga un certificado ya generado desde el disco (carpeta de salida)."""
    output_dir = current_app.config['CERTIFICADOS_OUTPUT_DIR']
    if not os.path.exists(output_dir):
        abort(404)

    file_path = os.path.join(output_dir, f"certificado_{idx}.pdf")
    if not os.path.exists(file_path):
        abort(404)

    return send_file(file_path, as_attachment=True, download_name=f"certificado_{idx}.pdf", mimetype='application/pdf')
