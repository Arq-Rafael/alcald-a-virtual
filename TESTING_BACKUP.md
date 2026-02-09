# Checklist: Pruebas del Sistema de Backup

## 1️⃣ Verificación de Archivos

### Archivos que Deben Existir:
```
✅ app/utils/backup_manager.py ........... BackupManager class
✅ app/routes/backup_api.py ............. Blueprint de API
✅ templates/componente_backup.html ..... UI Component
```

### Archivos Modificados:
```
✅ app/__init__.py ....................... Integración de backup_api
✅ app/config.py ......................... Configuración de directorios
```

---

## 2️⃣ Verificación de Código

### En app/__init__.py (Línea ~58)
Debe existir:
```python
from .routes.backup_api import backup_api
...
app.register_blueprint(backup_api)
```

### En app/__init__.py (Línea ~120)
Debe existir:
```python
from app.utils.backup_manager import BackupManager
...
with app.app_context():
    app.backup_manager = BackupManager(app)
    logging.info("[BACKUP] BackupManager inicializado")
```

### En app/config.py
Debe existir:
```python
BACKUPS_DIR = BASE_DIR / "backups"
BACKUP_MAX_VERSIONS = 10
```

---

## 3️⃣ Verificación en Tiempo de Ejecución

### Paso 1: Reiniciar la Aplicación
```powershell
# Matar proceso anterior (Ctrl+C)
# Ejecutar:
python run.py
```

**Buscar en logs estos mensajes:**
- ✅ `[BACKUP] BackupManager inicializado`
- ✅ Debe crear directorio `./backups/` si no existe
- ✅ No debe haber errores de importación

---

## 4️⃣ Pruebas de API

### Test 1: Ver Estado del Sistema
```powershell
$uri = "http://localhost:5000/api/backup/estado"
$response = Invoke-WebRequest -Uri $uri -Method GET
$response.Content | ConvertFrom-Json | Format-List
```

**Esperado:**
```json
{
  "success": true,
  "db_size_kb": 2048.5,
  "backups_count": 0,
  "total_backup_size_kb": 0,
  "recent_backups": []
}
```

---

### Test 2: Crear Backup Manual
```powershell
$uri = "http://localhost:5000/api/backup/crear"
$response = Invoke-WebRequest -Uri $uri -Method POST -ContentType "application/json"
$response.Content | ConvertFrom-Json | Format-List
```

**Esperado:**
```json
{
  "success": true,
  "mensaje": "Backup creado exitosamente",
  "backup": {
    "success": true,
    "archivo": "/backups/backup_YYYYMMDD_HHMMSS.zip",
    "nombre": "backup_YYYYMMDD_HHMMSS",
    "timestamp": "YYYYMMDD_HHMMSS",
    "tamaño_kb": 2048.5
  }
}
```

**Verificar en sistema de archivos:**
```powershell
ls ./backups/  # Debe mostrar archivo backup_*.zip
```

---

### Test 3: Listar Backups
```powershell
$uri = "http://localhost:5000/api/backup/listar"
$response = Invoke-WebRequest -Uri $uri -Method GET
$response.Content | ConvertFrom-Json | Format-List
```

**Esperado:**
```json
{
  "success": true,
  "backups": [
    {
      "archivo": "/backups/backup_20260208_143025.zip",
      "nombre": "backup_20260208_143025",
      "tamaño_archivo_kb": 2048.5,
      "timestamp": "20260208_143025",
      "fecha": "2026-02-08T14:30:25"
    }
  ],
  "total_backups": 1,
  "espacio_total_kb": 2048.5
}
```

---

### Test 4: Exportar Datos
```powershell
$uri = "http://localhost:5000/api/backup/exportar"
$body = @{
    formato = "json"
    tablas = @("usuarios")
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri $uri -Method POST `
    -ContentType "application/json" `
    -Body $body

$response.Content | ConvertFrom-Json | Format-List
```

**Esperado:**
```json
{
  "success": true,
  "mensaje": "Datos exportados exitosamente",
  "ruta": "/documentos_generados/export_TIMESTAMP.json"
}
```

**Verificar archivo creado:**
```powershell
ls ./documentos_generados/export_*.json
```

---

## 5️⃣ Pruebas de UI (Una vez integrado en configuracion.html)

### Test 1: Cargar Componente
- Navegar a Configuración → Sección Backup
- Debe mostrar:
  - ✅ Estado actual de BD (tamaño, contador de backups)
  - ✅ 3 botones: "Crear Backup", "Exportar Datos", "Auto-Backup"
  - ✅ Tabla de historial de backups

### Test 2: Crear Backup desde UI
- Click en "Crear Backup Manual"
- Debe mostrar spinner de cargando
- Después: Alerta de éxito + nueva fila en tabla

### Test 3: Descargar Backup
- En historial de backups, click en icono de "Descargar"
- Debe descargar archivo `.zip`

### Test 4: Restaurar Backup
- Click en "Restaurar" en backup del historial
- Modal de confirmación con advertencia
- Confirmar
- Sistema debe:
  - ✅ Crear backup de seguridad (`backup_before_restore_*`)
  - ✅ Restaurar BD anterior
  - ✅ Recargar página
- Verificar que datos restaurados son correctos

---

## 6️⃣ Pruebas de Restauración

