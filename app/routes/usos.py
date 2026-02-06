import os
import re
import io
import json
import base64
import datetime
import unicodedata
import logging
import pandas as pd
from app.utils.rbac import require_permission
try:
    import geopandas as gpd
except ImportError:
    gpd = None

logger = logging.getLogger(__name__)

try:
    import qrcode
except ImportError:
    qrcode = None

# Usar ReportLab exclusivamente para PDF (consistencia con otros módulos)
try:
    from xhtml2pdf import pisa
except ImportError:
    pisa = None
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, current_app, jsonify, abort
try:
    from shapely.geometry import mapping
except ImportError:
    mapping = None

usos_bp = Blueprint('usos_suelo', __name__)

# --- Caches ---
_df_predios = None
_df_normas = None
_df_normatividad_excel = None
uso_lookup_cc = {}
uso_lookup_mat = {}
_geojson_cache = None  # Cache para GeoJSON estático

# --- Column mapping ---
COLMAP = {
    'cc': ['cedula_catastral', 'cc', 'cod_pred', 'codigo', 'codigo_predio', 'codigo_catastral'],
    'matricula': ['matricula', 'matricula_inmobiliaria', 'num_mat', 'num_matricula'],
    'uso': ['uso', 'uso_predio', 'uso_suelo', 'uso_actual', 'uso_destinado'],
    'direccion': ['direccion', 'dir', 'direccion_predio', 'ubicacion'],
    'barrio': ['barrio', 'sector', 'zona', 'localidad'],
    'norma': ['norma', 'normatividad', 'articulo', 'descripcion_norma']
}

# --- Helpers ---

def pick_col(df, keys):
    for k in keys:
        k = k.lower()
        if k in df.columns:
            return k
    return None

def norm_val(v):
    return re.sub(r'[^0-9A-Za-z]', '', str(v or '')).lower()

def cargar_df_predios():
    global _df_predios, uso_lookup_cc, uso_lookup_mat
    if _df_predios is None:
        path = os.path.join(current_app.config['DATA_DIR'], 'tabla_predios.xlsx')
        if not os.path.exists(path):
            logger.warning(f"No se encuentra tabla_predios.xlsx en {path}")
            return pd.DataFrame()
            
        try:
            df = pd.read_excel(path)
            df.columns = [c.strip().lower() for c in df.columns]
            
            # Populate lookups
            # Assuming COD_PRED and NUM_DOC keys exist or mapped
            col_cc = pick_col(df, COLMAP['cc'])
            col_mat = pick_col(df, COLMAP['matricula'])
            col_uso = pick_col(df, COLMAP['uso'])
            
            if col_cc and col_uso:
                df['cedula_catastral'] = df[col_cc].astype(str).str.strip()
                uso_lookup_cc = df.set_index('cedula_catastral')[col_uso].to_dict()
                
            if col_mat and col_uso:
                df['matricula'] = df[col_mat].astype(str).str.strip()
                uso_lookup_mat = df.set_index('matricula')[col_uso].to_dict()
                
            _df_predios = df
        except Exception as e:
            logger.error(f"Error cargando predios: {e}", exc_info=True)
            return pd.DataFrame()
            
    return _df_predios

def cargar_df_normas():
    global _df_normas
    if _df_normas is None:
        path = os.path.join(current_app.config['DATA_DIR'], 'normatividad.xlsx')
        if not os.path.exists(path):
             return pd.DataFrame(columns=['uso','articulo','descripcion'])
        try:
            df = pd.read_excel(path)
            df.columns = [c.strip().lower() for c in df.columns]
            _df_normas = df
        except:
             _df_normas = pd.DataFrame(columns=['uso','articulo','descripcion'])
    return _df_normas

