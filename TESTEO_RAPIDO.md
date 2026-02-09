# 🧪 TESTEO RÁPIDO - GUÍA PASO A PASO

**Estimado:** 30-45 minutos  
**Dificultad:** ⭐⭐☆☆☆ (Muy Fácil)  
**Herramientas:** PowerShell, navegador, curl  

---

## PASO 0: VERIFICACIÓN RÁPIDA DE ARCHIVOS

Antes de hacer nada, entra a la carpeta del proyecto y verifica que existan:

```powershell
# En PowerShell, ejecuta:
Test-Path .\app\utils\backup_manager.py
Test-Path .\app\routes\backup_api.py
Test-Path .\templates\componente_backup.html
```

Si todos retornan `True`, continúa.

---

## PASO 1: REINICIAR FLASK (5 minutos)

### Matriarca el proceso anterior:
```powershell
# Si Flask está corriendo (Ctrl+C en otra terminal)
# o simplemente:
Get-Process python | Stop-Process -Force
```

### Inicia Flask:
```powershell
cd c:\Users\rafa_\Downloads\AlcaldiaVirtualWeb
python run.py
```

**Busca en los logs estos mensajes:**
```
[BACKUP] BackupManager inicializado
```

✅ Si ves este mensaje, **EXITO** - continúa.  
❌ Si ves error, revisa [TESTING_BACKUP.md](TESTING_BACKUP.md) sección "Errores Comunes"

---

## PASO 2: TEST 1 - VER ESTADO (2 minutos)

Abre **una NUEVA terminal PowerShell** (no cierres la anterior con Flask).

```powershell
$uri = "http://localhost:5000/api/backup/estado"
curl $uri
```

**Resultado esperado:**
```json
{
  "success": true,
  "db_size_kb": 2048.5,
  "backups_count": 0,
  "total_backup_size_kb": 0,
  "recent_backups": []
}
```

✅ **PASO 2 = EXITO** si ves `"success": true`  
⏸️ Si falla, vuelve a Paso 1 - Flask no reinició bien

---

## PASO 3: TEST 2 - CREAR BACKUP (3 minutos)

**En la misma terminal de PowerShell:**

```powershell
$uri = "http://localhost:5000/api/backup/crear"
curl -X POST $uri
```

**Resultado esperado:**
```json
{
  "success": true,
  "mensaje": "Backup creado exitosamente",
  "backup": {
    "archivo": "/backups/backup_20260208_143025.zip",
    "nombre": "backup_20260208_143025",
    "tamaño_kb": 2048.5
  }
}
```

✅ **PASO 3 = EXITO** si ves el archivo en respuesta

**Verificar físicamente:**
```powershell
ls .\backups\   # Debe mostrar backup_*.zip
dir .\backups\backup_*.zip
```

⏸️ Si no ves archivo, revisa que `app/config.py` tiene línea: `BACKUPS_DIR = BASE_DIR / "backups"`

---

## PASO 4: TEST 3 - LISTAR BACKUPS (2 minutos)

**En la terminal:**

```powershell
$uri = "http://localhost:5000/api/backup/listar"
curl $uri
```

**Resultado esperado:**
```json
{
  "success": true,
  "backups": [
    {
      "archivo": "/backups/backup_20260208_143025.zip",
      "nombre": "backup_20260208_143025",
      "tamaño_archivo_kb": 2048.5,
      "timestamp": "20260208_143025"
    }
  ],
  "total_backups": 1
}
```

✅ **PASO 4 = EXITO** si ves la lista con tu backup

---

## PASO 5: TEST 4 - DESCARGAR BACKUP (2 minutos)

Vamos a descargar el backup que creamos:

```powershell
# Primero obtén el nombre del último backup
$uri = "http://localhost:5000/api/backup/listar"
$response = curl $uri | ConvertFrom-Json
$backup_name = $response.backups[0].nombre

# Ahora descarga
$download_uri = "http://localhost:5000/api/backup/descargar/$backup_name.zip"
curl -O $download_uri
```

**Verificar:**
```powershell
ls backup_*.zip   # Debe estar en carpeta actual
```

