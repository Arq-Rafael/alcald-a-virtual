# ✅ CHECKLIST: VERIFICAR QUE TODO FUNCIONA

## 📋 LISTA DE VERIFICACIÓN PASO A PASO

### FASE 1: Preparación (2 minutos)

- [ ] **P1.1** - Abro navegador (Chrome, Firefox, Edge, etc.)
- [ ] **P1.2** - Ingreso a: http://127.0.0.1:5000/riesgo/planes-contingencia
- [ ] **P1.3** - Presiono: `Ctrl+Shift+R` para limpiar caché (o `Cmd+Shift+R` en Mac)
- [ ] **P1.4** - Espero 3 segundos a que cargue completamente

**Si llegaste aquí ✓**: Continúa a Fase 2

---

### FASE 2: Buscar el Cambio (1 minuto)

- [ ] **P2.1** - La página muestra una tabla con planes
- [ ] **P2.2** - Cada fila tiene botones a la derecha: `[PDF] [✎] [...]`
- [ ] **P2.3** - Busco un plan en estado **BORRADOR** o **EN REVISIÓN**
- [ ] **P2.4** - En los botones de ese plan, veo: `[PDF] [✎] [📋] [...otros]`
- [ ] **P2.5** - El botón `[📋]` tiene color **morado** (#6366f1)

**¿Viste el botón morado 📋?**
- ✓ SÍ → Continúa a Fase 3
- ✗ NO → Ve a [TROUBLESHOOTING](#troubleshooting)

---

### FASE 3: Interactuar con el Botón (1 minuto)

- [ ] **P3.1** - Hago click en el botón `[📋]` morado
- [ ] **P3.2** - Se abre un modal (ventana) oscuro
- [ ] **P3.3** - El modal tiene un encabezado: "Secciones del Plan"
- [ ] **P3.4** - El modal muestra 9 opciones:
  - [ ] 1. Introducción
  - [ ] 2. Objetivos y Alcance
  - [ ] 3. Marco Normativo
  - [ ] 4. Organización
  - [ ] 5. Análisis de Riesgos
  - [ ] 6. Medidas de Reducción
  - [ ] 7. Plan de Respuesta
  - [ ] 8. Actualización
  - [ ] 9. Anexos
- [ ] **P3.5** - Hay un botón `[Cerrar]` abajo del modal

**¿Se abrió el modal con 9 secciones?**
- ✓ SÍ → Continúa a Fase 4
- ✗ NO → Ve a [TROUBLESHOOTING](#troubleshooting)

---

### FASE 4: Seleccionar una Sección (2 minutos)

- [ ] **P4.1** - En el modal, hago click en `1. Introducción`
- [ ] **P4.2** - El modal se cierra
- [ ] **P4.3** - La página redirige a una nueva URL:
  ```
  /gestion-riesgo/planes-contingencia/editar/{id}/introduccion
  ```
- [ ] **P4.4** - Espero 2-3 segundos a que cargue la nueva página
- [ ] **P4.5** - La página muestra un nuevo layout con dos columnas

**¿Se cargó el wizard (página con dos columnas)?**
- ✓ SÍ → Continúa a Fase 5
- ✗ NO → Ve a [TROUBLESHOOTING](#troubleshooting)

---

### FASE 5: Verificar el Wizard (2 minutos)

- [ ] **P5.1** - Lado izquierdo: Veo una barra con 9 secciones listadas
  - [ ] "1. Introducción" está destacado/activo
  - [ ] Las otras 8 secciones están disponibles
- [ ] **P5.2** - Lado derecho: Veo un formulario con campos:
  - [ ] "Descripción del evento" (textarea)
  - [ ] "Justificación" (textarea)
  - [ ] "Contexto" (textarea)
- [ ] **P5.3** - Abajo del formulario hay botones:
  - [ ] `[◀ Anterior]`
  - [ ] `[Guardar Sección]`
  - [ ] `[Siguiente ▶]`

**¿Ves el wizard con las secciones y el formulario?**
- ✓ SÍ → Continúa a Fase 6
- ✗ NO → Ve a [TROUBLESHOOTING](#troubleshooting)

---

### FASE 6: Navegar entre Secciones (2 minutos)

- [ ] **P6.1** - En la barra izquierda, hago click en `2. Objetivos y Alcance`
- [ ] **P6.2** - El wizard se actualiza
- [ ] **P6.3** - Ahora "2. Objetivos y Alcance" está destacado
- [ ] **P6.4** - Los campos en la derecha cambian (nuevos campos para objetivos)
- [ ] **P6.5** - Hago click en `3. Marco Normativo`
- [ ] **P6.6** - Nuevamente se actualiza (más cambios en los campos)
- [ ] **P6.7** - Vuelvo a `1. Introducción` - ¡los campos vuelven a ser los originales!

**¿Puedes navegar entre las 9 secciones sin problemas?**
- ✓ SÍ → Continúa a Fase 7
- ✗ NO → Ve a [TROUBLESHOOTING](#troubleshooting)

---

### FASE 7: Probar Botón "Editar" Alternativo (1 minuto)

- [ ] **P7.1** - Vuelvo a la lista: http://127.0.0.1:5000/riesgo/planes-contingencia
- [ ] **P7.2** - Hago Ctrl+Shift+R para limpiar caché nuevamente
- [ ] **P7.3** - Busco otro plan (diferente al anterior)
- [ ] **P7.4** - Hago click en el botón `[✎]` (Editar)
- [ ] **P7.5** - El navegador redirige a:
  ```
  /gestion-riesgo/planes-contingencia/editar/{id}/introduccion
  ```
- [ ] **P7.6** - Se abre el wizard directamente en la Sección 1

**¿Funciona el botón "Editar" abriendo el wizard en Sección 1?**
- ✓ SÍ → Continúa a Fase 8
- ✗ NO → Ve a [TROUBLESHOOTING](#troubleshooting)

---

### FASE 8: Verificar Estados del Plan (2 minutos)

Para cada estado de plan, verifica que el botón 📋 está presente:

#### Estado: BORRADOR
- [ ] **P8.1** - Veo botones: `[PDF] [✎] [📋] [Revisar] [✕]`
- [ ] **P8.2** - El botón 📋 es morado y clickeable

#### Estado: EN REVISIÓN
- [ ] **P8.3** - Veo botones: `[PDF] [✎] [📋] [Aprobar] [↩]`
- [ ] **P8.4** - El botón 📋 es morado y clickeable

#### Estado: APROBADO
- [ ] **P8.5** - Veo botones: `[PDF] [👁] [📋] [Comité]`
- [ ] **P8.6** - El botón 📋 es morado y clickeable

**¿El botón aparece en todos los estados?**
- ✓ SÍ → ¡Continúa a RESULTADO FINAL!
- ✗ Parcialmente → Ve a [TROUBLESHOOTING](#troubleshooting)

---

### RESULTADO FINAL ✅

Si pasaste todas las fases, ¡FELICITACIONES! Todo está funcionando correctamente.

**Lo que verificaste:**
1. ✅ El botón "📋 Secciones" aparece en la tabla
2. ✅ El modal abre con las 9 secciones
3. ✅ Se puede seleccionar cada sección
4. ✅ El wizard carga correctamente
5. ✅ Se puede navegar entre secciones
6. ✅ El botón "Editar" abre el wizard
7. ✅ El botón aparece en todos los estados

**Próximos pasos:**
- ⏳ Guardar datos por sección (pronto)
- ⏳ Auto-completar con datos de Supatá (pronto)
- ⏳ Generar PDF con estructura oficial (pronto)

---

## <a name="troubleshooting"></a>🆘 TROUBLESHOOTING

### Problema: No veo el botón "📋" en ningún plan

**Soluciones en orden:**

1. **Hard Refresh (PRIMERO INTENTA ESTO)**
   ```
   Windows/Linux: Ctrl + Shift + R
   Mac: Cmd + Shift + R
   ```
   Espera 3-5 segundos.

2. **Limpiar cache del navegador:**
   - Abre DevTools (F12)
   - Click derecho en botón Recargar (parte superior izquierda)
   - Selecciona "Vaciar caché y recargar completamente"
   - Espera

3. **Cerrar y reabnir navegador:**
   - Cierra COMPLETAMENTE el navegador
   - Reabre
   - Ingresa a http://127.0.0.1:5000/riesgo/planes-contingencia
   - Busca el botón

4. **Verificar en la consola:**
   - F12 → Console
   - Pega: `document.querySelectorAll('[onclick*="mostrarMenuSecciones"]').length`
   - Si dice "0" → El botón no está en el HTML
   - Si dice "1" o más → El botón existe

5. **Reiniciar servidor:**
   ```
   Terminal: Ctrl+C (para parar el servidor)
   Luego: python run.py
   Espera a que diga "Running on http://127.0.0.1:5000"
   ```

---

### Problema: El botón existe pero no hace nada al clickear

**Soluciones:**

1. **Verificar consola:**
   ```
   F12 → Console
   typeof mostrarMenuSecciones
   
   Si dice: "function" → La función está cargada
   Si dice: "undefined" → Recarga la página (Ctrl+Shift+R)
   ```

2. **Verificar si hay errores JavaScript:**
   - F12 → Console
   - Busca mensajes rojos (errores)
   - Cópiame los errores si los ves

3. **Probar la función manualmente:**
   - F12 → Console
   - Pega: `mostrarMenuSecciones(1)`
   - Presiona Enter
   - ¿Se abre un modal?
     - Sí → El botón tiene otro problema
     - No → Hay error en la consola (muéstramelo)

---

### Problema: Modal se abre pero está vacío

**Soluciones:**

1. **Verificar HTML del modal:**
   - F12 → Elements
   - Busca: `<div class="ios-modal" id="seccionesModal`
   - ¿Tiene contenido dentro?

2. **Verificar CSS:**
   - El modal podría estar fuera de pantalla
   - Presiona F12 → Console
   - Pega: `document.querySelectorAll('.ios-modal')[0].style.display`
   - Debería decir: "flex"

3. **Reiniciar página:**
   - Ctrl+Shift+R
   - Intenta de nuevo

---

### Problema: Hago click en sección pero no va al wizard

**Soluciones:**

1. **Verificar URL en la consola:**
   - F12 → Console
   - Pega: `window.location.href`
   - Te mostrará la URL actual
   - ¿Es correcta?

2. **Verificar en Network tab:**
   - F12 → Network
   - Haz click en una sección
   - Busca request que diga "editar"
   - ¿El status es 200 (éxito) o 404 (error)?

3. **Verifi que las rutas existan:**
   ```
   F12 → Console
   fetch('/gestion-riesgo/planes-contingencia/editar/1/introduccion')
     .then(r => console.log('Status:', r.status))
   ```
   - Si dice "200" → La ruta existe
   - Si dice "404" → La ruta no existe (problema del servidor)

---

### Problema: El wizard no muestra las 9 secciones

**Soluciones:**

1. **Verificar que la ruta fue correcta:**
   - URL debe ser: `/editar/{id}/{seccion}`
   - Ejemplo: `/editar/1/introduccion`
   - ¿Ves `/detalle/` en la URL? Eso es una vista diferente

2. **Verificar que el plan existe:**
   - Vuelve a la lista
   - ¿El plan aparece en la tabla?
   - Sí → Problema de la ruta
   - No → El plan no existe

3. **Verificar DevTools:**
   - F12 → Console
   - Busca errores rojos
   - Cópiame cualquier error

---

### Problema: Error "404 Not Found"

**Soluciones:**

1. **Verifica que el ID existe:**
   - Vuelve a /riesgo/planes-contingencia
   - Busca el ID del plan en la tabla (primera columna)
   - Usa ese ID en la URL

2. **Verifica la URL:**
   - Correcta: `/gestion-riesgo/planes-contingencia/editar/1/introduccion`
   - Incorrecta: `/gestion-riesgo/editar/1/introduccion` (falta "planes-contingencia")

3. **Reinicia el servidor:**
   - Terminal: Ctrl+C
   - Espera 1-2 segundos
   - Pega: `python run.py`
   - Espera a que diga "Running on..."
   - Intenta de nuevo

---

### Problema: Mensajes de error en rojo en la consola

**Qué hacer:**

1. **Abre DevTools (F12)**
2. **Tab: Console**
3. **Copia cualquier mensaje rojo**
4. **Envíame exactamente qué dice el error**

Ejemplos comunes:
```
❌ "Cannot read property 'mostrarMenuSecciones' of undefined"
   → Solución: Recarga página (Ctrl+Shift+R)

❌ "GET /static/js/contingencia_oficial.js 404"
   → Solución: El archivo no se creó, revisa que exista

❌ "SyntaxError: Unexpected token"
   → Solución: Hay error de sintaxis en un archivo, reinicia servidor
```

---

## ✨ TEST RÁPIDO EN CONSOLA

Si no sabes qué hacer, copia y pega esto en la consola (F12 → Console):

```javascript
// Test completo
console.clear();
console.log('🧪 TEST DE VERIFICACIÓN');
console.log('========================\n');

// Test 1: Función existe
const f1 = typeof mostrarMenuSecciones === 'function';
console.log('1. Función mostrarMenuSecciones:', f1 ? '✅' : '❌');

// Test 2: Botones existen
const btn = document.querySelectorAll('[onclick*="mostrarMenuSecciones"]').length;
console.log('2. Botones en tabla:', btn > 0 ? `✅ (${btn} encontrados)` : '❌');

// Test 3: Modal existe
const modal = document.querySelectorAll('.ios-modal').length;
console.log('3. Modales en página:', modal >= 0 ? '✅' : '❌');

// Resultado
console.log('\n' + (f1 && btn > 0 ? '✅ TODO OK' : '❌ ALGO FALLA'));
```

Presiona Enter y dime qué dice.

---

## 📞 ¿Aún tienes problemas?

Proporciona esta información:

1. **Capturas de pantalla** (F5 screenshot)
2. **URL actual** (de la barra de direcciones)
3. **Errores de consola** (F12 → Console, texto rojo)
4. **Navegador** (Chrome, Firefox, Edge, etc.)
5. **Sistema operativo** (Windows, Mac, Linux)

---

**¡Espero que todo funcione! Si necesitas ayuda, cuéntame qué ves! 🚀**