### Preparación:
1. Crear backup: `backup_test_1.zip` (estado actual)
2. Crear algunos registros nuevos en la app
3. Crear otro backup: `backup_test_2.zip` (con nuevos datos)

### Test Restauración:
```powershell
# Restaurar desde backup_test_1
$uri = "http://localhost:5000/api/backup/restaurar/backup_test_1.zip"
$body = @{ confirmar = $true } | ConvertTo-Json

$response = Invoke-WebRequest -Uri $uri -Method POST `
    -ContentType "application/json" `
    -Body $body

$response.Content | ConvertFrom-Json | Format-List
```

**Esperado:**
- ✅ Archivo `backup_before_restore_*` creado
- ✅ Base de datos restaurada
- ✅ Datos vuelven a estado anterior

**Verificar:**
```powershell
ls ./backups/backup_before_restore_*
```

---

## 7️⃣ Pruebas de Límite de Versiones

### Setup:
Crear 12 backups (para probar que mantiene solo 10)

```powershell
for ($i = 1; $i -le 12; $i++) {
    Invoke-WebRequest -Uri "http://localhost:5000/api/backup/auto-backup" -Method POST
    Start-Sleep -Seconds 1
}
```

### Verificación:
```powershell
(ls ./backups/ | Measure-Object).Count   # Debe ser 10 ó 11
```

---

## 8️⃣ Pruebas de Errores

### Test 1: Restaurar Backup Inexistente
```powershell
$uri = "http://localhost:5000/api/backup/restaurar/backup_inexistente.zip"
$response = Invoke-WebRequest -Uri $uri -Method POST -ErrorVariable err
```

**Esperado: Error 404 con mensaje**

### Test 2: Descargar Backup Inexistente
```powershell
$uri = "http://localhost:5000/api/backup/descargar/backup_inexistente.zip"
$response = Invoke-WebRequest -Uri $uri -Method GET -ErrorVariable err
```

**Esperado: Error 404**

### Test 3: Eliminar Backup
```powershell
$uri = "http://localhost:5000/api/backup/eliminar/backup_20260208_143025.zip"
$response = Invoke-WebRequest -Uri $uri -Method DELETE
$response.Content | ConvertFrom-Json | Format-List
```

**Esperado: Éxito + archivo eliminado**

---

## 9️⃣ Integración en Configuración (MANUAL)

### Paso 1: Abrir `templates/configuracion.html`

### Paso 2: Encontrar la sección adecuada
Buscar donde mostrar el componente (típicamente al final o en sección "Administración")

### Paso 3: Agregar Include
```html
<!-- Sección de Backup y Restauración -->
<div class="seccion-backup">
    <h2>🔄 Backup y Restauración</h2>
    {% include 'componente_backup.html' %}
</div>
```

### Paso 4: Reiniciar y verificar
```powershell
python run.py
# Navegar a Configuración
# Debe mostrar componente de backup
```

---

## 🔟 Verificación Final

### Checklist Completado:
- [ ] Archivos existen en rutas correctas
- [ ] No hay errores al reiniciar app
- [ ] Endpoint `/api/backup/estado` funciona
- [ ] Crear backup genera archivo `.zip`
- [ ] Listar backups muestra lista completa
- [ ] Descargar backup descarga archivo
- [ ] Exportar crea JSON
- [ ] Restaurar reemplaza BD correctamente
- [ ] Componente integrado en configuracion.html
- [ ] UI carga sin errores JavaScript
- [ ] Crear backup desde UI funciona
- [ ] Restaurar desde UI funciona
- [ ] Auto-cleanup mantiene 10 versiones
- [ ] Manejo de errores funciona

---

## 🆘 Si Algo No Funciona

### Error: ModuleNotFoundError: No module named 'app.routes.backup_api'
**Solución:** 
- Verificar que `app/routes/backup_api.py` existe
- Verificar import en `app/__init__.py`
- Reiniciar Flask

### Error: AttributeError: 'Flask' object has no attribute 'backup_manager'
**Solución:**
- Verificar que BackupManager se inicializa en `__init__.py`
- Debe estar dentro de `with app.app_context():`
- Revisar logs para ver dónde falla

### Directorio `backups/` no se crea
**Solución:**
- BackupManager debe crear automáticamente
- Si no: crear manualmente `mkdir backups`
- Verificar permisos de escritura

### API devuelve 404
**Solución:**
- Verificar que blueprint está registrado en `app/__init__.py`
- Revisar que ruta es correcta (ej: `/api/backup/crear`)
- Probar con `/api/backup/estado` más simple

---

## 📊 Comandos Útiles

```powershell
# Ver estado actual
curl http://localhost:5000/api/backup/estado

# Ver todos los backups con detalles
curl http://localhost:5000/api/backup/listar

# Crear backup
curl -X POST http://localhost:5000/api/backup/crear

# Exportar datos
curl -X POST http://localhost:5000/api/backup/exportar

# Listar archivos ZIP en directorio
Get-ChildItem .\backups\ -Filter "*.zip"

# Ver tamaño de backups
(Get-ChildItem .\backups\ -Recurse | Measure-Object -Sum Length).Sum / 1KB
```

---

**Versión**: 1.0  
**Última Actualización**: Febrero 8, 2026  
**Status**: Listo para Pruebas
