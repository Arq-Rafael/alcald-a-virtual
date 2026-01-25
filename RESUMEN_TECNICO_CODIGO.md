# 📝 RESUMEN TÉCNICO: CÓDIGO AGREGADO

## 📂 Archivos Modificados

### 1. `templates/riesgo_planes_contingencia.html`
**Líneas agregadas: ~80 líneas**

#### A. Botón "Secciones" en los estados BORRADOR y EN REVISIÓN
```html
<!-- ANTES (solo 4 botones): -->
<button class="btn-ios btn-pdf" onclick="descargarPDF(${plan.id})">PDF</button>
<button class="btn-ios btn-editar" onclick="editarPlan(${plan.id})">✎</button>
<button class="btn-ios btn-enviar" onclick="...">Revisar</button>
<button class="btn-ios btn-eliminar" onclick="...">✕</button>

<!-- DESPUÉS (5 botones con nuevo): -->
<button class="btn-ios btn-pdf" onclick="descargarPDF(${plan.id})">PDF</button>
<button class="btn-ios btn-editar" onclick="editarPlan(${plan.id})">✎</button>
<button class="btn-ios btn-secciones" onclick="mostrarMenuSecciones(${plan.id})">📋</button> ← NUEVO
<button class="btn-ios btn-enviar" onclick="...">Revisar</button>
<button class="btn-ios btn-eliminar" onclick="...">✕</button>
```

#### B. Botón "Secciones" en estado APROBADO
```html
<!-- ANTES: -->
<button class="btn-ios btn-pdf" onclick="descargarPDF(${plan.id})">PDF</button>
<button class="btn-ios btn-ver" onclick="verDetalle(${plan.id})">👁</button>
<button class="btn-ios btn-comite" onclick="...">Comité</button>

<!-- DESPUÉS: -->
<button class="btn-ios btn-pdf" onclick="descargarPDF(${plan.id})">PDF</button>
<button class="btn-ios btn-ver" onclick="verDetalle(${plan.id})">👁</button>
<button class="btn-ios btn-secciones" onclick="mostrarMenuSecciones(${plan.id})">📋</button> ← NUEVO
<button class="btn-ios btn-comite" onclick="...">Comité</button>
```

#### C. CSS para el nuevo botón
```css
.btn-ios.btn-secciones {
  background-color: #6366f1;    /* Morado */
  color: white;
  font-size: 13px;
  padding: 4px 8px;
}
```

#### D. Función JavaScript: mostrarMenuSecciones()
```javascript
function mostrarMenuSecciones(planId) {
  // Define las 9 secciones
  const secciones = [
    { key: 'introduccion', label: '1. Introducción' },
    { key: 'objetivos', label: '2. Objetivos y Alcance' },
    { key: 'normativo', label: '3. Marco Normativo' },
    { key: 'organizacion', label: '4. Organización' },
    { key: 'riesgos', label: '5. Análisis de Riesgos' },
    { key: 'medidas', label: '6. Medidas de Reducción' },
    { key: 'respuesta', label: '7. Plan de Respuesta' },
    { key: 'actualizacion', label: '8. Actualización' },
    { key: 'anexos', label: '9. Anexos' }
  ];
  
  // Crea un modal dinámico con las 9 opciones
  // Cada opción enlaza a: /editar/{planId}/{seccion}
  // Estilo: Modal oscuro con fondo azul claro en bordes
}
```

#### E. Función JavaScript: cerrarModalSecciones()
```javascript
function cerrarModalSecciones(planId) {
  // Busca modal por ID
  // Agrega animación fadeOut (0.3s)
  // Después de 300ms, lo elimina del DOM
}
```

#### F. Animación CSS nueva
```css
@keyframes fadeOut {
  from { opacity: 1; }
  to { opacity: 0; }
}
```

#### G. Incluir script (al final del template)
```html
<script src="{{ url_for('static', filename='js/contingencia_oficial.js') }}"></script>
```

---

### 2. `static/js/contingencia_oficial.js` (NUEVO)
**Líneas totales: 87 líneas**

```javascript
/**
 * Script alternativo para agregar funcionalidad de secciones
 * (Backup en caso de que el código en el template no funcione)
 */

// Intercepta cargarPlanesExistentes() original
const originalCargarPlanesExistentes = window.cargarPlanesExistentes;
window.cargarPlanesExistentes = async function() {
  // Ejecuta la función original
  await originalCargarPlanesExistentes.apply(this, arguments);
  
  // Busca tabla de planes
  const tbody = document.getElementById('planesTbody');
  if (!tbody) return;
  
  // Para cada fila de la tabla:
  // - Extrae el ID del plan
  // - Agrega botón "Secciones" en los botones de acción
};

function mostrarMenuSecciones(planId) {
  // Mismo código que en el template
  // Crea modal, agrega 9 secciones, maneja eventos
}

function cerrarModalSecciones(planId) {
  // Mismo código que en el template
  // Cierra el modal con animación
}
```

