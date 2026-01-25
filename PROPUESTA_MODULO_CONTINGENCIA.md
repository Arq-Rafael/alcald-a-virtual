# 🚨 PROPUESTA DE REDISEÑO COMPLETO - MÓDULO PLANES DE CONTINGENCIA

## 📋 ANÁLISIS DEL FORMATO OFICIAL

He analizado el archivo Word oficial ubicado en:
`documentos_generados\gestion_riesgo\planes_contingencia\formato plan de contingencia.docx`

### Estructura Oficial Identificada:

**9 Secciones Principales:**
1. **Introducción** - Descripción del evento, justificación, contexto normativo
2. **Objetivos y Alcance** - Objetivo general, específicos, fechas, ubicación, aforo
3. **Marco Normativo** - Ley 1523/2012, Decreto 2157/2017, normas locales
4. **Organización y Responsabilidades** - Comité, coordinadores, PMU, directorio
5. **Análisis de Riesgos** - Amenazas (naturales/tecnológicas/antrópicas), matriz de riesgos
6. **Medidas de Reducción** - Prevención, mitigación, seguridad, capacitación
7. **Plan de Respuesta** - 9 subsecciones (alertas, comando, protocolos, evacuación, etc.)
8. **Actualización y Mejora** - Mecanismos de revisión del plan
9. **Anexos Técnicos** - Mapas, planos, formatos

**3 Tablas Clave:**
- **Tabla 1:** Organización (Cargo/Responsable, Nombre, Funciones)
- **Tabla 2:** Matriz de Riesgos (Amenaza, Probabilidad, Impacto, Nivel, Medidas)
- **Tabla 3:** Directorio de Emergencias (Entidad, Teléfono, Canal Radio, Observaciones)

---

## 🎯 PROBLEMÁTICA ACTUAL

### Problemas Identificados:
1. ❌ **Rutas faltantes**: `/editar/{id}` y `/detalle/{id}` retornan 404
2. ❌ **Modelo simple**: Actual modelo solo tiene campos básicos (tipo_evento, descripcion, ubicacion)
3. ❌ **Sin estructura de secciones**: No refleja las 9 secciones del formato oficial
4. ❌ **Sin auto-población**: Datos de Supatá deben ingresarse manualmente
5. ❌ **PDF básico**: No replica exactamente la estructura del Word oficial
6. ❌ **Sin edición por secciones**: Todo se edita en un solo formulario

---

## 🏗️ ARQUITECTURA PROPUESTA

### 1. NUEVO MODELO DE DATOS

#### A) Ampliar modelo `PlanContingencia` (app/models/plan_contingencia.py)