def cargar_excel_normatividad():
    """Carga el Excel completo de normatividad con toda la información detallada"""
    global _df_normatividad_excel
    if _df_normatividad_excel is None:
        project_root = os.path.abspath(os.path.join(current_app.root_path, '..'))
        excel_path = os.path.join(project_root, 'documentos_generados', 'normatividad', 'plantilla_normatividad_usos.xlsx')
        
        if not os.path.exists(excel_path):
            logger.warning(f"Excel de normatividad no encontrado en: {excel_path}")
            return pd.DataFrame()
        
        try:
            df = pd.read_excel(excel_path)
            # Normalizar nombres de columnas
            df.columns = [str(c).strip() for c in df.columns]
            _df_normatividad_excel = df
            logger.info(f"Excel de normatividad cargado: {len(df)} registros")
        except Exception as e:
            logger.error(f"Error cargando Excel de normatividad: {e}", exc_info=True)
            return pd.DataFrame()
    
    return _df_normatividad_excel

def normalizar_uso(texto):
    """Normaliza texto para comparación de usos del suelo"""
    if not texto:
        return ""
    # Convertir a minúsculas y quitar tildes
    texto = str(texto).lower().strip()
    texto = ''.join(c for c in unicodedata.normalize('NFKD', texto) if not unicodedata.combining(c))
    # Quitar caracteres especiales excepto espacios
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    # Normalizar espacios múltiples
    texto = re.sub(r'\s+', ' ', texto)
    return texto

def buscar_normatividad_completa(uso_predio):
    """
    Busca normatividad completa para un uso del suelo dado.
    Retorna diccionario con toda la información relevante.
    """
    if not uso_predio:
        return None
    
    df_norm = cargar_excel_normatividad()
    if df_norm.empty:
        return None
    
    uso_normalizado = normalizar_uso(uso_predio)
    
    # Buscar por coincidencia en múltiples campos
    campos_busqueda = ['uso', 'alias', 'uso_oficial', 'categoria', 'subcategoria']
    
    for idx, row in df_norm.iterrows():
        for campo in campos_busqueda:
            if campo in df_norm.columns:
                valor = normalizar_uso(row.get(campo, ''))
                if valor and uso_normalizado in valor or valor in uso_normalizado:
                    # Encontramos una coincidencia
                    return {
                        'uso': row.get('uso', ''),
                        'categoria': row.get('categoria', ''),
                        'subcategoria': row.get('subcategoria', ''),
                        'descripcion': row.get('descripcion', ''),
                        'uso_principal': row.get('Uso Principal', ''),
                        'usos_compatibles': row.get('Usos Compatibles', ''),
                        'usos_condicionados': row.get('Usos Condicionados', ''),
                        'usos_prohibidos': row.get('Usos Prohibidos', ''),
                        'directrices': row.get('DIRECTRICES Y CONDICIONAMIENTOS', ''),
                        'conclusiones': row.get('CONCLUSIONES', ''),
                        'tipo_norma': row.get('tipo_norma', ''),
                        'num_norma': row.get('num_norma', ''),
                        'año': row.get('año', ''),
                        'norma_general': row.get('Norma General', ''),
                        'vigente': row.get('vigente', ''),
                        'fuente_url': row.get('fuente_url', '')
                    }
    
    return None

def buscar_predio(cc=None, matricula=None):
    df = cargar_df_predios()
    if df.empty: return None
    
    col_cc   = pick_col(df, COLMAP["cc"])
    col_mat  = pick_col(df, COLMAP["matricula"])

    fila = None
    if cc and col_cc:
        m = df[col_cc].astype(str).map(norm_val) == norm_val(cc)
        if m.any():
            fila = df[m].iloc[0].to_dict()

    if fila is None and matricula and col_mat:
        m = df[col_mat].astype(str).map(norm_val) == norm_val(matricula)
        if m.any():
            fila = df[m].iloc[0].to_dict()
    return fila

def buscar_norma(uso):
    if not uso:
        return "Normatividad específica no encontrada"
    df = cargar_df_normas()
    col_uso   = pick_col(df, COLMAP["uso"])    
    col_norma = pick_col(df, COLMAP["norma"])  
    if not col_uso or not col_norma:
        return "Normatividad específica no encontrada"
    mask = df[col_uso].astype(str).str.lower().str.strip() == uso.lower().strip()
    if mask.any():
        return df.loc[mask, col_norma].iloc[0]
    return "Normatividad específica no encontrada"

