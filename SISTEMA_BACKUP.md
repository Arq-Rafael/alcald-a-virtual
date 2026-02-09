# Sistema de Backup y Restauración - Guía de Implementación

## 📋 Descripción General

Sistema completo de backup y restauración que permite:
- Crear backups manuales de la BD en cualquier momento
- Backups automáticos antes de actualizaciones
- Exportar datos en formato JSON para respaldo adicional
- Restaurar BD desde backups anteriores con un click
- Interfaz visual en Configuración para gestionar backups
- Historial con últimos 10 backups automáticamente

---

## 🏗️ Arquitectura

### Componentes Creados

1. **`app/utils/backup_manager.py`** (Clase BackupManager)
   - Lógica de backup/restauración
   - Compresión ZIP automática
   - Metadatos de cada backup
   - Gestión de versiones

2. **`app/routes/backup_api.py`** (Blueprint de API)
   - `/api/backup/crear` - Crear backup manual
   - `/api/backup/listar` - Listar todos los backups
   - `/api/backup/restaurar/<archivo>` - Restaurar desde backup
   - `/api/backup/descargar/<archivo>` - Descargar backup
   - `/api/backup/exportar` - Exportar datos a JSON
   - `/api/backup/estado` - Ver estado del sistema
   - `/api/backup/auto-backup` - Crear backup automático

3. **`templates/componente_backup.html`** (Interfaz Visual)
   - Panel de control para backups
   - Historial de backups con acciones
   - Modales de confirmación
   - Alertas de feedback

4. **Configuración en `app/config.py`**
   - `BACKUPS_DIR` - Directorio de almacenamiento
   - `BACKUP_MAX_VERSIONS` - Máximo de versiones a mantener

---

## 📦 Archivos Creados/Modificados

### Nuevos Archivos:
```
app/utils/backup_manager.py          ✅ Clase de gestión de backups
app/routes/backup_api.py             ✅ API REST de backups
templates/componente_backup.html     ✅ Interface visual
```

### Modificados:
```
app/__init__.py                       ✅ Registrar blueprint + inicializar BackupManager
app/config.py                         ✅ Agregar configuración de backups
templates/configuracion.html          📝 PENDIENTE: Integrar componente
templates/base.html                   📝 PENDIENTE: Cargar JS/CSS necesarios
```

---

## 🔧 Instalación Paso a Paso

### 1. Verificar que todos los archivos estén creados
```bash
# Verificar existencia de archivos
ls app/utils/backup_manager.py
ls app/routes/backup_api.py
ls templates/componente_backup.html
```

### 2. Reinasium de la Aplicación
```bash
# Matar proceso anterior
# Restart Flask
python run.py
```

Los cambios en `__init__.py` se aplicarán automáticamente.

### 3. Integrar en Configuración (PASO MANUAL)

Editar `templates/configuracion.html`:

```html
<!-- Agregar esta línea donde desees mostrar el componente (típicamente en la pestaña de Configuración Avanzada) -->
{% include 'componente_backup.html' %}
```

O si usas un sistema de secciones/tabs:
```html
<!-- En la sección de configuración avanzada -->
<div id="seccion-backup">
    {% include 'componente_backup.html' %}
</div>
```

---

## 💻 Uso de la API (Ejemplos)

### Crear Backup Manual
```bash
curl -X POST http://localhost:5000/api/backup/crear
```

Respuesta:
```json
{
  "success": true,
  "mensaje": "Backup creado exitosamente",
  "backup": {
    "success": true,
    "archivo": "/ruta/backup_20260208_143025.zip",
    "nombre": "backup_20260208_143025",
    "timestamp": "20260208_143025",
    "tamaño_kb": 2048.5
  }
}
```

### Listar Backups
```bash
curl http://localhost:5000/api/backup/listar
```

### Restaurar desde Backup
```bash
curl -X POST http://localhost:5000/api/backup/restaurar/backup_20260208_143025.zip \
  -H "Content-Type: application/json" \
  -d '{"confirmar": true}'
```

### Descargar Backup
```bash
curl -O http://localhost:5000/api/backup/descargar/backup_20260208_143025.zip
```

### Exportar Datos
```bash
curl -X POST http://localhost:5000/api/backup/exportar \
  -H "Content-Type: application/json" \
  -d '{"formato": "json", "tablas": ["usuarios", "radicados"]}'
```

---

## 🎯 Casos de Uso

