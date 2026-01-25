# 📋 NUEVO MÓDULO DE PLANES DE CONTINGENCIA V2
## ✅ COMPLETADO - Estructura Oficial + Diseño iOS Moderno

---

## 🎯 RESUMEN DE CAMBIOS

Se ha rediseñado **completamente** el módulo de planes de contingencia basándose en:
- ✅ Estructura oficial del Word template (9 secciones)
- ✅ Auto-población de datos de Supatá (población, altitud, clima, organismos)
- ✅ Normas APPA actualizadas
- ✅ Diseño iOS 26 iPhone moderno

---

## 📁 ARCHIVOS CREADOS/MODIFICADOS

### **MODELOS DE DATOS**
1. **`app/models/plan_contingencia_v2.py`** ✅
   - Modelo SQLAlchemy con 50+ campos
   - 9 secciones mapeadas según Word template
   - JSON columns para datos dinámicos (matrices, tablas)
   - Auto-población con datos de Supatá
   - Tabla: `planes_contingencia_v2`

### **UTILIDADES**
2. **`app/utils/supata_data.py`** ✅
   - Diccionario SUPATA_DATA con 30+ campos
   - Población: 6,428 habitantes
   - Altitud: 1,798 m.s.n.m.
   - Clima: Bosque húmedo premontano
   - 6 organismos de emergencia pre-configurados
   - 3 funciones auxiliares para acceso a datos

### **RUTAS/VISTAS**
3. **`app/routes/plan_contingencia_v2_routes.py`** ✅
   - Blueprint: `contingencia_bp` (prefijo: `/gestion-riesgo`)
   - Rutas implementadas:
     - `GET /planes-contingencia-v2` → Listar planes
     - `GET /planes-contingencia-v2/crear` → Formulario crear
     - `POST /planes-contingencia-v2/crear` → Guardar nuevo
     - `GET /planes-contingencia-v2/<id>` → Ver detalle
     - `GET /planes-contingencia-v2/editar/<id>/<seccion>` → Editar sección
     - `POST /planes-contingencia-v2/<id>/publicar` → Publicar plan
     - `POST /planes-contingencia-v2/<id>/eliminar` → Eliminar plan
     - `GET /api/contingencia/<id>/progreso` → API progreso
     - `GET /api/supata/info` → API datos municipio
     - `GET /api/supata/directorio` → API directorio emergencias

### **TEMPLATES**
4. **`templates/plan_contingencia_crear.html`** ✅
   - Formulario multi-sección con tabs iOS modernos
   - Datos de Supatá pre-poblados (cards automáticas)
   - 9 secciones navegables
   - Barra de progreso dinámico
   - Diseño iOS 26 con colores verdes naturales

5. **`templates/plan_contingencia_lista.html`** ✅
   - Listado de planes creados
   - Tarjetas con información resumida
   - Barra de progreso para cada plan
   - Paginación
   - Botones: Editar, Ver, Eliminar
   - Estado vacío cuando no hay planes

6. **`templates/plan_contingencia_detalle.html`** ✅
   - Visualización completa del plan
   - 9 secciones navegables con tabs
   - Datos de Supatá desplegados
   - Tabla de directorio de emergencias
   - Botones: Volver, Editar, Publicar

7. **`templates/plan_contingencia_editar.html`** ✅
   - Formulario de edición de secciones específicas
   - Validación de campos obligatorios
   - Botones: Guardar, Cancelar

### **REGISTROS**
8. **`app/__init__.py`** ✅ (Actualizado)
   - Importado: `from .routes.plan_contingencia_v2_routes import contingencia_bp`
   - Registrado: `app.register_blueprint(contingencia_bp)`

### **BASE DE DATOS**
9. **Tabla `planes_contingencia_v2`** ✅ (Creada)
   - Campo: municipio (default: 'Supatá')
   - Campo: poblacion_municipio (default: 6428)
   - Campo: altitud_municipio (default: 1798)
   - Campo: clima_municipio (default: 'Bosque húmedo premontano')
   - 50+ columnas para todos los campos requeridos
   - Índices: numero_plan, estado, municipio, fecha_creacion

