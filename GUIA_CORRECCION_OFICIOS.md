# 📋 GUÍA DE CORRECCIÓN - Generación de Oficios

## Problema Identificado

El oficio generado muestra texto repetitivo mal formateado en la segunda página. Esto se debe a:

1. **Datos de entrada incorrectos**: El campo `cuerpo` contenía texto repetitivo de prueba/placeholder
2. **Distribución de márgenes**: Los márgenes no estaban optimizados para el FORMATO.pdf oficial

## Soluciones Implementadas

###1. **Optimización de Márgenes** ✅
```python
margin = 75          # Reducido de 85px (mejor aprovechamiento del espacio)
header_margin = 200  # Aumentado de 180px (más espacio para escudo oficial)
footer_margin = 90   # Reducido de 180px (optimiza espacio vertical)
```

### 2. **Mejora en Espaciado** ✅
- Destinatario: 3px entre líneas (antes 2px)
- Separación destinatario-asunto: 15px (antes 10px)
- Espacio para firma: 100px mínimo (antes 40px)

### 3. **Validación de Contenido** (Recomendado)

Agregar validación en el frontend para evitar texto repetitivo:

```javascript
// En el formulario de oficios (templates/...)
function validarCuerpoOficio(texto) {
    // Detectar texto repetitivo (más de 3 repeticiones de la misma frase)
    const palabras = texto.split(' ');
    const frecuencia = {};
    
    palabras.forEach(palabra => {
        frecuencia[palabra] = (frecuencia[palabra] || 0) + 1;
    });
    
    const maxRepeticiones = Math.max(...Object.values(frecuencia));
    
    if (maxRepeticiones > 50) { // Umbral configurable
        alert('⚠️ El texto parece tener contenido repetitivo. Por favor revisa el campo "Cuerpo del Oficio".');
        return false;
    }
    
    return true;
}
```

## Cómo Generar un Oficio Correctamente

### Opción 1: Desde la Aplicación Web

1. Accede a **http://localhost:5000** (desarrollo) o **https://alcald-a-virtual-production.up.railway.app** (producción)
2. Ve a **Asistente IA** > **Oficios**
3. Llena el formulario con datos REALES:

   ```
   Número: 001
   Fecha: 2026-01-25
   Destinatario: JORGE ENRIQUE MACHUCA LOPEZ
   Cargo: Gerente Empresas Públicas de Cundinamarca
   Entidad: Empresas Públicas de Cundinamarca
   Dirección: Calle 26 # 1D - 82
   
   Asunto: Solicitud de Prórroga en tiempo (3 MESES) al CONVENIO...
   
   Cuerpo: (Texto bien formateado, NO REPETITIVO)
   Por medio de la presente me permito solicitar cordialmente...
   
   Firmante: Arquitectura
   Cargo Firmante: Arquitectura
   Teléfono: 3216356414
   Email: rafaelgordilan@gmail.com
   ```

4. Click en **"Generar PDF"**
5. El archivo se descargará automáticamente

### Opción 2: Importar desde JSON

Usa el archivo `oficio_ejemplo_correcto.json` generado:

```bash
# En la consola del navegador (F12)
fetch('oficio_ejemplo_correcto.json')
  .then(r => r.json())
  .then(data => {
    // Llenar formulario automáticamente
    document.getElementById('numero').value = data.numero;
    document.getElementById('fecha').value = data.fecha;
    document.getElementById('destinatario').value = data.destinatario;
    // ... etc
  });
```

## Resultados Esperados

### ✅ Página 1
- Encabezado con escudo oficial centrado
- Número de oficio y fecha correctamente alineados
- Destinatario con 4 líneas (nombre, cargo, entidad, dirección)
- Asunto y referencia claramente visibles
- Saludo formal
- Inicio del cuerpo del oficio

### ✅ Página 2 (si aplica)
- Continuación del cuerpo sin texto repetitivo
- Firma al final con espacio adecuado
- Datos de contacto (teléfono | email)

### ✅ Formato Oficial
- Cada página tiene el membrete oficial del FORMATO.pdf
- Espaciado consistente en todas las páginas
- Sin sobreposición de texto con encabezado/pie

## Verificación de Calidad

Antes de aprobar un oficio, verifica:

- [ ] No hay texto repetitivo
- [ ] Los márgenes son uniformes
- [ ] La firma cabe en la última página sin cortarse
- [ ] El asunto está completo y visible
- [ ] Las viñetas (•) se muestran correctamente
- [ ] El formato oficial (FORMATO.pdf) se aplicó correctamente

## Archivos Modificados

- `app/routes/ia.py` - Generación de PDF optimizada
- `test_generar_oficio_limpio.py` - Script de ejemplo
- `oficio_ejemplo_correcto.json` - Datos de prueba correctos

## Próximos Pasos

1. **Implementar validación en frontend** para evitar texto repetitivo
2. **Agregar preview del PDF** antes de descargar
3. **Crear plantillas predefinidas** para tipos comunes de oficios
4. **Agregar auto-numeración** desde la base de datos

---

**Fecha de actualización**: 2026-01-25  
**Versión**: 1.0  
**Autor**: GitHub Copilot AI Assistant
