## 🚀 GUÍA RÁPIDA - PLANES DE CONTINGENCIA V2

---

## ✅ TODO LO QUE SE HIZO

### **Base de Datos**
- ✅ Tabla `planes_contingencia_v2` creada con 50+ campos
- ✅ Campos de auto-población de Supatá (población, altitud, clima)
- ✅ Auditoría incluida (quién creó, cuándo actualizó)
- ✅ Índices para búsqueda rápida

### **Modelos**
- ✅ `app/models/plan_contingencia_v2.py` (157 líneas)
  - 9 secciones mapeadas
  - Métodos: to_dict(), obtener_progreso()
  - Datos pre-poblados de Supatá

### **Datos de Supatá**
- ✅ `app/utils/supata_data.py` (187 líneas)
  - SUPATA_DATA dictionary con 30+ campos
  - Población: 6,428 habitantes
  - Altitud: 1,798 m.s.n.m.
  - Clima: Bosque húmedo premontano, 12-16°C
  - 6 organismos emergencia (Bomberos, Cruz Roja, Policía, etc.)
  - 3 funciones auxiliares

### **Rutas/Controladores**
- ✅ `app/routes/plan_contingencia_v2_routes.py` (220 líneas)
  - 8 rutas web + 2 API endpoints
  - Login requerido en todas
  - Validación de datos
  - Manejo de errores

### **Templates/Vistas**
- ✅ `templates/plan_contingencia_crear.html`
  - Formulario multi-sección (9 tabs)
  - Cards de datos de Supatá auto-pobladas
  - Barra de progreso dinámica
  - Diseño iOS 26 moderno

- ✅ `templates/plan_contingencia_lista.html`
  - Listado de planes con tarjetas
  - Barra progreso por plan
  - Paginación
  - Botones: Editar, Ver, Eliminar

- ✅ `templates/plan_contingencia_detalle.html`
  - Vista completa del plan
  - 9 secciones navegables
  - Tabla de directorio emergencias
  - Botones: Editar, Publicar, Volver

- ✅ `templates/plan_contingencia_editar.html`
  - Edición de secciones específicas
  - Validación inline
  - Save/Cancel

### **Registros**
- ✅ `app/__init__.py` actualizado
  - Import: `from .routes.plan_contingencia_v2_routes import contingencia_bp`
  - Register: `app.register_blueprint(contingencia_bp)`

### **Servidor**
- ✅ Flask ejecutando correctamente
- ✅ Todas las rutas disponibles
- ✅ Base de datos conectada

---

## 🌐 CÓMO ACCEDER

### **URL Principal**
```
http://localhost:5000/gestion-riesgo/planes-contingencia-v2
```

### **Acciones Disponibles**

1. **Ver Lista de Planes** (vacía al inicio)
   ```
   GET /gestion-riesgo/planes-contingencia-v2
   ```

2. **Crear Nuevo Plan**
   ```
   GET /gestion-riesgo/planes-contingencia-v2/crear
   ```
   - Se llena con datos de Supatá automáticamente
   - Completa las 9 secciones
   - Haz clic "Crear Plan de Contingencia"

3. **Ver Detalle de Plan**
   ```
   GET /gestion-riesgo/planes-contingencia-v2/<ID>
   ```
   - Visualiza todas las secciones
   - Tabla de directorio emergencias
   - Botones: Editar, Publicar

4. **Editar Plan**
   ```
   GET/POST /gestion-riesgo/planes-contingencia-v2/editar/<ID>/<SECCION>
   ```
   - Edita secciones específicas
   - Mantiene otros datos intactos

5. **Publicar Plan**
   ```
   POST /gestion-riesgo/planes-contingencia-v2/<ID>/publicar
   ```
   - Valida campos obligatorios
   - Cambia estado a PUBLICADO

6. **Eliminar Plan**
   ```
   POST /gestion-riesgo/planes-contingencia-v2/<ID>/eliminar
   ```

---

## 📊 DATOS DE SUPATÁ (AUTO-POBLADOS)

Cuando creas un plan, estos datos se cargan automáticamente:

| Campo | Valor |
|-------|-------|
| **Municipio** | Supatá |
| **Departamento** | Cundinamarca |
| **Población** | 6,428 hab (urbana: 2,533 / rural: 3,895) |
| **Altitud** | 1,798 m.s.n.m. |
| **Área** | 128 km² |
| **Clima** | Bosque húmedo premontano |
| **Temperatura** | 12-16°C promedio |
| **Precipitación** | 1,500-2,500 mm anuales |