---

## 🏗️ ESTRUCTURA DE DATOS

### **9 Secciones del Plan**
```
1. INTRODUCCIÓN
   └─ Descripción, justificación, contexto

2. OBJETIVOS Y ALCANCE
   └─ Objetivo general, específicos, ubicación, aforo

3. MARCO NORMATIVO
   └─ Leyes (1523, Decreto 2157), normas APPA

4. ORGANIZACIÓN Y ROLES
   └─ Coordinadores, PMU, organismos de apoyo, directorio

5. AMENAZAS Y RIESGOS
   └─ Escenario, amenazas, vulnerabilidades, matriz riesgos

6. MEDIDAS DE REDUCCIÓN
   └─ Seguridad, adecuación, sanitarias, vigilancia, capacitación

7. PLAN DE RESPUESTA
   └─ Procedimientos, evacuación, médico, logística, comunicaciones

8. ACTUALIZACIÓN Y MEJORA
   └─ Responsable, frecuencia, simulacros, capacitaciones

9. ANEXOS TÉCNICOS
   └─ Documentos, planos, inventarios, observaciones
```

### **Auto-Población de Supatá**
```
SUPATA_DATA {
  "poblacion_total": 6428,
  "poblacion_urbana": 2533,
  "poblacion_rural": 3895,
  "altitud": 1798,
  "clima_tipo": "Bosque húmedo premontano",
  "temperatura_promedio": "12-16°C",
  "organismos_emergencia": [
    {"nombre": "Bomberos", "telefono": "119"},
    {"nombre": "Cruz Roja", "telefono": "01800 5198534"},
    {"nombre": "Policía", "telefono": "123"},
    ...
  ]
}
```

---

## 🎨 DISEÑO iOS 26 IMPLEMENTADO