# --- Routes ---

@usos_bp.route("/usos_suelo", methods=["GET", "POST"], endpoint='index')
@require_permission('geoportal')
def usos_suelo():
    resultado = None
    if request.method == "POST":
        cc    = request.form.get("cc", "").strip()
        matri = request.form.get("matri", "").strip()
        fila = buscar_predio(cc=cc or None, matricula=matri or None)
        if fila:
            df = cargar_df_predios()
            col_uso = pick_col(df, COLMAP["uso"])
            col_dir = pick_col(df, COLMAP["direccion"])
            col_bar = pick_col(df, COLMAP["barrio"])
            col_cc  = pick_col(df, COLMAP["cc"])
            col_mat = pick_col(df, COLMAP["matricula"])
            
            # Safely get values
            uso = fila.get(col_uso, "") if col_uso else ""
            
            resultado = {
                "cedula":     fila.get(col_cc, "") if col_cc else "",
                "matricula":  fila.get(col_mat, "") if col_mat else "",
                "uso":        uso,
                "direccion":  fila.get(col_dir, "") if col_dir else "",
                "barrio":     fila.get(col_bar, "") if col_bar else "",
                "propietario": fila.get("nombre", ""),   # si existe
                "norma":      buscar_norma(uso)
            }
        else:
            flash("No se encontró información para los datos ingresados", "danger")

    return render_template("usos_suelo.html", resultado=resultado)

@usos_bp.route("/usos_suelo/generar/<cc>/<matri>")
def generar_pdf(cc, matri):
    """Genera certificado de uso del suelo en PDF usando xhtml2pdf (sin dependencias externas)"""
    # 1) Busco el predio
    fila_predio = buscar_predio(cc=cc, matricula=matri)
    if not fila_predio:
        abort(404, "No hay datos para ese predio")

    # 2) Cargo DataFrames
    dfp = cargar_df_predios()
    dfn = cargar_df_normas()

    # 3) Columnas dinámicas en predios
    col_cc   = pick_col(dfp, COLMAP["cc"])
    col_mat  = pick_col(dfp, COLMAP["matricula"])
    col_uso  = pick_col(dfp, COLMAP["uso"])
    col_dir  = pick_col(dfp, COLMAP["direccion"])
    col_bar  = pick_col(dfp, COLMAP["barrio"])

    # 4) Extraigo datos básicos
    uso = fila_predio.get(col_uso, "") if col_uso else ""
    datos = {
        "cc":         fila_predio.get(col_cc, "") if col_cc else "",
        "matricula":  fila_predio.get(col_mat, "") if col_mat else "",
        "direccion":  fila_predio.get(col_dir, "") if col_dir else "",
        "barrio":     fila_predio.get(col_bar, "") if col_bar else "",
        "uso":        uso,
        "municipio":  "Supatá (Cundinamarca)",
        "entidad":    "Alcaldía Municipal de Supatá"
    }

    # 5) Helpers para limpiar tokens
    def strip_accents(txt):
        return ''.join(c for c in unicodedata.normalize('NFKD', str(txt)) if not unicodedata.combining(c))
    def clean_token(txt):
        s = strip_accents(txt).lower()
        for pref in ("zona","área","area"):
            if s.startswith(pref):
                s = s[len(pref):]
        return re.sub(r'[^0-9a-z]', '', s)

    uso_token = clean_token(uso)

    # 6) Busco la norma correspondiente
    row_norma = None
    if not dfn.empty:
        for _, row in dfn.iterrows():
            for key in ("uso","alias","uso_oficial"):
                if key in dfn.columns and clean_token(row.get(key,"")) == uso_token:
                    row_norma = row
                    break
            if row_norma is not None:
                break

    # 7) Relleno campos de normatividad
    campos = {
        "norma_general":      "norma general",
        "descripcion":        "descripcion",
        "uso_principal":      "uso principal",
        "usos_compatibles":   "usos compatibles",
        "usos_condicionados": "usos condicionados",
        "usos_prohibidos":    "usos prohibidos",
        "directrices":        "directrices y condicionamientos",
        "conclusiones":       "conclusiones",
        "fuente_url":         "fuente_url",
        "vigente":            "vigente"
    }
    for k, col in campos.items():
        datos[k] = row_norma.get(col, "") if row_norma is not None else ""

    # 8) Genero el QR en memoria
    qr_data = "https://www.supata-cundinamarca.gov.co"
    if qrcode:
        qr_img  = qrcode.make(qr_data)
        buf     = io.BytesIO()
        qr_img.save(buf, format="PNG")
        qr_src  = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    else:
        qr_src = ""  # Sin QR si no está disponible

    # 9) Ruta al escudo
    logo_path = "file:///" + os.path.join(
        current_app.root_path, "static", "imagenes", "escudo.png"
    ).replace("\\", "/")

    # 10) Renderizo el HTML
    html = render_template(
        "uso_pdf.html",
        logo_path=logo_path,
        qr_src=qr_src,
        **datos
    )

    # 11) Genero el PDF con xhtml2pdf (sin dependencias externas como wkhtmltopdf)
    if pisa:
        try:
            pdf_buffer = io.BytesIO()
            pdf_status = pisa.CreatePDF(io.BytesIO(html.encode('utf-8')), dest=pdf_buffer)
            if not pdf_status.err:
                pdf_buffer.seek(0)
                filename = f"UsoSuelo_{datos['cc']}_{datos['matricula']}.pdf"
                return send_file(pdf_buffer, mimetype='application/pdf', 
                               as_attachment=True, download_name=filename)
            else:
                logger.error(f"Error generando PDF con xhtml2pdf: {pdf_status.err}")
                abort(500, "Error generando PDF")
        except Exception as e:
            logger.error(f"Excepción generando PDF: {e}", exc_info=True)
            abort(500, f"Error generando PDF: {str(e)}")
    else:
        abort(500, "xhtml2pdf no disponible. Instalar con: pip install xhtml2pdf")