✅ **PASO 5 = EXITO** si descarga el archivo

---

## PASO 6: TEST 5 - EXPORTAR DATOS (2 minutos)

```powershell
$uri = "http://localhost:5000/api/backup/exportar"
$body = @{
    formato = "json"
    tablas = @("usuarios")
} | ConvertTo-Json

curl -X POST $uri `
  -H "Content-Type: application/json" `
  -d $body
```

**Resultado esperado:**
```json
{
  "success": true,
  "mensaje": "Datos exportados exitosamente",
  "ruta": "/documentos_generados/export_20260208_143500.json"
}
```

**Verificar:**
```powershell
ls .\documentos_generados\export_*.json
```

✅ **PASO 6 = EXITO** si existe archivo JSON

---

## PASO 7: TEST 6 - CREAR OTRO BACKUP (2 minutos)

Vamos a crear un segundo backup para poder probar restauración:

```powershell
curl -X POST http://localhost:5000/api/backup/crear
```

**Verificar:**
```powershell
ls .\backups\   # Debe mostrar 2 archivos ZIP
```

✅ **PASO 7 = EXITO** si tienes 2 backups

---

## PASO 8: TEST 7 - VER ESTADO ACTUALIZADO (1 minuto)

```powershell
curl http://localhost:5000/api/backup/estado
```

**Resultado esperado:**
```json
{
  "success": true,
  "db_size_kb": 2048.5,
  "backups_count": 2,
  "total_backup_size_kb": 4097,
  "recent_backups": [
    {...},
    {...}
  ]
}
```

✅ **PASO 8 = EXITO** si cuenta = 2

---

## PASO 9: TEST 8 - RESTAURAR BACKUP (5 minutos) ⚠️

**ADVERTENCIA:** Este test restaura la BD. Los datos actuales se guardan primero en `backup_before_restore_*`.

```powershell
# Obtén nombre del primer backup
$uri = "http://localhost:5000/api/backup/listar"
$response = curl $uri | ConvertFrom-Json
$backup_name = $response.backups[0].nombre  # El más antiguo

# Restaura
$restore_uri = "http://localhost:5000/api/backup/restaurar/$backup_name.zip"
$body = @{ confirmar = $true } | ConvertTo-Json

curl -X POST $restore_uri `
  -H "Content-Type: application/json" `
  -d $body
```

**Resultado esperado:**
```json
{
  "success": true,
  "mensaje": "BD restaurada exitosamente desde backup"
}
```

**Verificar que se creó backup de seguridad:**
```powershell
ls .\backups\backup_before_restore_*
```

✅ **PASO 9 = EXITO** si existe `backup_before_restore_*`

---

## PASO 10: TEST 9 - ELIMINAR BACKUP (2 minutos)

```powershell
# Obtén nombre del último backup
$uri = "http://localhost:5000/api/backup/listar"
$response = curl $uri | ConvertFrom-Json
$backup_to_delete = $response.backups[-1].nombre  # El último

# Elimina
$delete_uri = "http://localhost:5000/api/backup/eliminar/$backup_to_delete.zip"
curl -X DELETE $delete_uri
```

**Resultado esperado:**
```json
{
  "success": true,
  "mensaje": "Backup eliminado exitosamente"
}
```

**Verificar:**
```powershell
$before = (ls .\backups\ | Measure-Object).Count
# Ejecuta el comando DELETE arriba
$after = (ls .\backups\ | Measure-Object).Count
# $after debe ser $before - 1
```

✅ **PASO 10 = EXITO** si archivo fue eliminado

---

## RESUMEN RÁPIDO DE TESTS

| # | Test | Endpoint | Status |
|---|------|----------|--------|
| 1 | Ver estado | GET /api/backup/estado | ✅ |
| 2 | Crear backup | POST /api/backup/crear | ✅ |
| 3 | Listar backups | GET /api/backup/listar | ✅ |
| 4 | Descargar | GET /api/backup/descargar | ✅ |
| 5 | Exportar | POST /api/backup/exportar | ✅ |
| 6 | Segundo backup | POST /api/backup/crear | ✅ |
| 7 | Estado (2 backups) | GET /api/backup/estado | ✅ |
| 8 | Restaurar | POST /api/backup/restaurar | ✅ |
| 9 | Eliminar | DELETE /api/backup/eliminar | ✅ |