---

## 🔄 Cambios de URL/Routing

### Rutas existentes modificadas:
```
GET /riesgo/planes-contingencia
    ↓
    Renderiza: templates/riesgo_planes_contingencia.html
    ✅ CAMBIO: Ahora incluye script contingencia_oficial.js
                Botón "📋" agregado a cada plan
```

### Rutas nuevas (ya existían de antes):
```
GET /gestion-riesgo/planes-contingencia/editar/<id>/<seccion>
    ↓
    Renderiza: templates/contingencia_editar_wizard.html
    Contenido: Wizard con 9 secciones + formularios
    
GET /gestion-riesgo/planes-contingencia/detalle/<id>
    ↓
    Renderiza: templates/contingencia_detalle.html
    Contenido: Vista de solo lectura (acordeón)
```

---

## 📊 Estadísticas de Cambios

| Aspecto | Antes | Después | Cambio |
|---------|-------|---------|--------|
| Botones por plan | 4 | 5 | +1 botón |
| Líneas en template | 1667 | 1747 | +80 líneas |
| Archivos CSS | 1 | 1 | Sin cambios |
| Funciones JS | ~10 | ~12 | +2 funciones |
| Animaciones CSS | 1 | 2 | +1 animación |

---

## 🔗 Referencias de Código

### Flujo de interacción

```
Usuario hace click en [📋]
         ↓
Ejecuta: mostrarMenuSecciones(planId)
         ↓
Crea: <div class="ios-modal">
Agrega: 9 elementos <a> (links a secciones)
Estilo: Modal oscuro (#1e293b, #0f172a)
         ↓
Usuario selecciona sección
         ↓
Redirige a: /editar/{id}/{seccion}
Ejecuta: cerrarModalSecciones(planId)
Animación: fadeOut (300ms)
         ↓
Servidor carga: templates/contingencia_editar_wizard.html
Carga sección: Correspondiente a {seccion}
```

---

## 🎯 Interconexiones

### Entre funciones:

```
editarPlan(id)
  ↓
  window.location.href = `/editar/${id}/introduccion`
  
mostrarMenuSecciones(id)
  ↓
  Crea modal
  Usuario clickea sección
  ↓
  window.location.href = `/editar/${id}/{seccion}`
  
cerrarModalSecciones(id)
  ↓
  Busca #seccionesModal_{id}
  Agrega clase animación fadeOut
  Después 300ms, lo elimina
```

### Entre archivos:

```
HTML template riesgo_planes_contingencia.html
  ├─ Incluye: <script> con mostrarMenuSecciones()
  └─ Incluye: <script src="contingencia_oficial.js">
  
JavaScript contingencia_oficial.js
  ├─ Define: mostrarMenuSecciones() (backup)
  └─ Define: cerrarModalSecciones() (backup)
  
CSS de template
  ├─ .btn-ios.btn-secciones (color morado)
  └─ @keyframes fadeOut (animación)
```

---

## 💾 Guardado de Cambios

**No hay cambios en base de datos en esta actualización.**

Los cambios son:
- ✅ UI (botón, modal)
- ✅ Navegación (links a secciones)
- ✅ Estilos (colores, animaciones)

El almacenamiento de datos (plan_oficial) ya estaba implementado en actualizaciones anteriores.

---

## ✨ Resumen del Código Nuevo

### Mínimo indispensable:
```javascript
// 1 función principal
function mostrarMenuSecciones(planId) {
  // Crea modal con 9 secciones
  // 9 links a: /editar/{id}/{seccion}
}

// 1 función auxiliar
function cerrarModalSecciones(planId) {
  // Cierra y anima modal
}
```

### Estilos mínimos:
```css
.btn-ios.btn-secciones { background: #6366f1; }
@keyframes fadeOut { opacity: 1 → 0; }
```

### HTML mínimo:
```html
<button onclick="mostrarMenuSecciones(${plan.id})">📋</button>
```

---

## 🚀 Próximos Cambios Planeados

(No implementados aún)

### Para guardar datos:
```javascript
// PUT /api/contingencia/{id}/seccion/{seccion}
async function guardarSeccion(seccionName, data) {
  const response = await fetch(`/api/contingencia/${planId}/seccion/${seccionName}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
}
```

### Para auto-completar:
```javascript
// GET /api/contingencia/datos-municipio
async function autocompletarSupata() {
  const datos = await fetch('/api/contingencia/datos-municipio').then(r => r.json());
  // Completa campos con: población, organismos, etc.
}
```

### Para plantillas:
```javascript
// GET /api/contingencia/plantilla/{tipo}/{seccion}
async function cargarPlantilla(tipoEvento, seccion) {
  const template = await fetch(
    `/api/contingencia/plantilla/${tipoEvento}/${seccion}`
  ).then(r => r.json());
  // Pre-llena formulario
}
```

---

**¡Fin del resumen técnico! 🎉**