```python
class PlanContingencia(db.Model):
    __tablename__ = 'planes_contingencia'
    
    # Campos actuales (mantener)
    id = db.Column(db.Integer, primary_key=True)
    tipo_evento = db.Column(db.String(100), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.Enum('borrador', 'en_revision', 'aprobado', 'aprobado_comite'))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    
    # NUEVOS CAMPOS - SECCIÓN 1: INTRODUCCIÓN
    descripcion_evento = db.Column(db.Text)  # Descripción completa del evento
    justificacion = db.Column(db.Text)  # Por qué se requiere el plan
    
    # SECCIÓN 2: OBJETIVOS Y ALCANCE
    objetivo_general = db.Column(db.Text)
    objetivos_especificos = db.Column(db.JSON)  # Array de objetivos
    evento_nombre = db.Column(db.String(200))  # "Concierto XYZ"
    evento_fecha_inicio = db.Column(db.DateTime)
    evento_fecha_fin = db.Column(db.DateTime)
    evento_ubicacion = db.Column(db.String(500))
    evento_aforo = db.Column(db.Integer)
    limites_geograficos = db.Column(db.Text)
    
    # SECCIÓN 3: MARCO NORMATIVO (auto-poblado en su mayoría)
    normas_adicionales = db.Column(db.JSON)  # Normas locales específicas
    
    # SECCIÓN 4: ORGANIZACIÓN
    coordinadores = db.Column(db.JSON)  # Array de {cargo, nombre, telefono, funciones}
    organismos_apoyo = db.Column(db.JSON)  # Array de organismos externos
    pmu_ubicacion = db.Column(db.String(200))  # Ubicación del PMU
    directorio_emergencias = db.Column(db.JSON)  # Tabla 3 del Word
    
    # SECCIÓN 5: ANÁLISIS DE RIESGOS
    escenario_caracteristicas = db.Column(db.Text)  # Tipo evento, lugar, hora, etc.
    amenazas = db.Column(db.JSON)  # Array de amenazas identificadas
    matriz_riesgos = db.Column(db.JSON)  # Tabla 2 del Word
    vulnerabilidades = db.Column(db.Text)
    
    # SECCIÓN 6: MEDIDAS DE REDUCCIÓN
    medidas_seguridad = db.Column(db.JSON)  # Array de medidas
    adecuaciones_lugar = db.Column(db.Text)
    medidas_sanitarias = db.Column(db.Text)
    capacitaciones = db.Column(db.JSON)
    seguros = db.Column(db.Text)
    
    # SECCIÓN 7: PLAN DE RESPUESTA (sub-secciones)
    niveles_alerta = db.Column(db.JSON)  # 7.1
    estructura_comando = db.Column(db.Text)  # 7.2
    procedimientos_generales = db.Column(db.JSON)  # 7.3
    protocolos_especificos = db.Column(db.JSON)  # 7.4 - Por tipo de emergencia
    plan_evacuacion = db.Column(db.JSON)  # 7.5
    plan_primeros_auxilios = db.Column(db.JSON)  # 7.6
    plan_logistica = db.Column(db.JSON)  # 7.7
    plan_comunicaciones = db.Column(db.JSON)  # 7.8
    estrategias_continuidad = db.Column(db.Text)  # 7.9
    
    # SECCIÓN 8: ACTUALIZACIÓN
    mecanismos_actualizacion = db.Column(db.Text)
    ultima_revision = db.Column(db.DateTime)
    
    # SECCIÓN 9: ANEXOS
    anexos = db.Column(db.JSON)  # Array de {tipo, archivo_url, descripcion}
    
    # DATOS MUNICIPALES (auto-poblados desde constantes de Supatá)
    municipio_datos = db.Column(db.JSON)  # {nombre, población, altitud, etc.}
```

#### B) Crear tabla de plantillas pre-configuradas

```python
class PlantillaContingencia(db.Model):
    """Plantillas con contenido pre-configurado según tipo de evento"""
    __tablename__ = 'plantillas_contingencia'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo_evento = db.Column(db.String(100), nullable=False)
    seccion = db.Column(db.String(50))  # "objetivos", "riesgos", "protocolos", etc.
    contenido_json = db.Column(db.JSON)  # Plantilla pre-llenada
    activo = db.Column(db.Boolean, default=True)
```

---

### 2. RUTAS Y CONTROLADORES

#### A) Crear archivo: `app/routes/contingencia_views.py`

```python
from flask import Blueprint, render_template, redirect, url_for, flash
from app.models.plan_contingencia import PlanContingencia
from app.utils.contingencia_helpers import get_datos_supata, get_plantilla_por_tipo

bp = Blueprint('contingencia_views', __name__, url_prefix='/gestion-riesgo/planes-contingencia')

@bp.route('/')
def index():
    """Lista de planes (ya existe en template)"""
    return render_template('riesgo_planes_contingencia.html')

@bp.route('/editar/<int:id>')
@bp.route('/editar/<int:id>/<seccion>')
def editar(id, seccion='introduccion'):
    """
    Formulario de edición por secciones (wizard)
    Parámetro 'seccion' permite navegar entre las 9 secciones
    """
    plan = PlanContingencia.query.get_or_404(id)
    
    # Validar que solo planes borrador o en_revision puedan editarse
    if plan.estado in ['aprobado', 'aprobado_comite']:
        flash('No se puede editar un plan aprobado', 'error')
        return redirect(url_for('contingencia_views.detalle', id=id))
    
    # Obtener datos de Supatá para auto-completar
    datos_supata = get_datos_supata()
    
    # Obtener plantilla según tipo de evento (si existe)
    plantilla = get_plantilla_por_tipo(plan.tipo_evento, seccion)
    
    return render_template(
        'contingencia_editar_wizard.html',
        plan=plan,
        seccion_actual=seccion,
        datos_municipio=datos_supata,
        plantilla=plantilla
    )

@bp.route('/detalle/<int:id>')
def detalle(id):
    """Vista de solo lectura del plan completo"""
    plan = PlanContingencia.query.get_or_404(id)
    datos_supata = get_datos_supata()
    
    return render_template(
        'contingencia_detalle.html',
        plan=plan,
        datos_municipio=datos_supata
    )
```