**Si todos tienen ✅, todos los tests pasaron.**

---

## ✅ TEST 10: VERIFICACIÓN FINAL (5 minutos)

```powershell
# 1. Contar archivos backup
$backup_count = (ls .\backups\ | Measure-Object).Count
Write-Host "Total backups: $backup_count (debe ser 2-3)"

# 2. Ver tamaño total
$total_size = (ls .\backups\ -Recurse | Measure-Object -Sum Length).Sum / 1KB
Write-Host "Tamaño total backups: ${total_size} KB"

# 3. Listar archivos específicos
Write-Host "Archivos en backups/:"
ls .\backups\

# 4. Verificar que JSON export existe
Write-Host "Exports JSON:"
ls .\documentos_generados\export_*.json

# 5. Test final - crear auto-backup
Write-Host "Auto-backup..."
curl -X POST http://localhost:5000/api/backup/auto-backup
```

---

## 🎯 SI TODO PASÓ

Ahora integra el componente en `templates/configuracion.html`:

```html
<!-- Agrega esta línea en la sección apropiada de configuracion.html -->
{% include 'componente_backup.html' %}
```

Luego reinicia Flask y navega a Configuración. Deberías ver el panel de backup.

---

## ❌ SI ALGO FALLÓ

**Test 1-2 falla (Flask):**
- [ ] Verificar que Flask reinició correctamente
- [ ] Buscar `[BACKUP]` en logs de Flask
- [ ] Ver si hay error de sintaxis en archivos Python

**Test 3+ falla (API):**
- [ ] Verificar que `app/__init__.py` tiene import y register de backup_api
- [ ] Verificar que `app/config.py` tiene BACKUPS_DIR
- [ ] Revisitar [TESTING_BACKUP.md](TESTING_BACKUP.md) sección "Si Algo No Funciona"

**ZIP/Archivos no se crean:**
- [ ] Crear manualmente: `mkdir backups`
- [ ] Verificar permisos de escritura
- [ ] Revisar logs de Flask para errores

---

## 📋 CHECKBOX DE COMPLETITUD

```
⏱️  APUNTA EL TIEMPO ACTUAL: _________

TEST SUITE BACKUP:
☐ PASO 0: Archivos verificados
☐ PASO 1: Flask reinició
☐ PASO 2: Estado OK
☐ PASO 3: Backup creado
☐ PASO 4: Listado OK
☐ PASO 5: Descargado
☐ PASO 6: Exportado
☐ PASO 7: Segundo backup
☐ PASO 8: Restaurado
☐ PASO 9: Eliminado
☐ PASO 10: Verificación final

⏱️  TIEMPO FINAL: _________
⏱️  TOTAL: _________ minutos

STATUS: ✅ TODOS LOS TESTS PASARON
```

---

## 🎉 SIGUIENTE PASO

Una vez que todos los tests pasen:

1. **Integrar UI**
   - Edita `templates/configuracion.html`
   - Agrega `{% include 'componente_backup.html' %}`
   - Reinicia Flask
   - Navega a Configuración

2. **Probar desde UI**
   - Click "Crear Backup"
   - Verificar que aparece en tabla
   - Click "Restaurar" en un backup
   - Verificar que funciona

3. **Marcar como COMPLETO**
   - El sistema está 100% funcional
   - Listo para producción

---

## 💡 NOTAS

- **Tiempo real o más rápido:** Si todo funciona sin problemas
- **Todos los datos se preservan:** Cada test restaura o crea respaldo
- **Sin datos que borrar:** Puedes ejecutar tests múltiples veces
- **Reversible:** Si algo sale mal, está el `backup_before_restore_*`

---

**Buena suerte con los tests! 🚀**

Si algo falla, refiere a [TESTING_BACKUP.md](TESTING_BACKUP.md) para troubleshooting detallado.