@usos_bp.route('/usos_suelo/certificado/<cod_pred>')
def generar_certificado_cod_pred(cod_pred):
    """Atajo para generar certificado usando solo el código predial desde el visor 3D."""
    if not cod_pred:
        abort(400, "Código predial requerido")
    return generar_pdf(cc=cod_pred, matri="")

@usos_bp.route('/usos_suelo/geojson')
def usos_suelo_geojson():
    """Entrega el GeoJSON directamente con caché en memoria (optimizado para velocidad)."""
    global _geojson_cache
    
    # Retornar desde caché si ya está cargado
    if _geojson_cache is not None:
        return jsonify(_geojson_cache)
    
    # Intentar múltiples rutas posibles
    rutas_posibles = [
        os.path.join(current_app.root_path, 'static', 'geojson', 'usos_predial.geojson'),
        os.path.join(os.path.dirname(current_app.root_path), 'static', 'geojson', 'usos_predial.geojson'),
        'static/geojson/usos_predial.geojson',
        '/usos_predial.geojson'
    ]
    
    static_path = None
    for ruta in rutas_posibles:
        if os.path.exists(ruta):
            static_path = ruta
            logger.info(f"GeoJSON encontrado en: {ruta}")
            break
    
    if not static_path:
        logger.warning(f"No se encontró GeoJSON en: {rutas_posibles}")
        return jsonify({'type': 'FeatureCollection', 'features': [], 'error': 'Archivo no encontrado'})

    try:
        with open(static_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        _geojson_cache = data  # Guardar en caché
        logger.info(f"GeoJSON cargado y cacheado: {len(data.get('features', []))} features")
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error cargando GeoJSON: {e}", exc_info=True)
        return jsonify({'error': str(e), 'path': static_path}), 500

@usos_bp.route('/catastro_3d')
def catastro_3d():
    """Visor catastral profesional 3D con MapLibre GL."""
    return render_template('catastro_3d.html')

@usos_bp.route('/casco_urbano')
def mapa_casco_urbano():
    return render_template('mapa_casco.html')

@usos_bp.route('/usos_suelo/exportar_excel')
def exportar_usos_excel():
    df = cargar_df_predios()
    if df.empty:
        flash("No hay datos para exportar", "warning")
        return redirect(url_for('usos_suelo.index'))
    
    out = io.BytesIO()
    # Use ExcelWriter to write to buffer
    try:
        with pd.ExcelWriter(out, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Predios')
    except Exception as e:
        flash(f"Error generando Excel: {e}", "danger")
        return redirect(url_for('usos_suelo.index'))
        
    out.seek(0)
    return send_file(
        out,
        as_attachment=True,
        download_name=f"Reporte_Usos_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
@usos_bp.route('/usos_suelo/generar_pdf_croquis', methods=['POST'])
def generar_pdf_croquis():
    """Genera PDF con croquis del mapa y datos del predio"""
    try:
        data = request.get_json()
        cod_pred = data.get('cod_pred')
        map_screenshot = data.get('map_screenshot')
        predio_props = data.get('predio_props', {})
        
        if not cod_pred or not map_screenshot:
            return jsonify({'error': 'Faltan datos requeridos'}), 400
        
        # Decodificar imagen base64
        try:
            img_data = base64.b64decode(map_screenshot.split(',')[1])
        except:
            img_data = base64.b64decode(map_screenshot)
        
        # Generar PDF con xhtml2pdf (preferido) o reportlab (fallback)
        html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                    .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
                    .header {{ text-align: center; border-bottom: 3px solid #3b82f6; padding-bottom: 15px; margin-bottom: 20px; }}
                    .header h1 {{ margin: 0; color: #1f2937; font-size: 24px; }}
                    .header p {{ margin: 5px 0 0 0; color: #6b7280; }}
                    .section {{ margin-bottom: 20px; }}
                    .section-title {{ font-weight: bold; color: #1f2937; border-left: 4px solid #3b82f6; padding-left: 10px; margin-bottom: 10px; }}
                    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px; }}
                    .field {{ background: #f9fafb; padding: 10px; border-radius: 4px; border-left: 3px solid #06b6d4; }}
                    .field-label {{ font-size: 12px; font-weight: bold; color: #6b7280; text-transform: uppercase; margin-bottom: 3px; }}
                    .field-value {{ font-size: 14px; color: #1f2937; font-weight: 500; }}
                    .map-section {{ text-align: center; margin: 20px 0; page-break-inside: avoid; }}
                    .map-section img {{ max-width: 100%; height: auto; border: 2px solid #e5e7eb; border-radius: 6px; }}
                    .footer {{ text-align: center; margin-top: 30px; padding-top: 15px; border-top: 1px solid #e5e7eb; font-size: 11px; color: #9ca3af; }}
                    .footer p {{ margin: 5px 0; }}
                    .stamp {{ text-align: right; margin-top: 20px; font-size: 12px; color: #3b82f6; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📋 CERTIFICADO DE USO DEL SUELO</h1>
                        <p>Croquis y Detalles del Predio Catastral</p>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">📍 INFORMACIÓN DEL PREDIO</div>
                        <div class="grid">
                            <div class="field">
                                <div class="field-label">Código Catastral</div>
                                <div class="field-value">{predio_props.get('COD_PRED', 'N/A')}</div>
                            </div>
                            <div class="field">
                                <div class="field-label">Propietario</div>
                                <div class="field-value">{predio_props.get('PROPIETARIO', 'N/A')}</div>
                            </div>
                            <div class="field">
                                <div class="field-label">Área (ha)</div>
                                <div class="field-value">{predio_props.get('AREA_HA', 'N/A')}</div>
                            </div>
                            <div class="field">
                                <div class="field-label">Avalúo</div>
                                <div class="field-value>${predio_props.get('EVALÚO', 'N/A')}</div>
                            </div>
                            <div class="field">
                                <div class="field-label">Categoría</div>
                                <div class="field-value">{predio_props.get('Categoria', 'N/A')}</div>
                            </div>
                            <div class="field">
                                <div class="field-label">Subcategoría</div>
                                <div class="field-value">{predio_props.get('Subcategor', 'N/A')}</div>
                            </div>
                            <div class="field" style="grid-column: 1 / -1;">
                                <div class="field-label">Uso Específico</div>
                                <div class="field-value">{predio_props.get('Uso', 'N/A')}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">🗺️ CROQUIS DEL PREDIO</div>
                        <div class="map-section">
                            <img src="data:image/png;base64,{base64.b64encode(img_data).decode()}" alt="Croquis del mapa catastral"/>
                        </div>
                    </div>
                    
                    <div class="stamp">
                        <p><strong>Documento generado automáticamente</strong></p>
                        <p>Alcaldía Virtual - Catastro Municipal</p>
                    </div>
                    
                    <div class="footer">
                        <p>Este certificado contiene información del Sistema de Información Catastral Municipal</p>
                        <p>Generado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        # Intentar con xhtml2pdf primero
        if pisa:
            try:
                pdf_buffer = io.BytesIO()
                pdf_status = pisa.CreatePDF(io.BytesIO(html_content.encode('utf-8')), dest=pdf_buffer)
                if not pdf_status.err:
                    pdf_buffer.seek(0)
                    return send_file(
                        pdf_buffer,
                        mimetype='application/pdf',
                        as_attachment=True,
                        download_name=f'Croquis_{cod_pred}.pdf'
                    )
                else:
                    logger.warning(f"xhtml2pdf reportó error: {pdf_status.err}")
            except Exception as e:
                logger.debug(f"xhtml2pdf no disponible: {e}")
        
        # Fallback: Crear PDF simple con reportlab
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.units import inch
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import ImageReader
            from io import BytesIO
            
            pdf_buffer = BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=letter)
            width, height = letter
            
            # Título
            c.setFont("Helvetica-Bold", 20)
            c.drawString(inch * 0.5, height - inch * 0.5, "CERTIFICADO DE USO DEL SUELO")
            
            # Detalles
            c.setFont("Helvetica", 10)
            y_pos = height - inch * 1.2
            
            details = [
                f"Código Catastral: {predio_props.get('COD_PRED', 'N/A')}",
                f"Propietario: {predio_props.get('PROPIETARIO', 'N/A')}",
                f"Área (ha): {predio_props.get('AREA_HA', 'N/A')}",
                f"Uso del Suelo: {predio_props.get('Uso', 'N/A')}",
                f"Categoría: {predio_props.get('Categoria', 'N/A')}",
            ]
            
            for detail in details:
                c.drawString(inch * 0.5, y_pos, detail)
                y_pos -= inch * 0.3
            
            # Imagen del mapa
            try:
                img = ImageReader(io.BytesIO(img_data))
                c.drawImage(img, inch * 0.5, height * 0.3 - inch, width=inch * 7, height=inch * 3.5)
            except Exception as e:
                c.drawString(inch * 0.5, height * 0.3, f"[No se pudo cargar la imagen del mapa: {e}]")
            
            # Pie
            c.setFont("Helvetica", 8)
            c.drawString(inch * 0.5, inch * 0.3, f"Generado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            
            c.save()
            pdf_buffer.seek(0)
            
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'Croquis_{cod_pred}.pdf'
            )
        except Exception as e2:
            logger.error(f"Error con reportlab: {e2}", exc_info=True)
            return jsonify({'error': f'No se pudo generar PDF: {str(e2)}'}), 500
            
    except Exception as e:
        logger.error(f"Error generando PDF croquis: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@usos_bp.route('/usos_suelo/generar_certificado_completo', methods=['POST'])
def generar_certificado_completo():
    """Genera un PDF combinado: Formato oficial + uso del suelo + croquis del predio seleccionado."""
    try:
        data = request.get_json() or {}
        cod_pred = data.get('cod_pred')
        uso_actual = data.get('uso')
        predio_props = data.get('predio_props', {})
        map_screenshot = data.get('map_screenshot')
        if not cod_pred or not map_screenshot:
            return jsonify({'error': 'Faltan datos requeridos'}), 400

        # Buscar normatividad completa desde el Excel
        uso_buscado = uso_actual or predio_props.get('Uso') or predio_props.get('Subcategor') or predio_props.get('Categoria') or ''
        normatividad = buscar_normatividad_completa(uso_buscado)
        
        logger.debug(f"Buscando normatividad para: {uso_buscado}")
        if normatividad:
            logger.info(f"Encontrada normatividad: {normatividad.get('uso', 'N/A')}")
        else:
            logger.warning(f"No se encontró normatividad para: {uso_buscado}")
        
        # Cargar texto de normatividad desde archivos (fallback)
        def slug(s):
            s = ''.join(c for c in unicodedata.normalize('NFKD', str(s or '')) if not unicodedata.combining(c))
            return re.sub(r'[^0-9a-z]+', '_', s.lower()).strip('_')
        def cargar_norma_html(uso_val):
            # Prioridad: documentos_generados/normatividad at project root
            project_root = os.path.abspath(os.path.join(current_app.root_path, '..'))
            docs_dir = os.path.join(project_root, 'documentos_generados', 'normatividad')
            tpl_dir = os.path.join(current_app.root_path, 'templates', 'normatividad')
            candidate_dirs = []
            if os.path.isdir(docs_dir):
                candidate_dirs.append(docs_dir)
            if os.path.isdir(tpl_dir):
                candidate_dirs.append(tpl_dir)

            use_slug = slug(uso_val)
            for base_dir in candidate_dirs:
                try:
                    files = os.listdir(base_dir)
                except Exception:
                    continue

                # Buscar HTML directo primero
                for f in files:
                    try:
                        fs = slug(os.path.splitext(f)[0])
                    except Exception:
                        fs = ''
                    if use_slug in fs and f.lower().endswith('.html'):
                        try:
                            with open(os.path.join(base_dir, f), 'r', encoding='utf-8') as fh:
                                return fh.read()
                        except Exception:
                            continue

                # Buscar DOCX y convertir a HTML sencillo
                for f in files:
                    if not f.lower().endswith('.docx'):
                        continue
                    try:
                        fs = slug(os.path.splitext(f)[0])
                    except Exception:
                        fs = ''
                    if use_slug in fs:
                        fullpath = os.path.join(base_dir, f)
                        try:
                            try:
                                import docx
                                doc = docx.Document(fullpath)
                                paras = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
                                return '\n'.join(f'<p>{t}</p>' for t in paras)
                            except Exception:
                                # Fallback: extract raw text from DOCX XML
                                import zipfile
                                import xml.etree.ElementTree as ET
                                z = zipfile.ZipFile(fullpath)
                                xml = z.read('word/document.xml')
                                root = ET.fromstring(xml)
                                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                                texts = []
                                for p in root.findall('.//w:p', ns):
                                    t = ''.join([node.text or '' for node in p.findall('.//w:t', ns)])
                                    if t and t.strip():
                                        texts.append(t)
                                return '\n'.join(f'<p>{t}</p>' for t in texts)
                        except Exception:
                            continue

            return '<p>No se encontró normatividad específica para este uso.</p>'

        # Decodificar screenshot
        try:
            img_bytes = base64.b64decode(map_screenshot.split(',')[1])
        except Exception:
            img_bytes = base64.b64decode(map_screenshot)

        # Recursos
        escudo_path = 'file:///' + os.path.join(current_app.root_path, 'static', 'imagenes', 'escudo.png').replace('\\', '/')
        fecha_gen = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        # HTML del certificado usando el nuevo template mejorado
        html_cert = render_template('certificado_completo_v2.html',
                                    escudo_path=escudo_path,
                                    fecha_gen=fecha_gen,
                                    cod_pred=cod_pred,
                                    props=predio_props,
                                    uso_actual=uso_buscado,
                                    normatividad=normatividad,
                                    croquis_data='data:image/png;base64,' + base64.b64encode(img_bytes).decode('ascii'))

        # Generar PDF principal usando xhtml2pdf
        pdf_main_bytes = None
        if pisa:
            try:
                result_buffer = io.BytesIO()
                pdf_status = pisa.CreatePDF(io.BytesIO(html_cert.encode('utf-8')), dest=result_buffer)
                if not pdf_status.err:
                    pdf_main_bytes = result_buffer.getvalue()
                    logger.info("PDF generado con xhtml2pdf correctamente")
                else:
                    logger.error(f"Error generando PDF con xhtml2pdf: {pdf_status.err}")
            except Exception as e:
                logger.error(f"Excepción en xhtml2pdf: {e}", exc_info=True)
        
        if pdf_main_bytes is None:
            # Fallback simple con reportlab
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import inch
            from reportlab.lib.utils import ImageReader
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=letter)
            w, h = letter
            c.setFont('Helvetica-Bold', 16)
            c.drawString(inch*0.5, h - inch*0.7, 'CERTIFICADO DE USO DEL SUELO + CROQUIS')
            y = h - inch*1.1
            c.setFont('Helvetica', 10)
            c.drawString(inch*0.5, y, f'Código: {cod_pred}')
            y -= 14
            c.drawString(inch*0.5, y, f'Propietario: {predio_props.get("PROPIETARIO","N/A")}')
            y -= 14
            uso = uso_actual or predio_props.get('Uso') or predio_props.get('Subcategor') or predio_props.get('Categoria') or None
            c.drawString(inch*0.5, y, f'Uso: {predio_props.get("Uso") or uso or "N/A"}')
            y -= 18
            try:
                img = ImageReader(io.BytesIO(img_bytes))
                c.drawImage(img, inch*0.5, h*0.25, width=inch*7, height=inch*3.5)
            except Exception:
                c.drawString(inch*0.5, h*0.25, '[Croquis no disponible]')
            c.showPage()
            c.save()
            buf.seek(0)
            pdf_main_bytes = buf.getvalue()

        # Si existe FORMATO.pdf, intentar combinar (prepend)
        combined_bytes = pdf_main_bytes
        try:
            from PyPDF2 import PdfReader, PdfWriter
            formato_path = os.path.join(current_app.root_path, 'datos', 'FORMATO.pdf')
            if os.path.exists(formato_path):
                writer = PdfWriter()
                reader_form = PdfReader(formato_path)
                # Primero el formato oficial
                for p in reader_form.pages:
                    writer.add_page(p)
                # Luego nuestro certificado
                reader_main = PdfReader(io.BytesIO(pdf_main_bytes))
                for p in reader_main.pages:
                    writer.add_page(p)
                out_buf = io.BytesIO()
                writer.write(out_buf)
                out_buf.seek(0)
                combined_bytes = out_buf.getvalue()
        except Exception as e:
            logger.warning(f"Combinar con FORMATO.pdf falló: {e}")

        return send_file(io.BytesIO(combined_bytes), mimetype='application/pdf', as_attachment=True,
                         download_name=f'Certificado_{cod_pred}.pdf')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Endpoint de prueba para verificar búsqueda de normatividad
@usos_bp.route('/usos_suelo/test_normatividad/<uso>')
def test_normatividad(uso):
    """Endpoint de prueba para verificar la búsqueda de normatividad"""
    try:
        normatividad = buscar_normatividad_completa(uso)
        if normatividad:
            return jsonify({
                'success': True,
                'uso_buscado': uso,
                'normatividad_encontrada': normatividad
            })
        else:
            return jsonify({
                'success': False,
                'uso_buscado': uso,
                'mensaje': 'No se encontró normatividad para este uso'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500