#### B) Actualizar `app/routes/contingencia_api.py`

```python
# NUEVAS RUTAS API

@app.route('/api/contingencia/<int:id>/seccion/<seccion>', methods=['PUT'])
def actualizar_seccion(id, seccion):
    """Guardar una sección específica del plan"""
    plan = PlanContingencia.query.get_or_404(id)
    data = request.get_json()
    
    # Mapeo de secciones a campos del modelo
    campos_seccion = {
        'introduccion': ['descripcion_evento', 'justificacion'],
        'objetivos': ['objetivo_general', 'objetivos_especificos', 'evento_nombre', ...],
        'organizacion': ['coordinadores', 'organismos_apoyo', 'pmu_ubicacion', ...],
        'riesgos': ['escenario_caracteristicas', 'amenazas', 'matriz_riesgos', ...],
        # ... etc
    }
    
    # Actualizar solo los campos de esa sección
    for campo in campos_seccion.get(seccion, []):
        if campo in data:
            setattr(plan, campo, data[campo])
    
    db.session.commit()
    return jsonify({'success': True, 'mensaje': f'Sección {seccion} guardada'})

@app.route('/api/contingencia/plantilla/<tipo_evento>/<seccion>')
def obtener_plantilla(tipo_evento, seccion):
    """Retorna plantilla pre-configurada para un tipo de evento y sección"""
    plantilla = PlantillaContingencia.query.filter_by(
        tipo_evento=tipo_evento,
        seccion=seccion,
        activo=True
    ).first()
    
    if plantilla:
        return jsonify(plantilla.contenido_json)
    return jsonify({})

@app.route('/api/contingencia/datos-municipio')
def datos_municipio():
    """Retorna datos de Supatá para auto-completar"""
    from app.utils.contingencia_helpers import get_datos_supata
    return jsonify(get_datos_supata())
```

---

### 3. HELPERS Y UTILIDADES

#### Crear archivo: `app/utils/contingencia_helpers.py`