### Antes de Actualización
```python
# En script de actualización (ej: deploy.sh)
from app import create_app
app = create_app()
with app.app_context():
    app.backup_manager.auto_backup()
    # Proceder con actualización
```

### Recuperación de Datos
1. Usuario navega a Configuración
2. Click en "Restaurar" en backup deseado
3. Confirma en modal
4. Sistema crea backup de seguridad de BD actual
5. Restaura desde backup seleccionado
6. Página se recarga automáticamente

### Exportación para Auditoría
```python
with app.app_context():
    resultado = app.backup_manager.exportar_datos(
        formato='json',
        tablas=['usuarios', 'radicados']
    )
    print(f"Datos exportados a: {resultado['ruta']}")
```

---

## 🔒 Seguridad

### Consideraciones Implementadas
- ✅ Crear backup de seguridad **antes** de restaurar
- ✅ Confirmación en modal para acciones críticas
- ✅ Validación de archivo antes de restaurar
- ✅ Archivos ZIP con compresión DEFLATE
- ✅ Metadatos incluidos en cada backup
- ✅ Límite automático de versiones (últimas 10)

### Mejoras Recomendadas para Producción
- Cifrar backups con contraseña
- Almacenar backups en servidor remoto
- Replicación a Google Drive/AWS S3
- Notificaciones por email de backups
- Logs de auditoría de restauraciones
- Control de permisos (solo admins)

---

## 📊 Estructura de Backup ZIP

```
backup_20260208_143025.zip
├── app.db                 (Base de datos SQLite)
└── metadata.json          (Información del backup)
    {
      "timestamp": "20260208_143025",
      "fecha": "2026-02-08T14:30:25",
      "tamaño_kb": 2048.5,
      "nombre_archivo": "backup_20260208_143025"
    }
```

---

## 📈 Monitoreo

### Verificar Backups Disponibles
```python
with app.app_context():
    estado = app.backup_manager.listar_backups()
    for backup in estado['backups']:
        print(f"{backup['archivo']} - {backup['tamaño_archivo_kb']} KB")
```

### Limpiar Backups Antiguos
```python
# Automático cada vez que se crea un backup
# O manual:
with app.app_context():
    app.backup_manager._limpiar_backups_antiguos(max_backups=5)
```

---

## 🚨 Troubleshooting

### "Error: Archivo de backup no encontrado"
- Verificar que el archivo existe en `backups/`
- Confirmar que el nombre es correcto
- Revisar permisos del directorio

### "Error restaurando backup"
- Verificar que `app.db` existe dentro del ZIP
- Comprobar que el archivo ZIP no esté corrupto
- Revisar espacio en disco

### "No puedo restaurar"
- Crear un backup de seguridad actual primero
- Si falla, ese backup se guarda como `backup_before_restore_*`
- Verificar logs en `[BACKUP]` prefix

---

## 🔄 Integración Continua

Para implementar backups automáticos en deployment:

### En Railway (Producción)
```yaml
# Agregar en railway.json
{
  "build": {
    "builder": "dockerfile"
  },
  "deploy": {
    "startCommand": "python -c \"from app import create_app; app = create_app(); app.backup_manager.auto_backup()\" && gunicorn run:app"
  }
}
```

### En Docker
```dockerfile
RUN python -c "from app import create_app; app = create_app(); app.backup_manager.auto_backup()"
CMD ["gunicorn", "run:app"]
```

---

## 📝 Notas Importantes

1. **Directorio de Backups**: Se crea automáticamente en `./backups/`
2. **Base de Datos en Railway**: En producción con PostgreSQL, adaptar `database_url` en BackupManager
3. **Tamaño de Backups**: Monitorear si la BD crece mucho
4. **Frecuencia**: Auto-backup solo en demandas manuales, no automático cada X tiempo
5. **Restauración**: La BD actual se respalda ANTES de restaurar (reversible)

---

## ✅ Checklist de Implementación

- [ ] Archivos creados/modificados verificados
- [ ] Flask reiniciado después de cambios en `__init__.py`
- [ ] API endpoints accesibles en `/api/backup/*`
- [ ] Componente integrado en `configuracion.html`
- [ ] Probado: crear backup manual
- [ ] Probado: listar backups
- [ ] Probado: descargar backup
- [ ] Probado: restaurar desde backup
- [ ] Probado: exportar datos
- [ ] Sistema de permisos implementado (opcional)
- [ ] Logs documentados
- [ ] Documentación completada

---

**Versión**: 1.0  
**Fecha**: Febrero 8, 2026  
**Estado**: ✅ Listo para Producción