### **Características de Diseño**
- ✅ Tipografía: -apple-system (San Francisco)
- ✅ Colores: Verde naturaleza (#2d5016, #5a8a3a)
- ✅ Bordes redondeados: 16-20px (suave, moderno)
- ✅ Sombras: sutiles (0 2px 8px, 0 4px 12px)
- ✅ Espaciado: generoso y consistente
- ✅ Transiciones: 0.3s ease para todas las interacciones
- ✅ Iconos: Emoji (📋, ✓, ← →, etc.)
- ✅ Tabs navegables: smooth animations

### **Componentes iOS**
- Cards con bordes redondeados
- Botones con gradientes sutiles
- Barras de progreso animadas
- Badges de estado (PUBLICADO, BORRADOR, EN_EDICIÓN)
- Formularios con validación visual
- Tablas con hover effects

---

## 🚀 CÓMO USAR

### **1. Crear un Plan de Contingencia**
```
1. Ir a: /gestion-riesgo/planes-contingencia-v2/crear
2. Completar datos en 9 secciones
3. Datos de Supatá se cargan automáticamente
4. Hacer clic "Crear Plan de Contingencia"
```

### **2. Ver Planes Existentes**
```
1. Ir a: /gestion-riesgo/planes-contingencia-v2
2. Ver lista de planes con progreso
3. Hacer clic en "Ver" para detalle
```

### **3. Editar un Plan**
```
1. En lista: clic "Editar"
2. O en detalle: clic "Editar Plan"
3. Seleccionar sección a editar
4. Actualizar información
5. Guardar cambios
```

### **4. Publicar un Plan**
```
1. Ir a detalle del plan
2. Verificar todas las secciones completadas
3. Hacer clic "Publicar Plan"
4. Estado cambia a PUBLICADO
```

---

## 🔗 RUTAS DISPONIBLES

### **Web**
- `/gestion-riesgo/planes-contingencia-v2` → Listado
- `/gestion-riesgo/planes-contingencia-v2/crear` → Crear
- `/gestion-riesgo/planes-contingencia-v2/<id>` → Ver detalle
- `/gestion-riesgo/planes-contingencia-v2/editar/<id>/<seccion>` → Editar

### **API**
- `/api/contingencia/<id>/progreso` → JSON progreso
- `/api/supata/info` → JSON datos Supatá
- `/api/supata/directorio` → JSON organismos emergencia

---

## 📊 CAMPOS DE DATOS

### **Campos de Entrada (Textos)**
- introduccion_descripcion (textarea)
- introduccion_justificacion (textarea)
- introduccion_contexto (textarea)
- objetivo_general (textarea)
- alcance_evento (textarea)
- alcance_ubicacion (texto)
- alcance_duracion (texto)
- alcance_aforo (número)
- marco_normativo (textarea)
- coordinador_general (texto)
- pmu_ubicacion (texto)
- organismos_apoyo (textarea)
- descripcion_escenario (textarea)
- amenazas_identificadas (textarea)
- vulnerabilidades (textarea)
- medidas_seguridad (textarea)
- adecuacion_lugar (textarea)
- capacitacion_personal (textarea)
- procedimiento_general (textarea)
- rutas_evacuacion (textarea)
- puntos_encuentro (textarea)
- capacidad_rutas (texto)
- recursos_disponibles (textarea)
- responsable_actualizacion (texto)
- frecuencia_actualizacion (select)
- observaciones (textarea)

### **Campos de Datos Automáticos (Supatá)**
- municipio = 'Supatá'
- poblacion_municipio = 6428
- altitud_municipio = 1798
- clima_municipio = 'Bosque húmedo premontano'
- temperatura_municipio = '12-16°C'

### **Campos de Auditoría**
- creado_por (username del usuario)
- fecha_creacion (timestamp automático)
- ultima_modificacion_por (username)
- fecha_ultima_actualizacion (timestamp automático)

---

## ✅ ESTADO DEL PROYECTO

| Tarea | Estado |
|-------|--------|
| Modelo de datos | ✅ COMPLETO |
| Datos de Supatá | ✅ COMPLETO |
| Rutas/Vistas | ✅ COMPLETO |
| Templates crear | ✅ COMPLETO |
| Templates listar | ✅ COMPLETO |
| Templates detalle | ✅ COMPLETO |
| Templates editar | ✅ COMPLETO |
| Base de datos creada | ✅ COMPLETO |
| Servidor ejecutando | ✅ RUNNING |
| Diseño iOS moderno | ✅ IMPLEMENTADO |
| Auto-población Supatá | ✅ FUNCIONANDO |
| API endpoints | ✅ FUNCIONALES |

---

## 🔧 NOTAS TÉCNICAS

### **Dependencias**
- Flask-SQLAlchemy (ORM)
- Flask-Login (autenticación)
- SQLAlchemy JSON types (para columnas dinámicas)
- Jinja2 (templates)

### **Base de Datos**
- SQLite (development) o PostgreSQL (production)
- Tabla: `planes_contingencia_v2`
- Indices en: numero_plan, estado, municipio, fecha_creacion

### **Validación**
- Campos obligatorios marcados con *
- Validación frontend en formularios
- Validación backend en rutas

### **Seguridad**
- Todas las rutas requieren login (@login_required)
- CSRF protection en formularios
- Auditoría: creado_por, ultima_modificacion_por

---

## 🎯 PRÓXIMAS MEJORAS (Opcionales)

- [ ] Generación de PDF desde el plan
- [ ] Exportar a formato Word/Excel
- [ ] Versionamiento automático
- [ ] Comentarios/notas en secciones
- [ ] Búsqueda avanzada de planes
- [ ] Filtros por estado/municipio/fecha
- [ ] Historial de cambios
- [ ] Aprobación/revisión de planes
- [ ] Integración con eventos masivos (calendario)
- [ ] Recordatorios de actualización

---

## 📞 SOPORTE

Si hay problemas:
1. Revisar logs del servidor (`run.py` en terminal)
2. Verificar que flask-login está instalado
3. Confirmar que la tabla se creó: `SELECT * FROM planes_contingencia_v2;`
4. Revisar que las rutas se registraron en `app/__init__.py`

---

**Creado**: 2026
**Versión**: 1.0
**Estado**: ✅ PRODUCCIÓN LISTA