```python
"""Funciones auxiliares para planes de contingencia"""

def get_datos_supata():
    """Datos del municipio para auto-población"""
    return {
        "municipio": "Supatá",
        "departamento": "Cundinamarca",
        "provincia": "Gualivá",
        "poblacion": 6428,
        "altitud": 1798,
        "area_km2": 128,
        "distancia_bogota_km": 76,
        "clima": "Templado",
        "fundacion": "13 de diciembre de 1882",
        "coordenadas": {
            "latitud": "5°03'40\"N",
            "longitud": "74°14'12\"O"
        },
        "organismos_emergencia": [
            {
                "nombre": "Bomberos Voluntarios de Supatá",
                "telefono": "119",
                "direccion": "[Dirección a completar]",
                "tipo": "bomberos"
            },
            {
                "nombre": "Policía Nacional - CAI Supatá",
                "telefono": "123",
                "direccion": "[Dirección a completar]",
                "tipo": "policia"
            },
            {
                "nombre": "Hospital Municipal de Supatá",
                "telefono": "[Completar]",
                "direccion": "[Dirección a completar]",
                "tipo": "salud"
            },
            {
                "nombre": "Unidad Municipal de Gestión del Riesgo (UMGRD)",
                "telefono": "[Completar]",
                "direccion": "Alcaldía Municipal",
                "tipo": "gestion_riesgo"
            },
            {
                "nombre": "Cruz Roja Colombiana - Seccional",
                "telefono": "132",
                "direccion": "[Dirección a completar]",
                "tipo": "salud"
            },
            {
                "nombre": "Defensa Civil Colombiana",
                "telefono": "144",
                "direccion": "[Dirección a completar]",
                "tipo": "defensa_civil"
            }
        ],
        "marco_normativo": {
            "ley_1523_2012": "Política Nacional de Gestión del Riesgo de Desastres",
            "decreto_2157_2017": "Directrices para elaboración de planes de GRD",
            "estrategia_municipal": "Estrategia Municipal de Respuesta a Emergencias (EMRE)",
            "cmgrd": "Comité Municipal de Gestión del Riesgo de Desastres"
        }
    }

def get_plantilla_por_tipo(tipo_evento, seccion):
    """Retorna contenido pre-configurado según tipo de evento"""
    from app.models.plan_contingencia import PlantillaContingencia
    
    plantilla = PlantillaContingencia.query.filter_by(
        tipo_evento=tipo_evento,
        seccion=seccion,
        activo=True
    ).first()
    
    if plantilla:
        return plantilla.contenido_json
    
    # Plantillas por defecto si no existe en BD
    plantillas_default = {
        "lluvias": {
            "riesgos": {
                "amenazas_naturales": [
                    "Lluvias torrenciales",
                    "Inundaciones repentinas",
                    "Deslizamientos de tierra",
                    "Tormentas eléctricas"
                ],
                "amenazas_tecnologicas": [
                    "Colapso de estructuras temporales por agua",
                    "Cortocircuitos eléctricos"
                ]
            },
            "medidas": [
                "Monitoreo permanente de pronósticos del IDEAM",
                "Impermeabilización de zonas críticas",
                "Sistemas de drenaje funcionales",
                "Plan de evacuación rápida"
            ]
        },
        "incendios": {
            "riesgos": {
                "amenazas_tecnologicas": [
                    "Incendio estructural",
                    "Cortocircuitos eléctricos",
                    "Explosión de gas o combustibles"
                ],
                "amenazas_antropicas": [
                    "Uso indebido de llama abierta",
                    "Acumulación de material inflamable"
                ]
            },
            "medidas": [
                "Extintores tipo ABC en puntos estratégicos",
                "Prohibición estricta de fumar",
                "Personal capacitado en control de incendios",
                "Coordinación con Bomberos"
            ]
        },
        "eventos_masivos": {
            "riesgos": {
                "amenazas_antropicas": [
                    "Estampidas por pánico",
                    "Aglomeraciones peligrosas",
                    "Disturbios públicos",
                    "Emergencias médicas masivas"
                ]
            },
            "medidas": [
                "Control estricto de aforo",
                "Personal de seguridad visible",
                "Rutas de evacuación demarcadas",
                "Puesto médico avanzado (PMA)"
            ]
        }
    }
    
    return plantillas_default.get(tipo_evento, {}).get(seccion, {})
```

---

### 4. TEMPLATES (VISTAS)

#### A) `templates/contingencia_editar_wizard.html` (NUEVO)

**Wizard de 9 pasos con navegación por secciones:**

