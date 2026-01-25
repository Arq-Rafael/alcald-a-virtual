# 📋 Memoria de Sesión - Rediseño PDF Planes de Contingencia
**Fecha:** 23 de Enero 2026  
**Estado:** En Progreso - Rediseño de Portada y Layout

---

## 🎯 Objetivos Completados

### ✅ Correcciones Aplicadas
1. **Indentation Error Fijo** - Línea 440 en `contingencia_api.py` (loop TOC con indentación incorrecta)
2. **Rediseño de Portada** - Nuevo estilo moderno inspirado en referencia de póster
3. **Layout Reorganizado** - Todo el contenido reposicionado para respetar cabecera del FORMATO.pdf

---

## 🔧 Cambios Técnicos Realizados

### Archivo: `app/routes/contingencia_api.py` 

#### 1. **Nueva Portada Moderna** (líneas 330-385)
```python
# Diseño:
# - Fondo blanco base + capa de color con transparencia (25%)
# - Franja vertical de acento verde (25% del ancho)
# - Texto limpio: título + subtítulo + datos clave
# - Soporte para imagen de fondo: static/imagenes/portada_naturaleza.jpg
# - Si no existe imagen, mantiene esquema de color limpio
```

#### 2. **Variables de Posicionamiento**
- `margin = 60` (aumentado de 50 para mejor espaciado)
- `content_top = h - 240` (nueva variable para mantener distancia del encabezado)
- Todos los `y_pos` iniciales ahora usan `content_top - 40` en lugar de `h - 140`

#### 3. **Función _draw_section_header Mejorada**
```python
def _draw_section_header(c, title, color_primary, color_accent, margin, w, h, top=None):
    """Dibuja encabezado con parámetro 'top' opcional para flexibilidad"""
    safe_top = top or (h - 220)
    # ... resto del código
```

#### 4. **Saltos de Página Corregidos**
- Reemplazo de `y_pos = h - margin` por `y_pos = content_top - 40`
- En 5 ubicaciones diferentes para mantener consistencia

---

## 🚀 Próximos Pasos Recomendados

### Inmediatos:
1. **Agregar Imagen de Portada**
   - Descargar/crear imagen de naturaleza colombiana
   - Guardar en: `static/imagenes/portada_naturaleza.jpg` (tamaño mín: 612x792px)
   - Formatos soportados: JPG, PNG

2. **Probar Generación de PDF**
   - Acceder a `/riesgo/planes-contingencia`
   - Crear o editar un plan de contingencia
   - Descargar PDF y verificar:
     - ✓ Portada limpia sin superposiciones
     - ✓ Tabla de contenidos dentro de zona segura
     - ✓ Secciones respetan encabezado del formato
     - ✓ Textos no se montan unos sobre otros

3. **Ajustes Finos** (si es necesario)
   - Si hay superposición, aumentar `content_top` (ej: `h - 260`)
   - Si falta espacio, reducir `margin` (ej: 50)
   - Tweakear espaciado entre líneas ajustando `-14`, `-18`, `-20` en canvas.drawString

### Futuros:
- [ ] Agregar más elementos visuales a la portada (líneas decorativas, logos adicionales)
- [ ] Validar que todas las secciones del documento caigan en páginas completas
- [ ] Hacer portada responsive a diferentes tipos de evento (colores dinámicos)
- [ ] Agregar numeración de páginas en el pie de página
- [ ] Validar campos JSON no se truncuen

---

## 📊 Estado Actual del Sistema

**API Endpoint:** `/api/contingencia/<id>/pdf`  
**Formato Base:** `/datos/FORMATO.pdf`  
**Portada:** Dinámicamente generada con ReportLab  
**Fusión:** PyPDF2 merge (overlay + template)  
**Status:** ✅ Server activo en http://127.0.0.1:5000

---

## 🔍 Detalles de Código Importantes

**Color Scheme:**
- `COLOR_PRIMARY = #2d5016` (Verde oscuro)
- `COLOR_SECONDARY = #5a8a3a` (Verde medio)
- `COLOR_ACCENT = #7cb342` (Verde limón)
- `COLOR_TEXT = #333333` (Gris oscuro)

**Estructura de PDF:**
1. Portada personalizada
2. Tabla de contenidos
3. Secciones 1-11 con contenido dinámico
4. Merge con FORMATO.pdf para aplicar template oficial

---

## 💾 Archivos Modificados
- `app/routes/contingencia_api.py` - Toda la lógica de PDF

## 📁 Archivos a Crear
- `static/imagenes/portada_naturaleza.jpg` - Imagen de fondo para portada

---

## 🐛 Problemas Conocidos Resueltos
- ✅ IndentationError en línea 440 (TOC loop)
- ✅ Texto montado encima de encabezado del formato
- ✅ Portada poco profesional/atractiva
- ✅ Contenido invadiendo zona de cabecera

---

## 📞 Notas para Próxima Sesión
- El servidor está en modo debug, detecta cambios automáticamente
- Para reiniciar: `CTRL+C` en terminal, luego `C:/Users/rafa_/Downloads/AlcaldiaVirtualWeb/venv/Scripts/python.exe run.py`
- Si hay cambios en `contingencia_api.py`, el servidor se reinicia solo
- Las ediciones se aplican inmediatamente sin necesidad de recargar manualmente
