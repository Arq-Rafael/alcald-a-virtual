"""
Generador Profesional de PDF para Planes de Contingencia
Formato Oficial de la Alcaldía - Diseño Visual Premium
"""
import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Image as RLImage, KeepTogether, PageTemplate, Frame,
    Preformatted
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PyPDF2 import PdfReader, PdfWriter


class PDFPlanContingenciaOficial:
    """Generador profesional de PDF para Planes de Contingencia con formato oficial"""
    
    # Colores oficiales de la Alcaldía
    COLOR_PRIMARY = colors.HexColor('#1a472a')      # Verde oscuro oficial
    COLOR_SECONDARY = colors.HexColor('#2d5016')    # Verde intermedio
    COLOR_ACCENT = colors.HexColor('#7cb342')       # Verde claro
    COLOR_TEXT = colors.HexColor('#333333')
    COLOR_LIGHT = colors.HexColor('#f5f5f5')
    COLOR_BORDER = colors.HexColor('#cccccc')
    
    def __init__(self, plan, current_app):
        self.plan = plan
        self.current_app = current_app
        self.w, self.h = letter
        self.margin = 0.6 * inch
        self.styles = getSampleStyleSheet()
        self._crear_estilos_profesionales()
    
    def _crear_estilos_profesionales(self):
        """Crea estilos profesionales según formato Alcaldía"""
        
        # Título principal
        self.styles.add(ParagraphStyle(
            name='TituloPrincipal',
            parent=self.styles['Heading1'],
            fontSize=20,
            textColor=self.COLOR_PRIMARY,
            spaceAfter=6,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))
        
        # Subtítulo (tipo evento)
        self.styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=self.COLOR_SECONDARY,
            spaceAfter=10,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))
        
        # Encabezados de sección
        self.styles.add(ParagraphStyle(
            name='TituloSeccion',
            parent=self.styles['Heading2'],
            fontSize=13,
            textColor=colors.white,
            spaceAfter=10,
            fontName='Helvetica-Bold',
            textTransform='uppercase',
            backColor=self.COLOR_PRIMARY,
            leftIndent=8,
            rightIndent=8,
            topPadding=6,
            bottomPadding=6
        ))
        
        # Subencabezados
        self.styles.add(ParagraphStyle(
            name='SubtituloSeccion',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=self.COLOR_SECONDARY,
            spaceAfter=8,
            fontName='Helvetica-Bold',
            borderColor=self.COLOR_ACCENT,
            borderWidth=2,
            borderPadding=6,
            leftIndent=4
        ))
        
        # Cuerpo de texto
        self.styles.add(ParagraphStyle(
            name='Cuerpo',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.COLOR_TEXT,
            spaceAfter=10,
            fontName='Helvetica',
            alignment=TA_JUSTIFY,
            leading=14
        ))
        
        # Etiquetas de campo
        self.styles.add(ParagraphStyle(
            name='Etiqueta',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.COLOR_PRIMARY,
            fontName='Helvetica-Bold',
            spaceAfter=2
        ))
        
        # Valores de campo
        self.styles.add(ParagraphStyle(
            name='Valor',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.COLOR_TEXT,
            fontName='Helvetica',
            spaceAfter=8,
            leftIndent=12
        ))
        
        # Información resaltada
        self.styles.add(ParagraphStyle(
            name='Resaltado',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.white,
            fontName='Helvetica-Bold',
            backColor=self.COLOR_SECONDARY,
            leftIndent=6,
            rightIndent=6,
            topPadding=4,
            bottomPadding=4,
            spaceAfter=8
        ))
        
        # Pie de página
        self.styles.add(ParagraphStyle(
            name='PiePagina',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#999999'),
            alignment=TA_CENTER,
            spaceAfter=0
        ))
    
    def generar(self):
        """Genera el PDF completo del Plan de Contingencia con formato oficial"""
        try:
            buffer = __import__('io').BytesIO()
            
            # Crear documento con márgenes profesionales
            # Reservar espacio para encabezado del FORMATO.pdf oficial
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                topMargin=1.5 * inch,
                bottomMargin=0.7 * inch,
                leftMargin=self.margin,
                rightMargin=self.margin
            )
            
            # Construir contenido
            contenido = []
            
            # PORTADA (según estado del plan)
            contenido.extend(self._crear_portada_moderna())
            contenido.append(PageBreak())
            
            # TABLA DE CONTENIDOS
            contenido.extend(self._crear_tabla_contenidos())
            contenido.append(PageBreak())
            
            # SECCIONES PRINCIPALES
            contenido.extend(self._crear_info_general())
            contenido.append(PageBreak())
            
            contenido.extend(self._crear_escenario())
            contenido.append(PageBreak())
            
            contenido.extend(self._crear_alertas())
            contenido.append(PageBreak())
            
            contenido.extend(self._crear_estructura_org())
            contenido.append(PageBreak())
            
            contenido.extend(self._crear_fases())
            contenido.append(PageBreak())
            
            contenido.extend(self._crear_logistica())
            contenido.append(PageBreak())
            
            contenido.extend(self._crear_albergues())
            contenido.append(PageBreak())
            
            contenido.extend(self._crear_comunicaciones())
            contenido.append(PageBreak())
            
            contenido.extend(self._crear_salud())
            contenido.append(PageBreak())
            
            contenido.extend(self._crear_presupuesto())
            contenido.append(PageBreak())
            
            contenido.extend(self._crear_autorizaciones())
            
            # Construir PDF base (overlay)
            doc.build(contenido)
            buffer.seek(0)

            # ============================================
            # COMBINAR CON FORMATO OFICIAL (como en oficios)
            # ============================================
            try:
                formato_path = os.path.join(self.current_app.config['DATA_DIR'], 'FORMATO.pdf')
                if os.path.exists(formato_path):
                    template_pdf = PdfReader(formato_path)
                    overlay_pdf = PdfReader(buffer)
                    output = PdfWriter()

                    # Aplicar formato oficial a cada página
                    for page_num in range(len(overlay_pdf.pages)):
                        template_page = PdfReader(formato_path).pages[0]
                        overlay_page = overlay_pdf.pages[page_num]
                        template_page.merge_page(overlay_page)
                        output.add_page(template_page)

                    final_buffer = __import__('io').BytesIO()
                    output.write(final_buffer)
                    final_buffer.seek(0)
                    return final_buffer
                else:
                    print("ADVERTENCIA: FORMATO.pdf no encontrado, devolviendo PDF sin formato oficial")
                    buffer.seek(0)
                    return buffer
            except Exception as e:
                print(f"Error al combinar con FORMATO oficial: {e}")
                buffer.seek(0)
                return buffer
            
        except Exception as e:
            print(f"Error generando PDF: {e}")
            raise
    
    def _crear_portada_moderna(self):
        """Crea portada moderna con colores según tipo de evento y estado del plan"""
        contenido = []
        
        # Mapeo de colores por tipo de evento
        COLORES_EVENTOS = {
            'Lluvias': '#2563eb',
            'Incendios': '#dc2626',
            'Eventos masivos': '#7c3aed',
            'Deslizamientos': '#ea580c',
            'Sequia': '#f59e0b',
            'Sequía': '#f59e0b',
            'Derrames': '#059669'
        }
        
        # Determinar color según tipo de evento
        tipo_evento = self.plan.get('tipo_evento', 'Evento').replace('_', ' ')
        color_evento = COLORES_EVENTOS.get(tipo_evento, '#1a472a')
        
        # Determinar estado y color de badge
        estado = (self.plan.get('estado') or 'Borrador').lower()
        if estado in ['aprobado', 'aprobado_comite']:
            estado_texto = "APROBADO"
            estado_color = HexColor('#10b981')  # Verde
        elif estado in ['revision', 'en_revision']:
            estado_texto = "EN REVISIÓN"
            estado_color = HexColor('#f59e0b')  # Amarillo/Naranja
        else:
            estado_texto = "BORRADOR"
            estado_color = HexColor('#6b7280')  # Gris
        
        # Espaciador superior
        contenido.append(Spacer(1, 0.3 * inch))
        
        # Banner de color del evento (franja decorativa)
        banner_table = Table([['']],colWidths=[6.5*inch])
        banner_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor(color_evento)),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        contenido.append(banner_table)
        contenido.append(Spacer(1, 0.15 * inch))
        
        # Título principal
        titulo = Paragraph(
            "PLAN DE CONTINGENCIA",
            ParagraphStyle(
                'TituloPortada',
                parent=self.styles['Normal'],
                fontSize=26,
                textColor=HexColor(color_evento),
                fontName='Helvetica-Bold',
                alignment=TA_CENTER,
                spaceAfter=8
            )
        )
        contenido.append(titulo)
        
        # Subtítulo con tipo de evento
        subtitulo = Paragraph(
            f"PARA {tipo_evento.upper()}",
            ParagraphStyle(
                'SubtituloPortada',
                parent=self.styles['Normal'],
                fontSize=18,
                textColor=self.COLOR_SECONDARY,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER,
                spaceAfter=20
            )
        )
        contenido.append(subtitulo)
        
        # Badge de estado
        badge = Paragraph(
            f"● {estado_texto}",
            ParagraphStyle(
                'BadgeEstado',
                parent=self.styles['Normal'],
                fontSize=14,
                textColor=colors.white,
                backColor=estado_color,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER,
                borderPadding=10,
                spaceAfter=25
            )
        )
        contenido.append(badge)
        
        # Tabla de información del plan
        info_data = [
            [
                Paragraph("<b>Número de Plan:</b>", self.styles['Etiqueta']),
                Paragraph(str(self.plan.get('numero_plan', 'S/N')), self.styles['Valor'])
            ],
            [
                Paragraph("<b>Fecha de Elaboración:</b>", self.styles['Etiqueta']),
                Paragraph(datetime.now().strftime('%d de %B de %Y'), self.styles['Valor'])
            ],
            [
                Paragraph("<b>Cobertura:</b>", self.styles['Etiqueta']),
                Paragraph(self.plan.get('cobertura', 'Municipal'), self.styles['Valor'])
            ],
            [
                Paragraph("<b>Responsable:</b>", self.styles['Etiqueta']),
                Paragraph(self.plan.get('responsable_plan', 'No especificado'), self.styles['Valor'])
            ]
        ]
        
        # Agregar datos de aprobación si está aprobado
        if estado in ['aprobado', 'aprobado_comite']:
            if self.plan.get('numero_resolucion'):
                info_data.append([
                    Paragraph("<b>Resolución:</b>", self.styles['Etiqueta']),
                    Paragraph(self.plan.get('numero_resolucion', ''), self.styles['Valor'])
                ])
            if self.plan.get('fecha_resolucion'):
                info_data.append([
                    Paragraph("<b>Fecha de Aprobación:</b>", self.styles['Etiqueta']),
                    Paragraph(self.plan.get('fecha_resolucion', ''), self.styles['Valor'])
                ])
            if self.plan.get('aprobado_por'):
                info_data.append([
                    Paragraph("<b>Aprobado por:</b>", self.styles['Etiqueta']),
                    Paragraph(self.plan.get('aprobado_por', ''), self.styles['Valor'])
                ])
        
        tabla_info = Table(info_data, colWidths=[2.2*inch, 3.3*inch])
        tabla_info.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLOR_LIGHT),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1.5, HexColor(color_evento)),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        contenido.append(tabla_info)
        contenido.append(Spacer(1, 0.4 * inch))
        
        # Pie de portada
        pie_texto = "Este documento constituye el Plan de Contingencia oficial de la Alcaldía Municipal de Supatá."
        if estado not in ['aprobado', 'aprobado_comite']:
            pie_texto += "<br/><b>Documento en proceso de elaboración - No válido para ejecución oficial.</b>"
        else:
            pie_texto += "<br/><i>Documento oficial aprobado por el Comité de Gestión del Riesgo.</i>"
        
        pie = Paragraph(
            pie_texto,
            ParagraphStyle(
                'PiePortada',
                parent=self.styles['Normal'],
                fontSize=9,
                textColor=self.COLOR_SECONDARY,
                alignment=TA_CENTER,
                leading=13,
                spaceAfter=6
            )
        )
        contenido.append(pie)
        
        return contenido

    
    def _crear_tabla_contenidos(self):
        """Crea tabla de contenidos"""
        contenido = []
        
        titulo = Paragraph("TABLA DE CONTENIDOS", self.styles['TituloSeccion'])
        contenido.append(titulo)
        contenido.append(Spacer(1, 0.2 * inch))
        
        items = [
            "1. Información General del Plan",
            "2. Descripción del Escenario de Riesgo",
            "3. Umbrales de Alerta y Activación",
            "4. Estructura Organizacional de Respuesta",
            "5. Fases de Implementación",
            "6. Logística y Recursos",
            "7. Centros de Albergue",
            "8. Comunicaciones y Coordinación",
            "9. Atención en Salud",
            "10. Presupuesto Estimado",
            "11. Autorizaciones y Aprobaciones"
        ]
        
        for item in items:
            p = Paragraph(f"• {item}", self.styles['Cuerpo'])
            contenido.append(p)
        
        return contenido
    
    def _crear_info_general(self):
        """Crea sección de información general"""
        contenido = []
        
        titulo = Paragraph("1. INFORMACIÓN GENERAL", self.styles['TituloSeccion'])
        contenido.append(titulo)
        contenido.append(Spacer(1, 0.15 * inch))
        
        # Descripción
        desc = Paragraph(
            self.plan.get('descripcion', 'No especificada'),
            self.styles['Cuerpo']
        )
        contenido.append(desc)
        contenido.append(Spacer(1, 0.15 * inch))
        
        # Tabla de identificación
        info_table = [
            [
                Paragraph("<b>Nombre del Plan</b>", self.styles['Etiqueta']),
                Paragraph(
                    f"Plan de Contingencia - {self.plan.get('tipo_evento', 'Evento')}",
                    self.styles['Valor']
                )
            ],
            [
                Paragraph("<b>Identificación del Riesgo</b>", self.styles['Etiqueta']),
                Paragraph(self.plan.get('tipo_evento', 'N/A'), self.styles['Valor'])
            ],
            [
                Paragraph("<b>Jurisdicción</b>", self.styles['Etiqueta']),
                Paragraph(self.plan.get('cobertura', 'N/A'), self.styles['Valor'])
            ],
            [
                Paragraph("<b>Responsable del Plan</b>", self.styles['Etiqueta']),
                Paragraph(self.plan.get('responsable_plan', 'N/A'), self.styles['Valor'])
            ]
        ]
        
        tabla = Table(info_table, colWidths=[2*inch, 3*inch])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.COLOR_LIGHT),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, self.COLOR_BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        contenido.append(tabla)
        return contenido
    
    def _crear_escenario(self):
        """Crea sección de escenario"""
        contenido = []
        
        titulo = Paragraph("2. DESCRIPCIÓN DEL ESCENARIO", self.styles['TituloSeccion'])
        contenido.append(titulo)
        contenido.append(Spacer(1, 0.15 * inch))
        
        desc = Paragraph(
            self.plan.get('escenario', 'Descripción del escenario no especificada'),
            self.styles['Cuerpo']
        )
        contenido.append(desc)
        
        return contenido
    
    def _crear_alertas(self):
        """Crea sección de umbrales y alertas"""
        contenido = []
        
        titulo = Paragraph("3. UMBRALES DE ALERTA", self.styles['TituloSeccion'])
        contenido.append(titulo)
        contenido.append(Spacer(1, 0.15 * inch))
        
        umbrales = self.plan.get('umbrales', [])
        if umbrales:
            for umbral in umbrales:
                alerta = Paragraph(
                    f"<b>• Umbral {umbral.get('nivel', 'N/A')}:</b> {umbral.get('descripcion', '')}",
                    self.styles['Cuerpo']
                )
                contenido.append(alerta)
        
        return contenido
    
    def _crear_estructura_org(self):
        """Crea sección de estructura organizacional"""
        contenido = []
        
        titulo = Paragraph("4. ESTRUCTURA ORGANIZACIONAL", self.styles['TituloSeccion'])
        contenido.append(titulo)
        contenido.append(Spacer(1, 0.15 * inch))
        
        roles = self.plan.get('roles', [])
        if roles:
            headers = [
                Paragraph("<b>Rol/Cargo</b>", self.styles['Etiqueta']),
                Paragraph("<b>Nombre</b>", self.styles['Etiqueta']),
                Paragraph("<b>Contacto</b>", self.styles['Etiqueta']),
                Paragraph("<b>Responsabilidades</b>", self.styles['Etiqueta'])
            ]
            
            data = [headers]
            for rol in roles[:5]:  # Limitar a 5 filas
                data.append([
                    Paragraph(rol.get('rol', '-'), self.styles['Valor']),
                    Paragraph(rol.get('nombre', '-'), self.styles['Valor']),
                    Paragraph(rol.get('contacto', '-'), self.styles['Valor']),
                    Paragraph(rol.get('responsabilidad', '-'), self.styles['Valor'])
                ])
            
            tabla = Table(data, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 1.3*inch])
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.COLOR_PRIMARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, self.COLOR_BORDER),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.COLOR_LIGHT, colors.white]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            
            contenido.append(tabla)
        
        return contenido
    
    def _crear_fases(self):
        """Crea sección de fases"""
        contenido = []
        
        titulo = Paragraph("5. FASES DE IMPLEMENTACIÓN", self.styles['TituloSeccion'])
        contenido.append(titulo)
        contenido.append(Spacer(1, 0.15 * inch))
        
        fases = self.plan.get('fases', [])
        if fases:
            for fase in fases[:3]:
                fase_titulo = Paragraph(
                    f"<b>{fase.get('nombre', 'Fase')}:</b>",
                    self.styles['SubtituloSeccion']
                )
                contenido.append(fase_titulo)
                
                fase_desc = Paragraph(
                    fase.get('descripcion', ''),
                    self.styles['Cuerpo']
                )
                contenido.append(fase_desc)
        
        return contenido
    
    def _crear_logistica(self):
        """Crea sección de logística"""
        contenido = []
        
        titulo = Paragraph("6. LOGÍSTICA Y RECURSOS", self.styles['TituloSeccion'])
        contenido.append(titulo)
        contenido.append(Spacer(1, 0.15 * inch))
        
        recursos = self.plan.get('recursos_disponibles', [])
        if recursos:
            for recurso in recursos[:5]:
                item = Paragraph(
                    f"• <b>{recurso.get('tipo', 'Recurso')}:</b> {recurso.get('descripcion', '')}",
                    self.styles['Cuerpo']
                )
                contenido.append(item)
        
        return contenido
    
    def _crear_albergues(self):
        """Crea sección de albergues"""
        contenido = []
        
        titulo = Paragraph("7. CENTROS DE ALBERGUE", self.styles['TituloSeccion'])
        contenido.append(titulo)
        contenido.append(Spacer(1, 0.15 * inch))
        
        albergues = self.plan.get('albergues', [])
        if albergues:
            for albergue in albergues[:3]:
                alb_titulo = Paragraph(
                    f"<b>{albergue.get('nombre', 'Albergue')}:</b>",
                    self.styles['SubtituloSeccion']
                )
                contenido.append(alb_titulo)
                
                alb_info = Paragraph(
                    f"Ubicación: {albergue.get('ubicacion', 'N/A')}<br/>"
                    f"Capacidad: {albergue.get('capacidad', 'N/A')} personas<br/>"
                    f"Responsable: {albergue.get('responsable', 'N/A')}",
                    self.styles['Cuerpo']
                )
                contenido.append(alb_info)
        
        return contenido
    
    def _crear_comunicaciones(self):
        """Crea sección de comunicaciones"""
        contenido = []
        
        titulo = Paragraph("8. COMUNICACIONES Y COORDINACIÓN", self.styles['TituloSeccion'])
        contenido.append(titulo)
        contenido.append(Spacer(1, 0.15 * inch))
        
        comun = Paragraph(
            self.plan.get('comunicaciones', 'Plan de comunicaciones no especificado'),
            self.styles['Cuerpo']
        )
        contenido.append(comun)
        
        return contenido
    
    def _crear_salud(self):
        """Crea sección de salud"""
        contenido = []
        
        titulo = Paragraph("9. ATENCIÓN EN SALUD", self.styles['TituloSeccion'])
        contenido.append(titulo)
        contenido.append(Spacer(1, 0.15 * inch))
        
        salud = Paragraph(
            self.plan.get('salud', 'Plan de salud no especificado'),
            self.styles['Cuerpo']
        )
        contenido.append(salud)
        
        return contenido
    
    def _crear_presupuesto(self):
        """Crea sección de presupuesto"""
        contenido = []
        
        titulo = Paragraph("10. PRESUPUESTO ESTIMADO", self.styles['TituloSeccion'])
        contenido.append(titulo)
        contenido.append(Spacer(1, 0.15 * inch))
        
        presupuesto_total = self.plan.get('presupuesto_total', 0)
        presupuesto_items = self.plan.get('presupuesto', [])
        
        if presupuesto_items:
            headers = [
                Paragraph("<b>Concepto</b>", self.styles['Etiqueta']),
                Paragraph("<b>Cantidad</b>", self.styles['Etiqueta']),
                Paragraph("<b>Valor Unitario</b>", self.styles['Etiqueta']),
                Paragraph("<b>Total</b>", self.styles['Etiqueta'])
            ]
            
            data = [headers]
            for item in presupuesto_items[:5]:
                data.append([
                    Paragraph(item.get('concepto', '-'), self.styles['Valor']),
                    Paragraph(str(item.get('cantidad', '-')), self.styles['Valor']),
                    Paragraph(f"${item.get('valor_unitario', 0):,}", self.styles['Valor']),
                    Paragraph(f"${item.get('total', 0):,}", self.styles['Valor'])
                ])
            
            tabla = Table(data, colWidths=[2*inch, 1*inch, 1.5*inch, 1.5*inch])
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.COLOR_PRIMARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, self.COLOR_BORDER),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.COLOR_LIGHT, colors.white])
            ]))
            
            contenido.append(tabla)
        
        # Total
        contenido.append(Spacer(1, 0.15 * inch))
        total_para = Paragraph(
            f"<b>PRESUPUESTO TOTAL ESTIMADO: ${presupuesto_total:,.0f}</b>",
            self.styles['Resaltado']
        )
        contenido.append(total_para)
        
        return contenido
    
    def _crear_autorizaciones(self):
        """Crea sección de autorizaciones y aprobaciones"""
        contenido = []
        
        titulo = Paragraph("11. AUTORIZACIONES Y APROBACIONES", self.styles['TituloSeccion'])
        contenido.append(titulo)
        contenido.append(Spacer(1, 0.3 * inch))
        
        firmantes = [
            ("Elaborado por:", self.plan.get('elaborado_por', '_' * 40)),
            ("Revisado por:", self.plan.get('revisado_por', '_' * 40)),
            ("Aprobado por:", self.plan.get('aprobado_por', '_' * 40))
        ]
        
        for label, nombre in firmantes:
            contenido.append(Spacer(1, 0.25 * inch))
            
            linea = Paragraph(
                f"{label}",
                self.styles['Etiqueta']
            )
            contenido.append(linea)
            
            contenido.append(Spacer(1, 0.1 * inch))
            
            firma_linea = Paragraph(
                "__________________________",
                self.styles['Cuerpo']
            )
            contenido.append(firma_linea)
            
            nombre_linea = Paragraph(
                f"<i>{nombre}</i>",
                self.styles['Valor']
            )
            contenido.append(nombre_linea)
        
        # Pie de documento
        contenido.append(Spacer(1, 0.3 * inch))
        pie = Paragraph(
            f"Documento generado: {datetime.now().strftime('%d/%m/%Y a las %H:%M')}<br/>"
            "Este documento es confidencial y para uso oficial de la Alcaldía Municipal.",
            self.styles['PiePagina']
        )
        contenido.append(pie)
        
        return contenido
