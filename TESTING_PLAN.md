# 🧪 Guía de Prueba - Flujo Completo iOS 26

## 📋 Requisitos Previos

- [x] Servidor Flask ejecutándose en `http://127.0.0.1:5000`
- [x] Base de datos SQLite con al menos un Plan de Contingencia
- [x] Imagen `static/imagenes/rana_supata.png` presente
- [x] Navegador moderno (Chrome, Firefox, Safari, Edge)

---

## 🔧 Configuración de Prueba

### Verificar que el servidor está ejecutándose:
```bash
# Debería mostrar:
# * Running on http://127.0.0.1:5000
# * Debugger is active!
```

### Acceder a la interfaz:
```
URL: http://127.0.0.1:5000/gestion-riesgo/planes-contingencia
```

---

## ✅ Prueba 1: Visualización de Botones iOS

**Objetivo**: Verificar que los botones tienen el estilo iOS 26 correcto

### Pasos:
1. Acceder a planes-contingencia
2. Observar la tabla de planes
3. Localizar columna "Acciones" en cada fila

### Verificaciones Visuales:
- [ ] Botón "PDF" color verde (#34C759)
- [ ] Botón "Revisar" color amarillo (#FFB800)
- [ ] Botón "Aprobar" color azul (#007AFF)
- [ ] Botón "Comité" color verde oscuro (#1a472a)
- [ ] Botón "✕" (eliminar) color rojo, forma circular
- [ ] Todos con bordes redondeados (border-radius: 20px)
- [ ] Botones compactos y espaciados uniformemente

**Resultado Esperado**: ✅ Botones con diseño iOS moderno y colores diferenciados

---

## ✅ Prueba 2: Modal de Confirmación - Enviar a Revisión

**Objetivo**: Verificar que el modal iOS aparece al hacer clic en "Revisar"

### Pasos:
1. Hacer clic en botón amarillo "Revisar" de cualquier plan
2. Observar la transición del modal

### Verificaciones del Modal:
- [ ] Fondo oscuro semi-transparente (rgba(0,0,0,0.4))
- [ ] Modal sube desde la parte inferior (animación slideInFromBottom)
- [ ] Título: "¿Enviar a revisión?"
- [ ] Mensaje: "Plan: En Revision"
- [ ] Texto adicional: "Se generará el PDF final aprobado" (NO debería aparecer aquí)
- [ ] Botón "Cancelar" color gris (#f0f0f0)
- [ ] Botón "Confirmar" color azul (#007AFF)
- [ ] Al hacer clic fuera del modal, se cierra

### Prueba de Cancelación:
- [ ] Clic en "Cancelar" → modal se cierra sin cambios
- [ ] Clic en fondo oscuro → modal se cierra sin cambios

**Resultado Esperado**: ✅ Modal tipo iOS con animación suave y cerrado correctamente

---

## ✅ Prueba 3: Cambiar Estado a "En Revisión"

**Objetivo**: Completar el flujo de cambio a En_revision

### Pasos:
1. Hacer clic nuevamente en "Revisar"
2. Hacer clic en "Confirmar"
3. Observar lo que sucede

### Verificaciones:
- [ ] Modal se cierra
- [ ] Aparece burbuja de notificación en esquina inferior derecha
- [ ] Texto en burbuja: "✓ EN_REVISION" o similar
- [ ] Burbuja color verde (#34C759)
- [ ] Burbuja desaparece automáticamente después de 3 segundos
- [ ] Tabla se recarga automáticamente
- [ ] Estado del plan en tabla cambió a "En_revision" o equivalente

**Resultado Esperado**: ✅ Burbuja de éxito con auto-desaparición y lista actualizada

---

## ✅ Prueba 4: Modal de Confirmación - Aprobar (con oferta de PDF)

**Objetivo**: Verificar flujo especial cuando se aprueba (oferta de PDF adicional)

### Pasos:
1. Hacer clic en botón azul "Aprobar" del mismo plan (ahora en En_revision)
2. Observar el modal

### Verificaciones del Modal Principal:
- [ ] Título: "¿Aprobar el plan?"
- [ ] Mensaje: "Plan: Aprobado"
- [ ] Texto adicional: **"Se generará el PDF final aprobado"** (debería aparecer AQUÍ)
- [ ] Botones "Cancelar" y "Confirmar" presentes

### Prueba de Confirmación - Primera Fase:
1. Clic en "Confirmar"
2. Observar transiciones

### Verificaciones Después de Confirmar:
- [ ] Modal principal se cierra
- [ ] Burbuja verde aparece: "✓ APROBADO"
- [ ] Burbuja desaparece después de 3s
- [ ] **Después de ~800ms**, aparece NUEVO modal: "¿Generar PDF Final?"
- [ ] Nuevo modal también tiene diseño iOS

**Resultado Esperado**: ✅ Doble confirmación: primera para estado, segunda para PDF

---

## ✅ Prueba 5: Modal de Generación de PDF

**Objetivo**: Verificar que el modal de PDF aparece con las opciones correctas

### Pasos:
1. (Continuación de Prueba 4)
2. Esperar a que aparezca el segundo modal "¿Generar PDF Final?"

### Verificaciones del Modal:
- [ ] Título: "¿Generar PDF Final?"
- [ ] Mensaje: "El plan ha sido aprobado. ¿Desea descargar el documento final?"
- [ ] Botón "Más tarde" (cancelar)
- [ ] Botón "Descargar" (color azul #007AFF)
- [ ] Modal tiene diseño iOS con animación slideInFromBottom

### Prueba de Rechazo:
1. Clic en "Más tarde"
2. Verificaciones:
   - [ ] Modal se cierra
   - [ ] Tabla se recarga automáticamente
   - [ ] No se genera PDF (sin descarga)

**Resultado Esperado**: ✅ Modal con dos opciones funcionales

---

## ✅ Prueba 6: Descarga de PDF Aprobado

**Objetivo**: Verificar que el PDF se descarga con la portada mejorada

### Pasos:
1. Hacer clic en "Aprobar" nuevamente para el plan (si está en Aprobado)
2. O abrir un plan diferente en estado Aprobado
3. En modal "¿Generar PDF Final?" → clic en "Descargar"

### Verificaciones de Descarga:
- [ ] Se inicia descarga de PDF
- [ ] Nombre del archivo: `plan_contingencia_[ID].pdf`
- [ ] Modal se cierra después de iniciar descarga
- [ ] Tabla se recarga automáticamente

### Verificaciones del PDF Descargado:
Abrir el PDF con Adobe Reader o similar:

#### Página 1 (Portada Aprobada):
- [ ] Título: "PLAN DE CONTINGENCIA" (grande, en verde oscuro)
- [ ] Badge verde: "✓ APROBADO" (en verde #34C759)
- [ ] Subtítulo: Tipo de evento (ej: "INUNDACIÓN")
- [ ] **Imagen rana_supata centrada horizontalmente**
- [ ] Rana tiene buen tamaño (3.0" × 2.4")
- [ ] Rana NO está cortada ni deformada
- [ ] Tabla de información con:
  - Número de Plan
  - Cobertura
  - Estado: "Aprobado" en verde
  - Resolución (si existe)
  - Fecha de Aprobación
  - Aprobado por
- [ ] Pie de página: "Documento oficial aprobado por el Comité..."

#### Páginas Siguientes:
- [ ] Mantienen el formato de FORMATO.pdf (header con logo Alcaldía)
- [ ] Contienen las secciones del plan (Introducción, Objetivos, etc.)
- [ ] Espaciado correcto, texto no superpuesto

**Resultado Esperado**: ✅ PDF profesional con portada mejorada y rana bien posicionada

---

## ✅ Prueba 7: Flujo Completo Estado "Aprobado por Comité"

**Objetivo**: Probar el flujo para Aprobado_Comite (igual que Aprobado)

### Pasos:
1. Tomar un plan en estado "Aprobado"
2. Clic en botón verde oscuro "Comité"
3. Modal: "¿Aprobado por Comité?"

### Verificaciones:
- [ ] Modal aparece con mensaje correcto
- [ ] Mensaje: "Plan: Aprobado Comite"
- [ ] Texto adicional: "Se generará el PDF final aprobado"
- [ ] Al confirmar → burbuja "✓ APROBADO COMITE"
- [ ] Después → modal "¿Generar PDF Final?"
- [ ] PDF descargado también es aprobado (con rana, badge, etc.)

**Resultado Esperado**: ✅ Flujo idéntico al de Aprobado

---

## ✅ Prueba 8: Eliminar Plan

**Objetivo**: Verificar que eliminación funciona

### Pasos:
1. Clic en botón rojo circular "✕" de cualquier plan
2. Confirmar en el alert nativo (o modal if implementado)

### Verificaciones:
- [ ] Confirmación antes de eliminar (seguridad)
- [ ] Plan se elimina de la tabla
- [ ] Burbuja de éxito: "Plan eliminado exitosamente"
- [ ] Lista actualizada

**Resultado Esperado**: ✅ Plan eliminado correctamente

---

## ✅ Prueba 9: Descarga de PDF Directo

**Objetivo**: Verificar botón "PDF" sin cambiar estado

### Pasos:
1. Clic en botón verde "PDF" de un plan (sin cambiar estado)

### Verificaciones:
- [ ] PDF se descarga inmediatamente
- [ ] Sin modales
- [ ] Nombre: `plan_contingencia_[ID].pdf`
- [ ] Si plan está en Borrador → portada normal
- [ ] Si plan está en Aprobado → portada con rana

**Resultado Esperado**: ✅ Descarga directa sin confirmación

---

## ✅ Prueba 10: Animaciones y Transiciones

**Objetivo**: Verificar suavidad visual

### Verificaciones:
- [ ] Botones se comprimen al hacer clic (scale 0.95)
- [ ] Modal se desliza suavemente desde abajo (300ms)
- [ ] Burbuja aparece con escala suave (300ms)
- [ ] Sin saltos o parpadeos
- [ ] Animaciones fluidas en navegadores modernos

**Resultado Esperado**: ✅ Animaciones iOS-like suave

---

## 🐛 Pruebas de Casos Excepcionales

### Prueba 11: Plan sin imagen rana_supata
**Si no existe la imagen:**
- [ ] PDF se genera sin errores
- [ ] Portada muestra tabla de información sin imagen
- [ ] Mensaje en consola: "Advertencia: No se pudo cargar rana_supata.png"

**Resultado Esperado**: ✅ Fallback elegante

### Prueba 12: Error de API
**Simular error (modificar estado inválido):**
- [ ] Si API retorna error → burbuja roja: "Error: [mensaje]"
- [ ] Modal se cierra
- [ ] Lista NO se recarga

**Resultado Esperado**: ✅ Manejo de errores visible

### Prueba 13: Cerrar modal haciendo clic en backdrop
**Pasos:**
1. Abrir cualquier modal
2. Clic en el área gris oscura (fuera del modal)

**Verificación:**
- [ ] Modal se cierra sin hacer nada
- [ ] Sin cambios en el plan

**Resultado Esperado**: ✅ Cierre intuitivo

---

## 📊 Resumen de Casos de Prueba

| # | Descripción | Status | Notas |
|---|-------------|--------|-------|
| 1 | Visualización botones iOS | ⏳ | Esperar resultado |
| 2 | Modal confirmación básico | ⏳ | Esperar resultado |
| 3 | Cambiar estado En_revision | ⏳ | Esperar resultado |
| 4 | Modal aprobación especial | ⏳ | Esperar resultado |
| 5 | Modal PDF adicional | ⏳ | Esperar resultado |
| 6 | Descarga PDF aprobado | ⏳ | Esperar resultado |
| 7 | Flujo Aprobado_Comite | ⏳ | Esperar resultado |
| 8 | Eliminar plan | ⏳ | Esperar resultado |
| 9 | Descarga PDF directo | ⏳ | Esperar resultado |
| 10 | Animaciones suaves | ⏳ | Esperar resultado |
| 11 | Fallback sin rana | ⏳ | Esperar resultado |
| 12 | Manejo de errores | ⏳ | Esperar resultado |
| 13 | Cierre por backdrop | ⏳ | Esperar resultado |

---

## 🎯 Aceptación Final

El módulo de Planes de Contingencia se considera **COMPLETADO** cuando:

✅ Todos los casos de prueba 1-10 pasan exitosamente
✅ La portada aprobada muestra la rana centrada y bien formateada
✅ Los botones tienen el estilo iOS 26 correcto
✅ Las animaciones son suaves y sin saltos
✅ El flujo de aprobación es intuitivo con confirmaciones claras
✅ La burbuja de notificación aparece y desaparece correctamente
✅ El PDF descargado tiene calidad profesional

---

## 🚀 Comandos Útiles

### Reiniciar servidor:
```bash
Ctrl+C (en terminal con servidor)
python run.py  # o .\venv\Scripts\python.exe run.py
```

### Limpiar caché de navegador:
```
Ctrl+Shift+Delete (Chrome/Edge)
Cmd+Shift+Delete (Mac)
```

### Ver consola de errores:
```
F12 → Console → Revisar errores JavaScript
```

### Inspeccionar elementos:
```
F12 → Elements → Click en elemento → Ver estilos CSS
```

---

## 📞 Soporte

Si alguna prueba falla:
1. Revisar consola de navegador (F12 → Console)
2. Revisar logs del servidor (terminal donde corre Flask)
3. Verificar que FORMATO.pdf existe en `datos/FORMATO.pdf`
4. Verificar que rana_supata.png existe en `static/imagenes/`
5. Reiniciar servidor y limpiar caché del navegador