```html
<!-- Estructura de wizard con tabs laterales -->
<div class="wizard-container">
    <aside class="wizard-nav">
        <ul>
            <li class="{{ 'active' if seccion_actual == 'introduccion' }}">
                <a href="{{ url_for('contingencia_views.editar', id=plan.id, seccion='introduccion') }}">
                    1. Introducción
                </a>
            </li>
            <li class="{{ 'active' if seccion_actual == 'objetivos' }}">
                <a href="{{ url_for('contingencia_views.editar', id=plan.id, seccion='objetivos') }}">
                    2. Objetivos y Alcance
                </a>
            </li>
            <!-- ... 7 secciones más ... -->
        </ul>
    </aside>
    
    <main class="wizard-content">
        <!-- Panel de auto-completar con datos de Supatá -->
        <div class="datos-municipio-panel">
            <button onclick="autoRellenarMunicipio()">
                📍 Auto-completar datos de Supatá
            </button>
        </div>
        
        <!-- Formulario según sección actual -->
        {% if seccion_actual == 'introduccion' %}
            {% include 'contingencia_form_introduccion.html' %}
        {% elif seccion_actual == 'objetivos' %}
            {% include 'contingencia_form_objetivos.html' %}
        <!-- ... etc ... -->
        {% endif %}
        
        <!-- Botones navegación -->
        <div class="wizard-actions">
            <button onclick="guardarYAnterior()">← Anterior</button>
            <button onclick="guardarSeccion()">💾 Guardar</button>
            <button onclick="guardarYSiguiente()">Siguiente →</button>
        </div>
    </main>
</div>

<script>
// Datos del municipio disponibles para auto-completar
const datosMunicipio = {{ datos_municipio | tojson }};

function autoRellenarMunicipio() {
    // Rellenar campos automáticamente
    document.getElementById('municipio').value = datosMunicipio.municipio;
    document.getElementById('departamento').value = datosMunicipio.departamento;
    // ... etc
    
    // Rellenar tabla de organismos de emergencia
    rellenarOrganismosEmergencia(datosMunicipio.organismos_emergencia);
}

function guardarSeccion() {
    // Recopilar datos del formulario
    const formData = new FormData(document.getElementById('form-seccion'));
    const data = Object.fromEntries(formData.entries());
    
    // Enviar a API
    fetch(`/api/contingencia/{{ plan.id }}/seccion/{{ seccion_actual }}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            mostrarNotificacion('✅ Sección guardada');
        }
    });
}
</script>
```

#### B) `templates/contingencia_detalle.html` (NUEVO)

Vista de solo lectura con todas las secciones expandibles:

```html
<div class="plan-detalle">
    <header>
        <h1>{{ plan.tipo_evento | upper }} - {{ plan.evento_nombre }}</h1>
        <span class="badge badge-{{ plan.estado }}">{{ plan.estado | upper }}</span>
    </header>
    
    <!-- Acordeón de secciones -->
    <div class="accordion">
        <div class="accordion-item">
            <h2 class="accordion-header">1. Introducción</h2>
            <div class="accordion-content">
                <p><strong>Descripción del evento:</strong><br>{{ plan.descripcion_evento }}</p>
                <p><strong>Justificación:</strong><br>{{ plan.justificacion }}</p>
            </div>
        </div>
        
        <div class="accordion-item">
            <h2 class="accordion-header">2. Objetivos y Alcance</h2>
            <div class="accordion-content">
                <p><strong>Objetivo General:</strong><br>{{ plan.objetivo_general }}</p>
                <p><strong>Objetivos Específicos:</strong></p>
                <ul>
                    {% for obj in plan.objetivos_especificos %}
                    <li>{{ obj }}</li>
                    {% endfor %}
                </ul>
                <p><strong>Evento:</strong> {{ plan.evento_nombre }}</p>
                <p><strong>Fecha:</strong> {{ plan.evento_fecha_inicio | format_date }} - {{ plan.evento_fecha_fin | format_date }}</p>
                <p><strong>Ubicación:</strong> {{ plan.evento_ubicacion }}</p>
                <p><strong>Aforo:</strong> {{ plan.evento_aforo }} personas</p>
            </div>
        </div>
        
        <!-- ... 7 secciones más ... -->
        
        <div class="accordion-item">
            <h2 class="accordion-header">5. Análisis de Riesgos</h2>
            <div class="accordion-content">
                <!-- Tabla matriz de riesgos -->
                <table class="tabla-riesgos">
                    <thead>
                        <tr>
                            <th>Amenaza</th>
                            <th>Probabilidad</th>
                            <th>Impacto</th>
                            <th>Nivel de Riesgo</th>
                            <th>Medidas</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for riesgo in plan.matriz_riesgos %}
                        <tr>
                            <td>{{ riesgo.amenaza }}</td>
                            <td>{{ riesgo.probabilidad }}</td>
                            <td>{{ riesgo.impacto }}</td>
                            <td>
                                <span class="badge badge-riesgo-{{ riesgo.nivel | lower }}">
                                    {{ riesgo.nivel }}
                                </span>
                            </td>
                            <td>{{ riesgo.medidas }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <!-- Botones de acción -->
    <div class="detalle-actions">
        <button onclick="descargarPDF()">📄 Descargar PDF</button>
        {% if plan.estado in ['borrador', 'en_revision'] %}
        <a href="{{ url_for('contingencia_views.editar', id=plan.id) }}" class="btn btn-editar">
            ✏️ Editar Plan
        </a>
        {% endif %}
        <a href="{{ url_for('contingencia_views.index') }}" class="btn btn-secondary">
            ← Volver a lista
        </a>
    </div>
</div>
```

---

### 5. ACTUALIZAR GENERADOR DE PDF

#### Modificar `app/utils/pdf_plans_generator.py`

```python
class PDFPlanContingenciaOficial:
    """Generador de PDF con estructura exacta del formato Word oficial"""
    
    def __init__(self, plan):
        self.plan = plan
        self.buffer = BytesIO()
        self.doc = SimpleDocTemplate(self.buffer, pagesize=letter)
        self.elements = []
        self.styles = getSampleStyleSheet()
        self._configurar_estilos()
    
    def generar(self):
        """Generar PDF completo con las 9 secciones"""
        # Portada moderna con colores
        self._crear_portada_moderna()
        
        # Sección 1: Introducción
        self._crear_seccion_introduccion()
        
        # Sección 2: Objetivos y Alcance
        self._crear_seccion_objetivos()
        
        # Sección 3: Marco Normativo
        self._crear_seccion_normativo()
        
        # Sección 4: Organización (con TABLA 1)
        self._crear_seccion_organizacion()
        
        # Sección 5: Análisis de Riesgos (con TABLA 2)
        self._crear_seccion_riesgos()
        
        # Sección 6: Medidas de Reducción
        self._crear_seccion_medidas()
        
        # Sección 7: Plan de Respuesta (9 subsecciones)
        self._crear_seccion_respuesta()
        
        # Sección 8: Actualización
        self._crear_seccion_actualizacion()
        
        # Sección 9: Anexos
        self._crear_seccion_anexos()
        
        # Construir documento
        self.doc.build(self.elements)
        
        # Overlay con FORMATO.pdf (mantener formato oficial)
        return self._aplicar_overlay()
    
    def _crear_seccion_organizacion(self):
        """Sección 4 con tabla de roles y responsabilidades"""
        self.elements.append(Paragraph("4. ORGANIZACIÓN, ROLES Y RESPONSABILIDADES", self.styles['Heading1']))
        
        # Texto introductorio
        intro = f"""
        La estructura organizativa del plan de contingencia para <b>{self.plan.evento_nombre}</b>
        se establece conforme a los lineamientos del Sistema Nacional de Gestión del Riesgo,
        integrando coordinación interna con organismos de socorro del municipio de Supatá.
        """
        self.elements.append(Paragraph(intro, self.styles['Normal']))
        self.elements.append(Spacer(1, 0.2*inch))
        
        # TABLA 1: Roles y Responsabilidades (del Word)
        tabla_data = [
            ['Cargo/Responsable', 'Nombre', 'Funciones Principales']
        ]
        
        for coord in self.plan.coordinadores:
            funciones = '\n'.join(coord.get('funciones', []))
            tabla_data.append([
                Paragraph(coord['cargo'], self.styles['TableCell']),
                Paragraph(coord['nombre'], self.styles['TableCell']),
                Paragraph(funciones, self.styles['TableCellSmall'])
            ])
        
        tabla = Table(tabla_data, colWidths=[2*inch, 1.5*inch, 3*inch])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        self.elements.append(tabla)
        self.elements.append(PageBreak())
    
    def _crear_seccion_riesgos(self):
        """Sección 5 con matriz de riesgos (TABLA 2)"""
        self.elements.append(Paragraph("5. IDENTIFICACIÓN DE AMENAZAS Y ANÁLISIS DE RIESGOS", self.styles['Heading1']))
        
        # Descripción del escenario
        self.elements.append(Paragraph(self.plan.escenario_caracteristicas or "", self.styles['Normal']))
        self.elements.append(Spacer(1, 0.2*inch))
        
        # TABLA 2: Matriz de Riesgos (del Word)
        tabla_data = [
            ['Amenaza/Riesgo', 'Probabilidad', 'Impacto', 'Nivel de Riesgo', 'Medidas de Control']
        ]
        
        colores_riesgo = {
            'bajo': colors.green,
            'medio': colors.yellow,
            'alto': colors.orange,
            'critico': colors.red
        }
        
        for riesgo in self.plan.matriz_riesgos:
            nivel_color = colores_riesgo.get(riesgo['nivel'].lower(), colors.grey)
            tabla_data.append([
                Paragraph(riesgo['amenaza'], self.styles['TableCellSmall']),
                Paragraph(riesgo['probabilidad'], self.styles['TableCell']),
                Paragraph(riesgo['impacto'], self.styles['TableCell']),
                Paragraph(f"<b>{riesgo['nivel']}</b>", self.styles['TableCell']),
                Paragraph(riesgo['medidas'], self.styles['TableCellSmall'])
            ])
        
        tabla = Table(tabla_data, colWidths=[2*inch, 1*inch, 1*inch, 1.2*inch, 2.3*inch])
        # ... (estilos de tabla)
        
        self.elements.append(tabla)
        self.elements.append(PageBreak())
```

---

### 6. VENTANAS AUTOMATIZADAS

#### JavaScript en templates para auto-completar

```javascript
// En contingencia_editar_wizard.html

class VentanaAutomatizada {
    constructor(tipo, datos) {
        this.tipo = tipo;
        this.datos = datos;
    }
    
    mostrar() {
        const ventana = document.createElement('div');
        ventana.className = 'ventana-automatizada';
        ventana.innerHTML = this.generarContenido();
        document.body.appendChild(ventana);
    }
    
    generarContenido() {
        switch(this.tipo) {
            case 'municipio':
                return `
                    <div class="ventana-header">
                        <h3>📍 Datos del Municipio de Supatá</h3>
                        <button onclick="this.parentElement.parentElement.remove()">×</button>
                    </div>
                    <div class="ventana-body">
                        <table class="tabla-datos-municipio">
                            <tr><td>Municipio:</td><td><b>${this.datos.municipio}</b></td></tr>
                            <tr><td>Departamento:</td><td>${this.datos.departamento}</td></tr>
                            <tr><td>Provincia:</td><td>${this.datos.provincia}</td></tr>
                            <tr><td>Población:</td><td>${this.datos.poblacion.toLocaleString()} habitantes</td></tr>
                            <tr><td>Altitud:</td><td>${this.datos.altitud} msnm</td></tr>
                            <tr><td>Área:</td><td>${this.datos.area_km2} km²</td></tr>
                            <tr><td>Distancia Bogotá:</td><td>${this.datos.distancia_bogota_km} km</td></tr>
                            <tr><td>Clima:</td><td>${this.datos.clima}</td></tr>
                        </table>
                        <button class="btn-aplicar" onclick="aplicarDatosMunicipio()">
                            ✅ Aplicar estos datos al formulario
                        </button>
                    </div>
                `;
            
            case 'organismos':
                return `
                    <div class="ventana-header">
                        <h3>🚨 Organismos de Emergencia de Supatá</h3>
                        <button onclick="this.parentElement.parentElement.remove()">×</button>
                    </div>
                    <div class="ventana-body">
                        <p>Seleccione los organismos que participarán en el plan:</p>
                        <div class="lista-organismos">
                            ${this.datos.organismos_emergencia.map((org, idx) => `
                                <label class="organismo-item">
                                    <input type="checkbox" value="${idx}" checked>
                                    <div class="organismo-info">
                                        <strong>${org.nombre}</strong>
                                        <span class="tipo-badge">${org.tipo}</span>
                                        <small>Tel: ${org.telefono}</small>
                                    </div>
                                </label>
                            `).join('')}
                        </div>
                        <button class="btn-aplicar" onclick="aplicarOrganismos()">
                            ✅ Agregar organismos seleccionados
                        </button>
                    </div>
                `;
            
            case 'plantilla':
                return `
                    <div class="ventana-header">
                        <h3>📋 Plantilla: ${this.datos.tipo_evento}</h3>
                        <button onclick="this.parentElement.parentElement.remove()">×</button>
                    </div>
                    <div class="ventana-body">
                        <p>Cargar contenido pre-configurado para eventos de tipo <b>${this.datos.tipo_evento}</b>:</p>
                        <div class="plantilla-preview">
                            <h4>Amenazas identificadas:</h4>
                            <ul>
                                ${this.datos.amenazas.map(a => `<li>${a}</li>`).join('')}
                            </ul>
                            <h4>Medidas sugeridas:</h4>
                            <ul>
                                ${this.datos.medidas.map(m => `<li>${m}</li>`).join('')}
                            </ul>
                        </div>
                        <button class="btn-aplicar" onclick="aplicarPlantilla()">
                            ✅ Cargar esta plantilla
                        </button>
                    </div>
                `;
        }
    }
}

// Funciones de aplicación
function mostrarVentanaMunicipio() {
    fetch('/api/contingencia/datos-municipio')
        .then(res => res.json())
        .then(datos => {
            const ventana = new VentanaAutomatizada('municipio', datos);
            ventana.mostrar();
        });
}

function mostrarVentanaOrganismos() {
    fetch('/api/contingencia/datos-municipio')
        .then(res => res.json())
        .then(datos => {
            const ventana = new VentanaAutomatizada('organismos', datos);
            ventana.mostrar();
        });
}

function mostrarVentanaPlantilla(tipoEvento, seccion) {
    fetch(`/api/contingencia/plantilla/${tipoEvento}/${seccion}`)
        .then(res => res.json())
        .then(datos => {
            const ventana = new VentanaAutomatizada('plantilla', datos);
            ventana.mostrar();
        });
}
```

---

## 📦 MIGRACIÓN DE DATOS

### Script de migración para planes existentes:

```python
# migrations/upgrade_planes_contingencia_v2.py

from app import db
from app.models.plan_contingencia import PlanContingencia
from app.utils.contingencia_helpers import get_datos_supata

def upgrade():
    """Migrar planes existentes al nuevo formato"""
    planes = PlanContingencia.query.all()
    datos_supata = get_datos_supata()
    
    for plan in planes:
        # Auto-poblar con datos de Supatá
        plan.municipio_datos = datos_supata
        
        # Migrar campos simples a estructura compleja
        if plan.descripcion:
            plan.descripcion_evento = plan.descripcion
        
        if plan.ubicacion:
            plan.evento_ubicacion = plan.ubicacion
        
        # Inicializar arrays vacíos para nuevos campos
        plan.objetivos_especificos = []
        plan.coordinadores = []
        plan.organismos_apoyo = datos_supata['organismos_emergencia']  # Pre-poblar
        plan.matriz_riesgos = []
        plan.medidas_seguridad = []
        
    db.session.commit()
    print(f"✅ Migrados {len(planes)} planes al nuevo formato")

if __name__ == '__main__':
    upgrade()
```

---

## 🎯 RESUMEN DE MEJORAS

### ✅ Problemas Resueltos:

1. **Rutas faltantes**: Creadas `/editar/{id}` y `/detalle/{id}`
2. **Modelo expandido**: 30+ campos nuevos en modelo `PlanContingencia`
3. **Estructura oficial**: Replica exacta del Word con 9 secciones y 3 tablas
4. **Auto-población**: Datos de Supatá pre-cargados automáticamente
5. **Edición por secciones**: Wizard de 9 pasos con guardado independiente
6. **Ventanas automatizadas**: Paneles emergentes con datos pre-configurados
7. **PDF mejorado**: Genera PDF exacto del formato Word oficial
8. **Plantillas por tipo**: Contenido pre-configurado según tipo de evento

### 🚀 Funcionalidades Nuevas:

- **Auto-completar municipio**: Botón para rellenar automáticamente datos de Supatá
- **Organismos pre-cargados**: Lista de bomberos, policía, hospital, UMGRD
- **Plantillas inteligentes**: Amenazas y medidas según tipo de evento
- **Matriz de riesgos visual**: Tabla interactiva con código de colores
- **Directorio de emergencias**: Auto-poblado con contactos locales
- **Vista de solo lectura**: Acordeón expandible con todas las secciones
- **Validación por sección**: Guardar progreso parcial
- **Marco normativo incluido**: Ley 1523, Decreto 2157 pre-cargados

---

## 📝 PRÓXIMOS PASOS

1. ✅ **Aprobar propuesta** (usuario confirma diseño)
2. Crear migración de base de datos (agregar columnas nuevas)
3. Implementar routes `contingencia_views.py`
4. Crear templates wizard y detalle
5. Actualizar API con endpoints de sección
6. Crear helpers con datos de Supatá
7. Actualizar generador PDF
8. Poblar tabla de plantillas
9. Migrar datos existentes
10. Testing completo

---

## 💡 NOTAS TÉCNICAS

- **JSON Fields**: Usar `db.JSON` para arrays y objetos complejos (requiere PostgreSQL o SQLite 3.9+)
- **Migraciones**: Usar Alembic para cambios en BD
- **Validación**: Implementar validadores Marshmallow para cada sección
- **Performance**: Índice en `tipo_evento` y `estado` para búsquedas rápidas
- **Seguridad**: Solo usuarios autorizados pueden crear/editar planes
- **Backup**: Guardar snapshot del plan antes de cada cambio mayor

---

**¿Proceder con la implementación de esta propuesta?**
