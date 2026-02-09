# 🎯 QUICK REFERENCE - Sistema de Backup

## 🔗 API Endpoints

### Estado del Sistema
```bash
GET /api/backup/estado
```
**Retorna:** DB size, backup count, espacio usado

---

### Crear Backup Manual
```bash
POST /api/backup/crear
```
**Body:** (vacío)  
**Retorna:** Datos del backup recién creado

---

### Listar Backups
```bash
GET /api/backup/listar
```
**Retorna:** Array de backups con metadata

---

### Restaurar Backup
```bash
POST /api/backup/restaurar/{nombre_archivo}.zip
Content-Type: application/json

{"confirmar": true}
```
**Requiere:** `confirmar: true`  
**Retorna:** Éxito/Error  

---

### Descargar Backup
```bash
GET /api/backup/descargar/{nombre_archivo}.zip
```
**Retorna:** Archivo ZIP descargable

---

### Eliminar Backup
```bash
DELETE /api/backup/eliminar/{nombre_archivo}.zip
```
**Retorna:** Confirmación de eliminar

---

### Exportar Datos (JSON)
```bash
POST /api/backup/exportar
Content-Type: application/json

{
  "formato": "json",
  "tablas": ["usuarios", "radicados"]
}
```
**Tablas disponibles:** usuarios, radicados, radicado_arborea  
**Retorna:** Ruta de archivo JSON

---

### Auto-Backup
```bash
POST /api/backup/auto-backup
```
**Retorna:** Datos backup + Limpia versiones viejas

---

## 🗂️ Rutas de Archivo

```
./backups/                          # Directorio de backups
├── backup_20260208_143025.zip
├── backup_20260208_143045.zip
└── backup_before_restore_*.zip

./documentos_generados/              # Exportaciones JSON
└── export_TIMESTAMP.json
```

---

## ⚙️ Configuración (app/config.py)

```python
BACKUPS_DIR = BASE_DIR / "backups"      # Ubicación
BACKUP_MAX_VERSIONS = 10                 # Máx. versiones mantener
```

---

## 🧪 Pruebas Rápidas

### Con PowerShell:
```powershell
# Ver estado
curl http://localhost:5000/api/backup/estado

# Crear backup
curl -X POST http://localhost:5000/api/backup/crear

# Listar backups
curl http://localhost:5000/api/backup/listar

# Restaurar (cambiar nombre)
curl -X POST "http://localhost:5000/api/backup/restaurar/backup_TIMESTAMP.zip" `
  -H "Content-Type: application/json" `
  -d '{"confirmar":true}'
```

---

## 📱 UI en Configuración

```html
<!-- Agregar en templates/configuracion.html -->
{% include 'componente_backup.html' %}
```

---

## 🔄 Flujo Rápido de Restauración

1. **Crear backup** → `POST /api/backup/crear`
2. **Listar** → `GET /api/backup/listar`
3. **Encontrar archivo** → Buscar en historial
4. **Restaurar** → `POST /api/backup/restaurar/archivo.zip` + confirmar
5. **Sistema crea** → `backup_before_restore_TIMESTAMP.zip`
6. **Recarga página**

---

## 🚀 Inicialización en app/__init__.py

```python
# Línea ~58
from .routes.backup_api import backup_api

# Línea ~60  
app.register_blueprint(backup_api)

# Línea ~120
with app.app_context():
    from app.utils.backup_manager import BackupManager
    app.backup_manager = BackupManager(app)
```

---

## 🛡️ Seguridad

| Acción | Protección |
|--------|-----------|
| Crear | ✅ Automático - no requiere confirmación |
| Restaurar | ✅ Modal confirma + crea backup de seguridad |
| Exportar | ✅ Solo usuarios autenticados |
| Eliminar | ✅ Eliminación permanente |

---

## 📊 Estado en Logs

```
[BACKUP] BackupManager inicializado                    # Al iniciar
[BACKUP] Backup creado: backup_20260208_143025.zip    # Crear backup
[BACKUP] Restaurando desde: backup_20260208_143025    # Restaurar
[BACKUP] Limpiando backups antiguos                   # Auto-cleanup
```

---

## ❌ Errores Comunes

| Error | Solución |
|-------|----------|
| ModuleNotFoundError: backup_api | Reiniciar Flask |
| AttributeError: backup_manager | Verificar __init__.py |
| Directorio backups/ no existe | Se crea automáticamente, o crear manualmente |
| Archivo no encontrado | Verificar nombre exacto en listar |
| Falla al restaurar ZIP | Archivo corrupto o BD incompatible |

---

## 🎯 Tamaño Típico

```
app.db               ~2-5 MB (SQLite local)
backup_XXXX.zip      ~0.5-2 MB (comprimido DEFLATE)
10 backups           ~5-20 MB total
JSON export          ~1-3 MB
```

---

