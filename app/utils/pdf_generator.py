"""
Generador mejorado de PDF para Planes de Contingencia
Usa ReportLab Platypus para evitar superposiciones de texto
"""
import json
import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Image as RLImage, KeepTogether, PageTemplate, Frame
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas

class PDFPlanContingencia:
    """Generador de PDF para Planes de Contingencia"""
    
    def __init__(self, plan, current_app):
        self.plan = plan
        self.current_app = current_app
        self.w, self.h = letter
        self.margin = 0.75 * inch
        self.styles = getSampleStyleSheet()
        self._crear_estilos_personalizados()
    
    def _crear_estilos_personalizados(self):
        """Crea estilos personalizados para el PDF"""
        self.styles.add(ParagraphStyle(
            name='TituloSecciones',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2d5016'),
            spaceAfter=12,
            fontName='Helvetica-Bold',
            borderColor=colors.HexColor('#7cb342'),
            borderWidth=2,
            borderPadding=10,
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubtituloSecciones',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#5a8a3a'),
            spaceAfter=8,
            fontName='Helvetica-Bold',
        ))
        
        self.styles.add(ParagraphStyle(
            name='Cuerpo',
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            alignment=TA_JUSTIFY,
            spaceAfter=10,
            leading=14,
        ))
        
        self.styles.add(ParagraphStyle(
            name='Etiqueta',
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            fontName='Helvetica-Bold',
            spaceAfter=4,
        ))
    
    def generar(self):
        """Genera el PDF completo y retorna el buffer"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin,
                title=f"Plan de Contingencia {self.plan.numero_plan}",
                author=self.plan.responsable_principal,
            )
            
            # Construir contenido
            elementos = []
            
            # 1. PORTADA
            elementos.extend(self._crear_portada())
            elementos.append(PageBreak())
            
            # 2. TABLA DE CONTENIDOS
            elementos.extend(self._crear_tabla_contenidos())
            elementos.append(PageBreak())
            
            # 3. INFORMACIÓN GENERAL
            elementos.extend(self._crear_seccion_general())
            elementos.append(PageBreak())
            
            # 4. ESCENARIO Y RIESGO
            elementos.extend(self._crear_escenario_riesgo())
            elementos.append(PageBreak())
            
            # 5. ALERTAS
            elementos.extend(self._crear_alertas())
            elementos.append(PageBreak())
            
            # 6. ESTRUCTURA ORGANIZATIVA
            elementos.extend(self._crear_estructura_organizativa())
            elementos.append(PageBreak())
            
            # 7. FASES DE RESPUESTA
            elementos.extend(self._crear_fases_respuesta())
            elementos.append(PageBreak())
            
            # 8. LOGÍSTICA
            elementos.extend(self._crear_logistica())
            elementos.append(PageBreak())
            
            # 9. ALBERGUES
            elementos.extend(self._crear_albergues())
            elementos.append(PageBreak())
            
            # 10. COMUNICACIONES
            elementos.extend(self._crear_comunicaciones())
            elementos.append(PageBreak())
            
            # 11. SALUD
            elementos.extend(self._crear_salud())
            elementos.append(PageBreak())
            
            # 12. PRESUPUESTO
            elementos.extend(self._crear_presupuesto())
            elementos.append(PageBreak())
            
            # 13. AUTORIZACIONES
            elementos.extend(self._crear_autorizaciones())
            
            # Construir PDF
            doc.build(elementos)
            buffer.seek(0)
            print(f'✓ PDF generado exitosamente: {len(buffer.getvalue())} bytes')
            return buffer
            
        except Exception as e:
            print(f'✗ Error generando PDF: {e}')
            import traceback
            traceback.print_exc()
            return None
    
    def _crear_portada(self):
        """Crea la portada del plan"""
        elementos = []
        
        # Encabezado institucional
        elementos.append(Spacer(1, 0.3*inch))
        
        titulo = Paragraph(
            "PLAN DE CONTINGENCIA",
            ParagraphStyle(
                'PortadaTitulo',
                fontSize=28,
                textColor=colors.HexColor('#2d5016'),
                alignment=TA_CENTER,
                fontName='Helvetica-Bold',
                spaceAfter=12,
            )
        )
        elementos.append(titulo)
        
        subtitulo = Paragraph(
            f"Para {self.plan.tipo_evento.replace('_', ' ').title()}",
            ParagraphStyle(
                'PortadaSubtitulo',
                fontSize=18,
                textColor=colors.HexColor('#5a8a3a'),
                alignment=TA_CENTER,
                spaceAfter=24,
            )
        )
        elementos.append(subtitulo)
        
        elementos.append(Spacer(1, 0.3*inch))
        
        # Datos principales
        datos_portada = [
            ('Municipio:', self.plan.municipio or '-'),
            ('Nombre del Plan:', self.plan.nombre_plan or '-'),
            ('Número de Plan:', self.plan.numero_plan or '-'),
            ('Versión:', self.plan.version or '1.0'),
            ('Vigencia:', f"{self.plan.vigencia_desde.strftime('%d/%m/%Y') if self.plan.vigencia_desde else 'N/A'} - {self.plan.vigencia_hasta.strftime('%d/%m/%Y') if self.plan.vigencia_hasta else 'N/A'}"),
            ('Responsable Principal:', self.plan.responsable_principal or '-'),
            ('Teléfono:', self.plan.telefono_responsable or '-'),
            ('Correo Electrónico:', self.plan.correo_responsable or '-'),
            ('Fecha de Generación:', datetime.now().strftime('%d de %B de %Y')),
        ]
        
        for etiqueta, valor in datos_portada:
            fila = [
                Paragraph(f"<b>{etiqueta}</b>", self.styles['Etiqueta']),
                Paragraph(valor, self.styles['Cuerpo']),
            ]
            tbl = Table([fila], colWidths=[2*inch, 4*inch])
            tbl.setStyle(TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elementos.append(tbl)
            elementos.append(Spacer(1, 0.1*inch))
        
        return elementos
    
    def _crear_tabla_contenidos(self):
        """Crea tabla de contenidos"""
        elementos = []
        elementos.append(Paragraph("TABLA DE CONTENIDOS", self.styles['TituloSecciones']))
        elementos.append(Spacer(1, 0.2*inch))
        
        items_toc = [
            "1. INFORMACIÓN GENERAL",
            "2. ESCENARIO Y ANÁLISIS DE RIESGO",
            "3. ALERTAS Y NIVELES DE ACTIVACIÓN",
            "4. ORGANIZACIÓN Y ESTRUCTURA DE MANDO",
            "5. FASES DE RESPUESTA",
            "6. LOGÍSTICA Y RECURSOS",
            "7. ALBERGUES Y REFUGIOS",
            "8. COMUNICACIONES Y VOCERÍA",
            "9. SALUD Y ASISTENCIA HUMANITARIA",
            "10. PRESUPUESTO",
            "11. AUTORIZACIONES",
        ]
        
        for item in items_toc:
            elementos.append(Paragraph(f"• {item}", self.styles['Cuerpo']))
        
        return elementos
    
    def _crear_seccion_general(self):
        """Crea sección de información general"""
        elementos = []
        elementos.append(Paragraph("1. INFORMACIÓN GENERAL", self.styles['TituloSecciones']))
        elementos.append(Spacer(1, 0.15*inch))
        
        datos = [
            ('Nombre del Plan:', self.plan.nombre_plan or '-'),
            ('Tipo de Evento:', self.plan.tipo_evento.replace('_', ' ').title()),
            ('Ámbito:', self.plan.ambito or '-'),
            ('Municipio:', self.plan.municipio or '-'),
            ('Población Objetivo:', f"{self.plan.poblacion_objetivo or '0'} personas"),
            ('Área de Cobertura:', self.plan.area_cobertura or '-'),
            ('Responsable Principal:', self.plan.responsable_principal or '-'),
            ('Teléfono de Contacto:', self.plan.telefono_responsable or '-'),
            ('Correo Electrónico:', self.plan.correo_responsable or '-'),
            ('Entidad Responsable:', self.plan.entidad_responsable or 'Alcaldía Municipal'),
        ]
        
        for label, value in datos:
            elementos.append(Paragraph(f"<b>{label}</b> {value}", self.styles['Cuerpo']))
        
        return elementos
    
    def _crear_escenario_riesgo(self):
        """Crea sección de escenario y riesgo"""
        elementos = []
        elementos.append(Paragraph("2. ESCENARIO Y ANÁLISIS DE RIESGO", self.styles['TituloSecciones']))
        elementos.append(Spacer(1, 0.15*inch))
        
        secciones = [
            ('Descripción del Peligro:', self.plan.descripcion_peligro),
            ('Antecedentes Históricos:', self.plan.antecedentes_historicos),
            ('Población Expuesta:', self.plan.poblacion_expuesta),
            ('Activos Expuestos:', self.plan.activos_expuestos),
            ('Supuestos y Limitaciones:', self.plan.supuestos_limitaciones),
        ]
        
        for titulo, contenido in secciones:
            if contenido:
                elementos.append(Paragraph(f"<b>{titulo}</b>", self.styles['SubtituloSecciones']))
                elementos.append(Paragraph(contenido or 'Sin información', self.styles['Cuerpo']))
                elementos.append(Spacer(1, 0.1*inch))
        
        return elementos
    
    def _crear_alertas(self):
        """Crea sección de alertas y umbrales"""
        elementos = []
        elementos.append(Paragraph("3. ALERTAS Y NIVELES DE ACTIVACIÓN", self.styles['TituloSecciones']))
        elementos.append(Spacer(1, 0.15*inch))
        
        umbrales = {}
        if self.plan.umbrales_alertas:
            try:
                umbrales = json.loads(self.plan.umbrales_alertas) if isinstance(self.plan.umbrales_alertas, str) else self.plan.umbrales_alertas
            except:
                pass
        
        if umbrales:
            datos_tabla = [['Nivel', 'Criterio/Descripción']]
            for nivel, criterio in umbrales.items():
                datos_tabla.append([nivel.upper(), str(criterio)])
            
            tabla = Table(datos_tabla, colWidths=[1.5*inch, 4.5*inch])
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d5016')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            ]))
            elementos.append(tabla)
        else:
            elementos.append(Paragraph("Sin información de umbrales", self.styles['Cuerpo']))
        
        return elementos
    
    def _crear_estructura_organizativa(self):
        """Crea sección de estructura organizativa"""
        elementos = []
        elementos.append(Paragraph("4. ORGANIZACIÓN Y ESTRUCTURA DE MANDO", self.styles['TituloSecciones']))
        elementos.append(Spacer(1, 0.15*inch))
        
        estructura = {}
        if self.plan.estructura_organizativa:
            try:
                estructura = json.loads(self.plan.estructura_organizativa) if isinstance(self.plan.estructura_organizativa, str) else self.plan.estructura_organizativa
            except:
                pass
        
        if estructura and isinstance(estructura, dict) and 'roles' in estructura:
            roles = estructura['roles']
            if roles:
                datos_tabla = [['Sector', 'Responsable', 'Teléfono', 'Correo']]
                for rol in roles:
                    if isinstance(rol, dict):
                        datos_tabla.append([
                            rol.get('sector', '-'),
                            rol.get('responsable', '-'),
                            rol.get('telefono', '-'),
                            rol.get('correo', '-'),
                        ])
                
                tabla = Table(datos_tabla, colWidths=[1.2*inch, 2*inch, 1.3*inch, 1.5*inch])
                tabla.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5a8a3a')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                ]))
                elementos.append(tabla)
        
        if self.plan.estructura_comando_desc:
            elementos.append(Spacer(1, 0.15*inch))
            elementos.append(Paragraph("<b>Descripción de la Estructura:</b>", self.styles['SubtituloSecciones']))
            elementos.append(Paragraph(self.plan.estructura_comando_desc, self.styles['Cuerpo']))
        
        return elementos
    
    def _crear_fases_respuesta(self):
        """Crea sección de fases de respuesta"""
        elementos = []
        elementos.append(Paragraph("5. FASES DE RESPUESTA", self.styles['TituloSecciones']))
        elementos.append(Spacer(1, 0.15*inch))
        
        fases = [
            ('Preparación', self.plan.fase_preparacion),
            ('Alistamiento', self.plan.fase_alistamiento),
            ('Respuesta', self.plan.fase_respuesta),
            ('Rehabilitación', self.plan.fase_rehabilitacion),
        ]
        
        for nombre_fase, contenido in fases:
            elementos.append(Paragraph(f"<b>{nombre_fase}</b>", self.styles['SubtituloSecciones']))
            elementos.append(Paragraph(contenido or 'Sin información', self.styles['Cuerpo']))
            elementos.append(Spacer(1, 0.1*inch))
        
        return elementos
    
    def _crear_logistica(self):
        """Crea sección de logística"""
        elementos = []
        elementos.append(Paragraph("6. LOGÍSTICA Y RECURSOS", self.styles['TituloSecciones']))
        elementos.append(Spacer(1, 0.15*inch))
        
        seccs = [
            ('Inventario de Recursos', self.plan.inventario_recursos),
            ('Puntos de Acopio', self.plan.puntos_acopio),
            ('Rutas de Abastecimiento', self.plan.rutas_abastecimiento),
        ]
        
        for titulo, contenido in seccs:
            if contenido:
                elementos.append(Paragraph(f"<b>{titulo}</b>", self.styles['SubtituloSecciones']))
                elementos.append(Paragraph(contenido, self.styles['Cuerpo']))
                elementos.append(Spacer(1, 0.1*inch))
        
        return elementos
    
    def _crear_albergues(self):
        """Crea sección de albergues"""
        elementos = []
        elementos.append(Paragraph("7. ALBERGUES Y REFUGIOS", self.styles['TituloSecciones']))
        elementos.append(Spacer(1, 0.15*inch))
        
        if self.plan.albergues:
            elementos.append(Paragraph(self.plan.albergues, self.styles['Cuerpo']))
        else:
            elementos.append(Paragraph("Sin información de albergues", self.styles['Cuerpo']))
        
        return elementos
    
    def _crear_comunicaciones(self):
        """Crea sección de comunicaciones"""
        elementos = []
        elementos.append(Paragraph("8. COMUNICACIONES Y VOCERÍA", self.styles['TituloSecciones']))
        elementos.append(Spacer(1, 0.15*inch))
        
        seccs = [
            ('Vocerías', self.plan.vocerías if hasattr(self.plan, 'vocerías') else None),
            ('Canales de Comunicación', self.plan.canales_comunicacion),
            ('Formatos de Boletines', self.plan.formatos_boletines),
        ]
        
        for titulo, contenido in seccs:
            if contenido:
                elementos.append(Paragraph(f"<b>{titulo}</b>", self.styles['SubtituloSecciones']))
                elementos.append(Paragraph(contenido, self.styles['Cuerpo']))
                elementos.append(Spacer(1, 0.1*inch))
        
        return elementos
    
    def _crear_salud(self):
        """Crea sección de salud"""
        elementos = []
        elementos.append(Paragraph("9. SALUD Y ASISTENCIA HUMANITARIA", self.styles['TituloSecciones']))
        elementos.append(Spacer(1, 0.15*inch))
        
        seccs = [
            ('Protocolos de Salud', self.plan.protocolos_salud),
            ('Grupos Vulnerables', self.plan.grupos_vulnerables),
            ('Kits Humanitarios', self.plan.kits_humanitarios),
        ]
        
        for titulo, contenido in seccs:
            if contenido:
                elementos.append(Paragraph(f"<b>{titulo}</b>", self.styles['SubtituloSecciones']))
                elementos.append(Paragraph(contenido, self.styles['Cuerpo']))
                elementos.append(Spacer(1, 0.1*inch))
        
        return elementos
    
    def _crear_presupuesto(self):
        """Crea sección de presupuesto"""
        elementos = []
        elementos.append(Paragraph("10. PRESUPUESTO", self.styles['TituloSecciones']))
        elementos.append(Spacer(1, 0.15*inch))
        
        if self.plan.presupuesto_total:
            elementos.append(Paragraph(
                f"<b>Presupuesto Total:</b> ${self.plan.presupuesto_total:,}",
                self.styles['Cuerpo']
            ))
        
        if self.plan.presupuesto_por_fase:
            elementos.append(Spacer(1, 0.1*inch))
            elementos.append(Paragraph("<b>Distribución por Fases</b>", self.styles['SubtituloSecciones']))
            elementos.append(Paragraph(self.plan.presupuesto_por_fase, self.styles['Cuerpo']))
        
        if self.plan.fuentes_financiamiento:
            elementos.append(Spacer(1, 0.1*inch))
            elementos.append(Paragraph("<b>Fuentes de Financiamiento</b>", self.styles['SubtituloSecciones']))
            elementos.append(Paragraph(self.plan.fuentes_financiamiento, self.styles['Cuerpo']))
        
        return elementos
    
    def _crear_autorizaciones(self):
        """Crea página de autorizaciones"""
        elementos = []
        elementos.append(Paragraph("11. AUTORIZACIONES", self.styles['TituloSecciones']))
        elementos.append(Spacer(1, 0.3*inch))
        
        # Líneas de firma
        firmas = [
            ('Responsable Principal', self.plan.responsable_principal or '________________'),
            ('Aprobado por', self.plan.aprobado_por or '________________'),
        ]
        
        for titulo, valor in firmas:
            elementos.append(Spacer(1, 0.25*inch))
            elementos.append(Paragraph(f"<b>{titulo}</b>", self.styles['Cuerpo']))
            elementos.append(Paragraph('_' * 50, self.styles['Cuerpo']))
            elementos.append(Paragraph(valor, self.styles['Cuerpo']))
            elementos.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", self.styles['Cuerpo']))
        
        return elementos