### **Organismos de Emergencia Pre-configurados**
1. Cuerpo de Bomberos Voluntarios (119)
2. Cruz Roja Colombiana (01800 5198534)
3. Policía Nacional (123)
4. Defensa Civil Cundinamarca
5. Acueducto Municipal (ESPUS)
6. Empresa de Energía (Electrohuila)

---

## 🎨 DISEÑO iOS 26

- ✅ Tipografía: San Francisco (-apple-system)
- ✅ Colores: Verde naturaleza (#2d5016, #5a8a3a)
- ✅ Bordes redondeados: 16-20px (moderno)
- ✅ Sombras: sutiles y consistentes
- ✅ Espaciado: generoso
- ✅ Transiciones: smooth 0.3s
- ✅ Iconos: Emoji para accesibilidad
- ✅ Responsive: funciona en móvil/tablet

---

## 📋 ESTRUCTURA DEL PLAN (9 Secciones)

```
1️⃣ INTRODUCCIÓN
   └─ Descripción evento, justificación, contexto

2️⃣ OBJETIVOS Y ALCANCE
   └─ Objetivos general/específicos, ubicación, aforo

3️⃣ MARCO NORMATIVO
   └─ Referencias a Ley 1523, Decreto 2157, APPA

4️⃣ ORGANIZACIÓN Y ROLES
   └─ Coordinadores, PMU, organismos apoyo, directorio

5️⃣ AMENAZAS Y RIESGOS
   └─ Escenario, amenazas, vulnerabilidades, matriz

6️⃣ MEDIDAS DE REDUCCIÓN
   └─ Seguridad, adecuación, sanitarias, vigilancia, capacitación

7️⃣ PLAN DE RESPUESTA
   └─ Procedimientos, evacuación, médico, logística, comunicaciones

8️⃣ ACTUALIZACIÓN Y MEJORA
   └─ Responsable, frecuencia, simulacros, capacitaciones

9️⃣ ANEXOS TÉCNICOS
   └─ Documentos, planos, inventarios, observaciones
```

---

## 🧪 PRUEBA RÁPIDA

1. **Inicia sesión** en la aplicación
2. **Navega a**: `/gestion-riesgo/planes-contingencia-v2/crear`
3. **Observa**: Los datos de Supatá aparecen automáticamente
4. **Completa**: Una sección (ej: Introducción)
5. **Avanza**: A la siguiente sección
6. **Crea**: El plan
7. **Ve**: El plan en la lista
8. **Edita**: Una sección
9. **Publica**: El plan

---

## 🔧 ARCHIVOS CLAVE

### **Modelo de Datos**
- `app/models/plan_contingencia_v2.py` → Base datos schema

### **Datos Municipales**
- `app/utils/supata_data.py` → Auto-población

### **Lógica**
- `app/routes/plan_contingencia_v2_routes.py` → Controladores

### **Interfaz**
- `templates/plan_contingencia_*.html` → Vistas (4 templates)

### **Registro**
- `app/__init__.py` → Blueprint registrado

---

## ✨ FUNCIONALIDADES

✅ Crear planes completos
✅ Editar secciones individuales
✅ Ver detalles en navegación por tabs
✅ Barra de progreso dinámica
✅ Auto-población de datos de Supatá
✅ Directorio de emergencias automático
✅ Publicar planes
✅ Eliminar planes
✅ Auditoría (quién creó, cuándo)
✅ API endpoints JSON
✅ Validación de campos
✅ Diseño iOS moderno
✅ Responsive (móvil/tablet/desktop)
✅ Paginación en listado

---

## 🐛 TROUBLESHOOTING

### **Problema: "No puedo acceder a /gestion-riesgo/planes-contingencia-v2"**
- Solución: Confirma que hiciste login
- Verifica que el servidor está corriendo (` python run.py`)

### **Problema: "Base de datos no existe"**
- Solución: Ejecuta `python init_db_planes.py`

### **Problema: "Módulo flask_login no encontrado"**
- Solución: `pip install flask-login`

### **Problema: "Datos de Supatá vacíos"**
- Solución: Verifica que `app/utils/supata_data.py` existe
- Recarga la página del navegador

---

## 📞 SOPORTE

Si algo no funciona:
1. Revisa la consola del servidor (busca errores en rojo)
2. Verifica que todas las dependencias están instaladas
3. Confirma que iniciaste sesión
4. Limpia el cache del navegador (Ctrl+Shift+Del)
5. Reinicia el servidor Python

---

**Versión**: 1.0  
**Estado**: ✅ PRODUCCIÓN LISTA  
**Diseño**: iOS 26 iPhone Moderno  
**Datos**: Auto-población de Supatá  
**Normas**: Ley 1523 / APPA Actualizada
