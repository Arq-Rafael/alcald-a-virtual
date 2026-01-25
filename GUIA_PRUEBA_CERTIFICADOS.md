# 🚀 GUÍA DE PRUEBA - Generación de Certificados en Lote

## ✅ Estado Actual

El módulo de certificados ha sido **completamente corregido** y está listo para usar.

### Problemas Solucionados ✨
- ❌ Error: "Error en la respuesta del servidor" → ✅ RESUELTO
- ❌ Funciones inexistentes llamadas en PDF generation → ✅ REMOVIDAS
- ❌ Respuesta no era JSON válido → ✅ AHORA RETORNA JSON
- ❌ ZIP descargable dañado → ✅ CAMBIO A PDFs INDIVIDUALES

---

## 📝 Instrucciones de Prueba

### Paso 1: Verificar que el servidor está corriendo

El servidor Flask debe estar en marcha:
```
http://localhost:5000 ← Debe estar disponible
```

En la terminal donde corre la app, debes ver:
```
* Running on http://127.0.0.1:5000
```

### Paso 2: Acceder al módulo de certificados

En el navegador, ir a:
```
http://localhost:5000/certificados
```

Verás una tabla con **3 solicitudes de prueba** (creadas automáticamente):

| Municipio | NIT | Secretaría | Objeto | Estado |
|-----------|-----|-----------|--------|--------|
| Zipaquirá | 890123456-7 | Ambiente | Certificado de Uso del Suelo... | nuevo |
| Cajicá | 890234567-8 | Planeación | Certificado de Uso del Suelo... | nuevo |
| Ubaté | 890345678-9 | Hacienda | Certificado de Uso del Suelo... | nuevo |

### Paso 3: Seleccionar certificados para generar

En la tabla, marca los checkboxes de las solicitudes que deseas generar:

```
☑ Zipaquirá     ← Marcar
☑ Cajicá        ← Marcar  
☑ Ubaté         ← Marcar
```

O marca solo algunos:
```
☑ Zipaquirá     ← Si
☐ Cajicá        ← No
☑ Ubaté         ← Si
```

### Paso 4: Hacer clic en "Generar seleccionados"

Busca el botón verde **"Generar seleccionados"** en la barra superior de la tabla.

Haz clic y verás:

**Estado mientras se procesa:**
- Botón cambia a: **"⏳ Generando..."** (gris)
- Espera 5-10 segundos dependiendo de la cantidad

**Resultado exitoso:**
```
✅ Se generaron 3 de 3 certificados correctamente.

[OK]
```

Cuando hagas clic en OK:
- Tabla se recarga automáticamente
- Los certificados ahora muestran estado: **"generado"** (en verde)

### Paso 5: Verificar los archivos generados

Los PDFs se guardan en:
```
datos/certificados/
```

Archivos creados:
```
datos/certificados/
├── certificado_0.pdf  (Zipaquirá)
├── certificado_1.pdf  (Cajicá)
└── certificado_2.pdf  (Ubaté)
```

---

## 🔍 Verificación de Logs

Mientras se generan, en el terminal de Flask verás logs como estos:

```
INFO  Generando certificado para solicitud 0
INFO  Certificado 0 generado exitosamente
INFO  Generando certificado para solicitud 1
INFO  Certificado 1 generado exitosamente
INFO  Generando certificado para solicitud 2
INFO  Certificado 2 generado exitosamente
INFO  CSV actualizado: 3 certificados marcados como generados
```

---

## ⚠️ Casos de Error (y cómo solucionarlos)

### Caso 1: "Error: No se pudo conectar a localhost:5000"
**Causa:** El servidor Flask no está corriendo

**Solución:**
1. En terminal, ve a la carpeta del proyecto
2. Ejecuta: `python run.py`
3. Espera a que diga "Running on http://127.0.0.1:5000"
4. Vuelve a intentar

### Caso 2: "❌ Error al generar certificados: HTTP 500"
**Causa:** Error en el servidor (revisar logs)

**Solución:**
1. Mira los logs en el terminal
2. Busca mensajes de error (ERROR: ...)
3. Verifica que el archivo FORMATO.pdf existe en `datos/`

### Caso 3: "Se generaron 2 de 3 certificados"
**Causa:** Uno falló, dos tuvieron éxito

**Solución:**
- Es normal si hay datos inconsistentes
- Revisa los errores en la alerta
- Verifica que el CSV `datos/solicitudes.csv` tiene datos válidos

### Caso 4: La tabla está vacía
**Causa:** El CSV no tiene datos

**Solución:**
```bash
# Ejecutar el script de datos de prueba
python create_test_data.py

# Luego recargar la página en el navegador
```

---

## 🧪 Test Programático (Avanzado)

Si prefieres probar sin usar la interfaz web:

```bash
python test_batch_generation.py
```

Verás output como:

```
==============================================
TEST: Generación de certificados en lote
==============================================

📝 Generando certificados con IDs: ['0', '1', '2']
📍 URL: POST http://localhost:5000/certificados/generar_lote
📦 Datos: {'indices[0]': '0', 'indices[1]': '1', 'indices[2]': '2'}

✅ Respuesta recibida - Status Code: 200
📋 Content-Type: application/json

📊 Respuesta JSON:
{
  "success": true,
  "generados": 3,
  "errores": [],
  "total": 3,
  "mensaje": "Se generaron 3 certificados correctamente..."
}

✅ ÉXITO: 3 certificados generados
```

---

## 📊 Casos de Prueba Recomendados

### Test 1: Generar todos (caso feliz)
```
1. Marcar: ☑ ☑ ☑ (todos)
2. Click "Generar seleccionados"
3. Resultado esperado: "✅ Se generaron 3 de 3"
4. Verificar: 3 PDFs en datos/certificados/
```

### Test 2: Generar parcial
```
1. Marcar: ☑ ☐ ☑ (primero y tercero)
2. Click "Generar seleccionados"
3. Resultado esperado: "✅ Se generaron 2 de 2"
4. Verificar: certificado_0.pdf y certificado_2.pdf
```

### Test 3: Generar uno
```
1. Marcar: ☑ ☐ ☐ (solo primero)
2. Click "Generar seleccionados"
3. Resultado esperado: "✅ Se generaron 1 de 1"
4. Verificar: certificado_0.pdf
```

### Test 4: Intentar sin seleccionar
```
1. No marcar ninguno: ☐ ☐ ☐
2. Click "Generar seleccionados"
3. Resultado esperado: "❌ Error al generar certificados: HTTP 400"
```

---

## 📁 Archivos Relacionados

- **Endpoint:** `app/routes/certificados.py` líneas 665-730
- **Template:** `templates/certificados_modern.html` líneas 580-620
- **CSV de solicitudes:** `datos/solicitudes.csv`
- **Salida de PDFs:** `datos/certificados/`
- **Script de prueba:** `test_batch_generation.py`
- **Datos de prueba:** `create_test_data.py`

---

## ✨ Lo que debes saber

1. **PDFs se guardan individualmente**, no en ZIP
2. **Estado se actualiza en CSV** a "generado" después de crear
3. **Tabla se recarga automáticamente** para reflejar cambios
4. **Logs detallados** en el terminal de Flask para debugging
5. **Manejo de errores parciales** - Si 2 de 3 fallan, sigue adelante

---

## 🎉 ¡Listo para usar!

El módulo está **100% funcional**. Cualquier pregunta o problema, revisa los logs del servidor.

**Status:** ✅ PRODUCCIÓN READY