## ⏱️ Tiempos Típicos

| Operación | Tiempo |
|-----------|--------|
| Crear backup | 1-2 segundos |
| Restaurar | 2-3 segundos |
| Exportar JSON | 1-2 segundos |
| Listar backups | <100ms |
| Auto-cleanup | <500ms |

---

## 🔑 Clase BackupManager

### Métodos Disponibles:
```python
app.backup_manager.crear_backup()           # dict
app.backup_manager.restaurar_backup(arch)   # dict
app.backup_manager.listar_backups()          # dict
app.backup_manager.eliminar_backup(arch)     # bool
app.backup_manager.exportar_datos(fmt, tabs) # dict
app.backup_manager.auto_backup()             # dict
app.backup_manager._limpiar_backups_antiguos(max) # None
```

---

## 📝 Estructura de Respuesta (JSON)

### Crear Backup:
```json
{
  "success": true,
  "mensaje": "Backup creado exitosamente",
  "backup": {
    "archivo": "/ruta/backup_XXXX.zip",
    "nombre": "backup_XXXX",
    "timestamp": "YYYYMMDD_HHMMSS",
    "tamaño_kb": 2048.5
  }
}
```

### Listar:
```json
{
  "success": true,
  "backups": [
    {
      "archivo": "/backups/backup_XXXX.zip",
      "nombre": "backup_XXXX",
      "tamaño_archivo_kb": 2048.5,
      "timestamp": "YYYYMMDD_HHMMSS",
      "fecha": "2026-02-08T14:30:25"
    }
  ],
  "total_backups": 5,
  "espacio_total_kb": 10240
}
```

---

## 🎨 Componentes UI

### Elemento: `componente_backup.html`
```html
<!-- Estado actual -->
- DB Size
- Backup Count
- Total Space

<!-- Botones Acción -->
- Crear Backup Manual
- Exportar Datos
- Auto-Backup

<!-- Tabla Historial -->
- Nombre | Fecha | Tamaño | Acciones
- Acciones: Restaurar | Descargar | Deletar
```

---

## 🔌 Integración con Rutas

```python
# En app/routes/backup_api.py
@backup_api.route('/crear', methods=['POST'])
@backup_api.route('/listar', methods=['GET'])
@backup_api.route('/restaurar/<archivo>', methods=['POST'])
# ... etc
```

---

## 📦 Dependencias Usadas

```python
# backup_manager.py
import zipfile       # Compresión ZIP
import json         # Metadata
import logging      # Logs
from pathlib import Path
from datetime import datetime

# backup_api.py
from flask import Blueprint, request, jsonify, send_file
```

No requiere dependencias externas. Solo librerías estándar de Python.

---

## 🧹 Auto-Limpieza

```python
# Se ejecuta automáticamente después de crear backup
# Mantiene solo últimas N versiones
_limpiar_backups_antiguos(max=10)

# Lógica:
# 1. Lista todos los backups
# 2. Ordena por fecha modificación (más nuevo primero)
# 3. Elimina backups 11+ en adelante
```

---

## 🔄 Ciclo de Restablecimiento

1. Usuario click "Restaurar"
2. Modal pide confirmación
3. `POST /api/backup/restaurar/archivo.zip`
4. BackupManager:
   - Mover app.db → app.db.old (seguridad)
   - Descomprime ZIP
   - Extrae app.db
   - Valida presencia de archivo
   - Reemplaza app.db activo
5. Frontend recarga página
6. Nuevos datos visibles

---

## 📋 Validaciones Implementadas

- ✅ Verificar ZIP válido
- ✅ Verificar app.db existe en ZIP
- ✅ Verificar espacio en disco
- ✅ Verificar permisos de escritura
- ✅ Crear backup de seguridad ANTES de restaurar
- ✅ Confirmar vía POST body
- ✅ Logging de todas las operaciones

---

## 🎬 Inicio Rápido (Desarrollo)

```powershell
# 1. Reiniciar Flask
python run.py

# 2. Verificar inicialización
# Buscar en logs: "[BACKUP] BackupManager inicializado"

# 3. Probar API
curl http://localhost:5000/api/backup/estado

# 4. Integrar UI en configuracion.html
# Agregar: {% include 'componente_backup.html' %}

# 5. Test completo
# - Navegar a Configuración
# - Hacer click en "Crear Backup Manual"
# - Verificar archivo en ./backups/
```

---

## 📞 Contacto / Soporte

- **Documentación Técnica:** `SISTEMA_BACKUP.md`
- **Testing Detallado:** `TESTING_BACKUP.md`
- **Resumen Ejecutivo:** `BACKUP_RESUMEN.md`
- **Esta tarjeta:** `QUICK_REFERENCE_BACKUP.md`

---

**Última actualización:** Febrero 8, 2026  
**Versión:** 1.0  
**Estado:** ✅ Listo para Pruebas
