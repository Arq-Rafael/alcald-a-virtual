"""
Generador de PDFs para Gestión Arbórea
Genera PDFs de permisos, informes y reportes consolidados
"""
from io import BytesIO
import os
from datetime import datetime
from jinja2 import Template
import json

try:
    from weasyprint import WeasyPrint, HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

class PDFGenerador:
    """Genera PDFs profesionales para gestión arbórea"""
    
    # Rutas base
    BASE_PATH = r'c:\Users\rafa_\Downloads\AlcaldiaVirtualWeb\documentos_generados\gestion_riesgo\gestion_arborea'
    TEMPLATE_PATH = os.path.join(BASE_PATH, 'templates')
    
    @staticmethod
    def crear_directorio():
        """Asegura que existen los directorios necesarios"""
        os.makedirs(PDFGenerador.BASE_PATH, exist_ok=True)
        os.makedirs(PDFGenerador.TEMPLATE_PATH, exist_ok=True)
    
    @staticmethod
    def generar_permiso_pdf(radicado):
        """
        Genera PDF del permiso de intervención arbórea
        Incluye: número de radicado, árbol, solicitante, decisión, vigencia
        """
        if not WEASYPRINT_AVAILABLE:
            return None
        
        PDFGenerador.crear_directorio()
        
        # HTML para el permiso
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .page {{
                    width: 210mm;
                    height: 297mm;
                    padding: 20mm;
                    margin: 0 auto;
                    background: white;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    border-bottom: 3px solid #2d5016;
                    padding-bottom: 15px;
                    margin-bottom: 20px;
                }}
                .header h1 {{
                    font-size: 18px;
                    color: #2d5016;
                    margin-bottom: 5px;
                }}
                .header p {{
                    font-size: 12px;
                    color: #666;
                }}
                .radicado-info {{
                    background: #f5f5f5;
                    padding: 10px 15px;
                    border-radius: 4px;
                    margin-bottom: 20px;
                    font-size: 11px;
                }}
                .radicado-info strong {{
                    color: #2d5016;
                }}
                .section {{
                    margin-bottom: 15px;
                    page-break-inside: avoid;
                }}
                .section h2 {{
                    font-size: 13px;
                    color: #2d5016;
                    border-left: 4px solid #7cb342;
                    padding-left: 10px;
                    margin-bottom: 10px;
                    text-transform: uppercase;
                }}
                .section p {{
                    font-size: 11px;
                    margin-bottom: 5px;
                }}
                .row {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                    margin-bottom: 10px;
                }}
                .row.full {{
                    grid-template-columns: 1fr;
                }}
                .field {{
                    font-size: 11px;
                }}
                .field label {{
                    font-weight: bold;
                    color: #2d5016;
                    display: block;
                    margin-bottom: 3px;
                }}
                .field value {{
                    padding: 5px;
                    background: #fff9f5;
                    border-left: 2px solid #7cb342;
                    padding-left: 8px;
                }}
                .decision {{
                    background: #e8f5e9;
                    border: 2px solid #7cb342;
                    border-radius: 4px;
                    padding: 15px;
                    margin: 15px 0;
                    text-align: center;
                }}
                .decision.aprobado {{
                    background: #e8f5e9;
                    border-color: #7cb342;
                }}
                .decision.negado {{
                    background: #ffebee;
                    border-color: #d32f2f;
                }}
                .decision h3 {{
                    font-size: 14px;
                    margin-bottom: 5px;
                }}
                .footer {{
                    border-top: 1px solid #ddd;
                    padding-top: 15px;
                    margin-top: 30px;
                    font-size: 10px;
                    text-align: center;
                    color: #999;
                }}
                .firma-line {{
                    border-top: 1px solid #000;
                    width: 40%;
                    margin: 30px auto 5px;
                    text-align: center;
                    font-size: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="page">
                <div class="header">
                    <h1>PERMISO DE INTERVENCIÓN ARBÓREA</h1>
                    <p>Alcaldía Municipal - Gestión del Riesgo</p>
                </div>
                
                <div class="radicado-info">
                    <strong>Radicado:</strong> {radicado.numero_radicado} | 
                    <strong>Fecha:</strong> {radicado.permiso_fecha_emision.strftime('%d/%m/%Y') if radicado.permiso_fecha_emision else 'N/A'} | 
                    <strong>Estado:</strong> {radicado.estado}
                </div>
                
                <div class="section">
                    <h2>Solicitante</h2>
                    <div class="row">
                        <div class="field">
                            <label>Nombre</label>
                            <value>{radicado.solicitante_nombre or 'No especificado'}</value>
                        </div>
                        <div class="field">
                            <label>Cédula</label>
                            <value>{radicado.solicitante_documento or 'N/A'}</value>
                        </div>
                    </div>
                    <div class="row">
                        <div class="field">
                            <label>Contacto</label>
                            <value>{radicado.solicitante_contacto or 'N/A'}</value>
                        </div>
                        <div class="field">
                            <label>Correo</label>
                            <value>{radicado.solicitante_correo or 'N/A'}</value>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>Árbol a Intervenir</h2>
                    <div class="row">
                        <div class="field">
                            <label>Especie (Común)</label>
                            <value>{radicado.arbol_especie_comun or 'No especificada'}</value>
                        </div>
                        <div class="field">
                            <label>Especie (Científica)</label>
                            <value>{radicado.arbol_especie_cientifico or 'N/A'}</value>
                        </div>
                    </div>
                    <div class="row">
                        <div class="field">
                            <label>DAP (cm)</label>
                            <value>{radicado.arbol_dap_cm or 'N/A'}</value>
                        </div>
                        <div class="field">
                            <label>Altura (m)</label>
                            <value>{radicado.arbol_altura_m or 'N/A'}</value>
                        </div>
                    </div>
                    <div class="row">
                        <div class="field">
                            <label>Riesgo Identificado</label>
                            <value>{radicado.arbol_riesgo_inicial or 'No evaluado'}</value>
                        </div>
                        <div class="field">
                            <label>Tipo de Solicitud</label>
                            <value>{radicado.tipo_solicitud or 'N/A'}</value>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="decision {'aprobado' if radicado.dictamen_decision == 'Aprobado' else 'negado'}">
                        <h3>DECISIÓN: {radicado.dictamen_decision or 'Pendiente'}</h3>
                        <p>{radicado.dictamen_motivo_negacion if radicado.dictamen_decision == 'Negado' else 'Permiso otorgado para la intervención solicitada'}</p>
                    </div>
                </div>
                
                {"<div class='section'><h2>Vigencia del Permiso</h2><div class='row'><div class='field'><label>Vigencia</label><value>" + str(radicado.permiso_vigencia_dias) + " días</value></div><div class='field'><label>Fecha Límite</label><value>" + (radicado.permiso_fecha_limite.strftime('%d/%m/%Y') if radicado.permiso_fecha_limite else 'N/A') + "</value></div></div></div>" if radicado.dictamen_decision == "Aprobado" else ""}
                
                {"<div class='section'><h2>Obligaciones</h2><p>" + (radicado.permiso_obligaciones or 'Cumplir con la normativa ambiental vigente.') + "</p></div>" if radicado.permiso_obligaciones else ""}
                
                <div class="footer">
                    <p>Documento generado automáticamente por el Sistema de Gestión del Riesgo</p>
                    <p>Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            # Generar PDF
            pdf = HTML(string=html_content).write_pdf()
            
            # Guardar archivo
            filename = f"{radicado.numero_radicado}_permiso_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(PDFGenerador.BASE_PATH, filename)
            
            with open(filepath, 'wb') as f:
                f.write(pdf)
            
            return filepath, filename
        except Exception as e:
            print(f"Error generando PDF: {e}")
            return None, None
    
    @staticmethod
    def generar_informe_compensacion_pdf(radicado):
        """
        Genera PDF del informe de compensación
        Incluye: cálculo automático, especie recomendada, plan de compensación
        """
        if not WEASYPRINT_AVAILABLE:
            return None
        
        PDFGenerador.crear_directorio()
        
        # Parsear JSON del cálculo
        calculo = json.loads(radicado.compensacion_calculo_json) if radicado.compensacion_calculo_json else {}
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .page {{
                    width: 210mm;
                    height: 297mm;
                    padding: 20mm;
                    margin: 0 auto;
                    background: white;
                }}
                .header {{
                    text-align: center;
                    border-bottom: 3px solid #1976d2;
                    padding-bottom: 15px;
                    margin-bottom: 20px;
                }}
                .header h1 {{
                    font-size: 18px;
                    color: #1976d2;
                    margin-bottom: 5px;
                }}
                .section {{
                    margin-bottom: 20px;
                }}
                .section h2 {{
                    font-size: 13px;
                    color: #1976d2;
                    border-left: 4px solid #42a5f5;
                    padding-left: 10px;
                    margin-bottom: 10px;
                    text-transform: uppercase;
                }}
                .calculo-box {{
                    background: #e3f2fd;
                    border: 2px solid #1976d2;
                    border-radius: 4px;
                    padding: 15px;
                    margin: 15px 0;
                    text-align: center;
                }}
                .calculo-box h3 {{
                    font-size: 14px;
                    color: #1976d2;
                    margin-bottom: 10px;
                }}
                .formula {{
                    font-family: 'Courier New', monospace;
                    font-size: 12px;
                    background: #fff;
                    padding: 10px;
                    border-radius: 3px;
                    margin: 10px 0;
                    border-left: 3px solid #42a5f5;
                }}
                .resultado {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #1976d2;
                    margin: 10px 0;
                }}
                .detalles {{
                    font-size: 11px;
                    color: #666;
                    line-height: 1.8;
                }}
                .field {{
                    font-size: 11px;
                    margin-bottom: 8px;
                    padding: 8px;
                    background: #f9f9f9;
                    border-left: 3px solid #42a5f5;
                    padding-left: 10px;
                }}
                .field strong {{
                    color: #1976d2;
                    display: inline-block;
                    width: 150px;
                }}
                .footer {{
                    border-top: 1px solid #ddd;
                    padding-top: 15px;
                    margin-top: 30px;
                    font-size: 10px;
                    text-align: center;
                    color: #999;
                }}
            </style>
        </head>
        <body>
            <div class="page">
                <div class="header">
                    <h1>INFORME DE COMPENSACIÓN</h1>
                    <p>Plántulas a Reforestar - Gestión Arbórea</p>
                </div>
                
                <div class="radicado-info" style="background: #f5f5f5; padding: 10px 15px; border-radius: 4px; margin-bottom: 20px; font-size: 11px;">
                    <strong>Radicado:</strong> {radicado.numero_radicado} | 
                    <strong>Solicitante:</strong> {radicado.solicitante_nombre or 'N/A'} | 
                    <strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y')}
                </div>
                
                <div class="section">
                    <h2>Cálculo de Compensación</h2>
                    <div class="calculo-box">
                        <h3>Número de Árboles a Plantar</h3>
                        <div class="formula">
                            Fórmula: ceil((DAP ÷ 10) × Coeficiente)
                        </div>
                        <div class="detalles">
                            DAP: {calculo.get('dap_cm', radicado.arbol_dap_cm) or 'N/A'} cm <br>
                            Coeficiente: {calculo.get('coeficiente', radicado.compensacion_coeficiente) or 'N/A'} <br>
                            Cálculo: ({calculo.get('dap_cm', 0)} ÷ 10) × {calculo.get('coeficiente', 1)} = {calculo.get('resultado', radicado.compensacion_arboles_plantar) or 'N/A'}
                        </div>
                        <div class="resultado">
                            {radicado.compensacion_arboles_plantar or 'Pendiente'} ÁRBOLES
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>Especie Recomendada</h2>
                    <div class="field">
                        <strong>Especie:</strong> {radicado.compensacion_especie_recomendada or 'A definir según contexto'}
                    </div>
                </div>
                
                <div class="section">
                    <h2>Plan de Reforestación</h2>
                    <div class="field">
                        <strong>Sitio:</strong> {radicado.compensacion_sitio or 'Por definir'}
                    </div>
                    <div class="field">
                        <strong>Plazo:</strong> {radicado.compensacion_plazo or 'Según normativa'}
                    </div>
                </div>
                
                <div class="footer">
                    <p>Documento generado automáticamente - {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            pdf = HTML(string=html_content).write_pdf()
            
            filename = f"{radicado.numero_radicado}_compensacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(PDFGenerador.BASE_PATH, filename)
            
            with open(filepath, 'wb') as f:
                f.write(pdf)
            
            return filepath, filename
        except Exception as e:
            print(f"Error generando PDF: {e}")
            return None, None
    
    @staticmethod
    def generar_pdf_consolidado(radicado, incluir_permiso=True, incluir_informe=True):
        """
        Genera un PDF consolidado con permiso + informe de compensación
        """
        if not WEASYPRINT_AVAILABLE:
            return None
        
        PDFGenerador.crear_directorio()
        
        # Parsear JSON
        calculo = json.loads(radicado.compensacion_calculo_json) if radicado.compensacion_calculo_json else {}
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .page {{
                    width: 210mm;
                    height: 297mm;
                    padding: 20mm;
                    margin: 0 auto;
                    background: white;
                    page-break-after: always;
                }}
                .page:last-child {{
                    page-break-after: avoid;
                }}
                .header {{
                    text-align: center;
                    border-bottom: 3px solid #2d5016;
                    padding-bottom: 15px;
                    margin-bottom: 20px;
                }}
                .header h1 {{
                    font-size: 18px;
                    color: #2d5016;
                    margin-bottom: 5px;
                }}
                .section {{
                    margin-bottom: 15px;
                }}
                .section h2 {{
                    font-size: 13px;
                    color: #2d5016;
                    border-left: 4px solid #7cb342;
                    padding-left: 10px;
                    margin-bottom: 10px;
                    text-transform: uppercase;
                }}
                .info-box {{
                    background: #f5f5f5;
                    padding: 10px 15px;
                    border-radius: 4px;
                    margin-bottom: 15px;
                    font-size: 11px;
                }}
                .field {{
                    font-size: 11px;
                    margin-bottom: 8px;
                    padding: 8px;
                    background: #f9f9f9;
                    border-left: 3px solid #7cb342;
                    padding-left: 10px;
                }}
                .field strong {{
                    color: #2d5016;
                    display: inline-block;
                    width: 130px;
                }}
                .decision {{
                    background: #e8f5e9;
                    border: 2px solid #7cb342;
                    border-radius: 4px;
                    padding: 15px;
                    margin: 15px 0;
                    text-align: center;
                }}
                .calculo-box {{
                    background: #e8f5e9;
                    border: 2px solid #7cb342;
                    border-radius: 4px;
                    padding: 15px;
                    margin: 15px 0;
                    text-align: center;
                }}
                .formula {{
                    font-family: 'Courier New', monospace;
                    font-size: 11px;
                    background: #fff;
                    padding: 8px;
                    border-radius: 3px;
                    margin: 8px 0;
                    border-left: 3px solid #7cb342;
                }}
                .resultado {{
                    font-size: 20px;
                    font-weight: bold;
                    color: #2d5016;
                    margin: 10px 0;
                }}
                .footer {{
                    border-top: 1px solid #ddd;
                    padding-top: 10px;
                    margin-top: 20px;
                    font-size: 10px;
                    text-align: center;
                    color: #999;
                }}
                .page-break {{
                    page-break-after: always;
                }}
            </style>
        </head>
        <body>
            <!-- PÁGINA 1: PERMISO -->
            <div class="page">
                <div class="header">
                    <h1>PERMISO DE INTERVENCIÓN ARBÓREA</h1>
                    <p>Alcaldía Municipal - Gestión del Riesgo</p>
                </div>
                
                <div class="info-box">
                    <strong>Radicado:</strong> {radicado.numero_radicado} | 
                    <strong>Fecha:</strong> {radicado.permiso_fecha_emision.strftime('%d/%m/%Y') if radicado.permiso_fecha_emision else 'N/A'} | 
                    <strong>Estado:</strong> {radicado.estado}
                </div>
                
                <div class="section">
                    <h2>Solicitante</h2>
                    <div class="field">
                        <strong>Nombre:</strong> {radicado.solicitante_nombre or 'No especificado'}
                    </div>
                    <div class="field">
                        <strong>Cédula:</strong> {radicado.solicitante_documento or 'N/A'}
                    </div>
                    <div class="field">
                        <strong>Contacto:</strong> {radicado.solicitante_contacto or 'N/A'}
                    </div>
                </div>
                
                <div class="section">
                    <h2>Árbol a Intervenir</h2>
                    <div class="field">
                        <strong>Especie (Común):</strong> {radicado.arbol_especie_comun or 'No especificada'}
                    </div>
                    <div class="field">
                        <strong>Especie (Científica):</strong> {radicado.arbol_especie_cientifico or 'N/A'}
                    </div>
                    <div class="field">
                        <strong>DAP:</strong> {radicado.arbol_dap_cm or 'N/A'} cm
                    </div>
                    <div class="field">
                        <strong>Altura:</strong> {radicado.arbol_altura_m or 'N/A'} m
                    </div>
                    <div class="field">
                        <strong>Tipo de Solicitud:</strong> {radicado.tipo_solicitud or 'N/A'}
                    </div>
                </div>
                
                <div class="decision">
                    <h3>DECISIÓN: {radicado.dictamen_decision or 'Pendiente'}</h3>
                    <p>{radicado.dictamen_motivo_negacion if radicado.dictamen_decision == 'Negado' else 'Permiso otorgado'}</p>
                </div>
                
                {"<div class='section'><h2>Vigencia</h2><div class='field'><strong>Válido por:</strong> " + str(radicado.permiso_vigencia_dias) + " días</div><div class='field'><strong>Hasta:</strong> " + (radicado.permiso_fecha_limite.strftime('%d/%m/%Y') if radicado.permiso_fecha_limite else 'N/A') + "</div></div>" if radicado.dictamen_decision == 'Aprobado' else ""}
                
                <div class="footer">
                    <p>Documento generado automáticamente - {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>
            
            <!-- PÁGINA 2: COMPENSACIÓN -->
            <div class="page">
                <div class="header">
                    <h1>INFORME DE COMPENSACIÓN</h1>
                    <p>Plántulas a Reforestar</p>
                </div>
                
                <div class="info-box">
                    <strong>Radicado:</strong> {radicado.numero_radicado} | 
                    <strong>Solicitante:</strong> {radicado.solicitante_nombre or 'N/A'}
                </div>
                
                <div class="section">
                    <h2>Cálculo de Compensación</h2>
                    <div class="calculo-box">
                        <h3>Número de Árboles a Plantar</h3>
                        <div class="formula">
                            ceil((DAP ÷ 10) × Coeficiente)
                        </div>
                        <div style="font-size: 11px; margin: 10px 0;">
                            ({calculo.get('dap_cm', radicado.arbol_dap_cm) or 'N/A'} ÷ 10) × {calculo.get('coeficiente', radicado.compensacion_coeficiente) or 'N/A'} = {calculo.get('resultado', radicado.compensacion_arboles_plantar) or 'N/A'}
                        </div>
                        <div class="resultado">
                            {radicado.compensacion_arboles_plantar or 'Pendiente'}
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>Plan de Reforestación</h2>
                    <div class="field">
                        <strong>Especie:</strong> {radicado.compensacion_especie_recomendada or 'A definir'}
                    </div>
                    <div class="field">
                        <strong>Sitio:</strong> {radicado.compensacion_sitio or 'Por definir'}
                    </div>
                    <div class="field">
                        <strong>Plazo:</strong> {radicado.compensacion_plazo or 'Según normativa'}
                    </div>
                </div>
                
                <div class="footer">
                    <p>Documento consolidado generado automáticamente - {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            pdf = HTML(string=html_content).write_pdf()
            
            filename = f"{radicado.numero_radicado}_consolidado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(PDFGenerador.BASE_PATH, filename)
            
            with open(filepath, 'wb') as f:
                f.write(pdf)
            
            return filepath, filename
        except Exception as e:
            print(f"Error generando PDF consolidado: {e}")
            return None, None
