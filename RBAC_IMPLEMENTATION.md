# Sistema RBAC Implementado - Documentación

## Resumen de Cambios

Se ha implementado un completo sistema de Control de Acceso Basado en Roles (RBAC) que restringe el acceso a los módulos según la secretaría/departamento del usuario.

### 1. Arreglos de Persistencia de Fotos de Perfil

**Archivos modificados:**
- `app/__init__.py` - Línea 124: Convertir `UPLOADS_DIR` a string en `send_from_directory()`
- `app/routes/perfil.py` - Línea 72: Convertir `BASE_DIR` a string en `os.path.join()`

**Problema resuelto:**
- La ruta `UPLOADS_DIR` era un objeto `pathlib.Path`, no un string, lo que causaba errores al servir archivos
- Las fotos de perfil ahora se sirven correctamente vía `/uploads/<path:filename>` route

### 2. Sistema RBAC (Role-Based Access Control)

**Nuevo archivo:** `app/utils/rbac.py`

**Funcionalidades implementadas:**

#### Mapeo de Permisos por Secretaría:

```python
SECRETARIA_PERMISSIONS = {
    'planeacion': {'redactar', 'solicitudes', 'calendario', 'participacion', 'geoportal', 'seguimiento', 'riesgo', 'contratos', 'certificados'},
    'gobierno': {'redactar', 'solicitudes', 'calendario', 'participacion', 'riesgo', 'contratos'},
    'hacienda': {'redactar', 'solicitudes', 'calendario'},
    'desarrollo_rural': {'redactar', 'solicitudes', 'calendario', 'riesgo'},
    'desarrollo_social': {'redactar', 'solicitudes', 'calendario', 'riesgo'},
}
```

#### Funciones principales:

1. **`has_permission(module_name)`**
   - Verifica si el usuario actual tiene acceso a un módulo
   - Admin/superadmin tienen acceso a todo
   - Usuarios normales requieren secretaría definida

2. **`@require_permission(module_name, abort_code=403)`**
   - Decorador para proteger rutas
   - Redirige a login si no hay sesión
   - Retorna error 403 si no tiene permiso

3. **`get_accessible_modules()`**
   - Retorna lista de módulos a los que el usuario puede acceder
   - Usado para filtrar navegación

4. **`get_user_secretaria()`** y **`get_user_role()`**
   - Obtienen secretaría y rol del usuario en sesión

### 3. Protección de Rutas

Se agregó `@require_permission('modulo')` a las siguientes rutas principales:

| Módulo | Archivo | Ruta | Decorador |
|--------|---------|------|-----------|
| Solicitudes | `app/routes/solicitudes.py` | `/solicitudes` | `@require_permission('solicitudes')` |
| Certificados | `app/routes/certificados.py` | `/certificados` | `@require_permission('certificados')` |
| Participación | `app/routes/participacion.py` | `/participacion` | `@require_permission('participacion')` |
| Seguimiento | `app/routes/seguimiento.py` | `/seguimiento` | `@require_permission('seguimiento')` |
| Geoportal (Usos) | `app/routes/usos.py` | `/usos_suelo` | `@require_permission('geoportal')` |
| Gestión del Riesgo | `app/routes/riesgo_api.py` | `/api/riesgo/arborea` | `@require_permission('riesgo')` |
| Contratos | `app/routes/contratos_api.py` | `/contratos` | `@require_permission('contratos')` |
| Configuración | `app/routes/configuracion.py` | `/configuracion` | `@require_permission('configuracion')` |

### 4. Actualización de Navegación

**Archivo modificado:** `templates/base.html` - Sección `dock-container` (líneas 302-430)

Se reemplazó navegación hardcodeada con rendering condicional:

```jinja2
<!-- Redactar Oficio -->
{% if has_permission('redactar') %}
<a href="{{ url_for('ia.letter') }}" class="dock-item item-letter">
  <i class="bi bi-pencil-square"></i>
  <span class="label">Redactar</span>
</a>
{% endif %}
```

Módulos con condicionales:
- ✅ Redactar (acción `redactar`)
- ✅ Solicitudes
- ✅ Calendario
- ✅ Participación/Ciudadanía
- ✅ Geoportal
- ✅ Seguimiento/Metas
- ✅ Gestión del Riesgo
- ✅ Contratos
- ✅ Certificados
- ✅ IA (siempre visible para todos)
- ✅ Configuración (solo admin)

### 5. Context Processor Actualizado

**Archivo:** `app/__init__.py` - Función `inject_utilities()`

Se agregaron funciones RBAC al contexto global de Jinja2:
- `has_permission(module)` - Verifican permisos en plantillas
- `get_accessible_modules()` - Obtienen lista de módulos accesibles
- `get_user_role()` - Obtienen rol del usuario
- `get_user_secretaria()` - Obtienen secretaría del usuario

### 6. Mapeo de Alias de Módulos

Para mayor flexibilidad, se define alias que apuntan a los mismos módulos:

```python
MODULES_ALIAS = {
    'redactar': ['redactar_oficios', 'oficios'],
    'solicitudes': ['solicitudes', 'gestionar_solicitudes'],
    'calendario': ['calendario', 'events'],
    'participacion': ['participacion', 'radicados'],
    'geoportal': ['geoportal', 'usos', 'catastro'],
    'seguimiento': ['seguimiento', 'metas', 'informes'],
    'riesgo': ['riesgo', 'contingencia', 'planes_contingencia'],
    'contratos': ['contratos', 'contratacion'],
}
```

## Cómo Funciona

### Flujo de Autenticación y Autorización:

1. Usuario inicia sesión en `/login`
   - Se valida usuario/contraseña
   - Se carga `Usuario.secretaria` en sesión

2. Usuario accede a módulo (ej: `/solicitudes`)
   - Decorator `@require_permission('solicitudes')` se ejecuta
   - Llama a `has_permission('solicitudes')`
   - Obtiene `usuario.secretaria` de sesión
   - Verifica si secretaría tiene permiso en `SECRETARIA_PERMISSIONS`
   - Si ✓ permite acceso; Si ✗ retorna 403

3. Navegación (dock-container)
   - Jinja2 evalúa `{% if has_permission('modulo') %}`
   - Solo muestra items que usuario puede acceder
   - Admins ven todos los módulos excepto según reglas

### Permisos Especiales:

**Admin y Superadmin:**
- Acceso total a todos los módulos
- `@require_permission()` no los restringe

**Solo Configuración:**
- Solo admin puede acceder via `@require_permission('configuracion')`
- Tiene validación doble `@require_permission + @admin_required`

## Pruebas Recomendadas

### 1. Test de Persistencia de Fotos:

```bash
1. Logout && Login
2. Ir a /perfil
3. Subir nueva foto de perfil
4. Logout
5. Login de nuevo
6. Verificar que la foto persiste
```

### 2. Test de Control de Acceso:

**Usuario: planeacion**
- ✅ Debe ver: redactar, solicitudes, calendario, participación, geoportal, seguimiento, riesgo, contratos, certificados, ia
- ❌ No debe ver: configuración
- ❌ Acceso directo a `/configuracion` → Error 403

**Usuario: gobierno**
- ✅ Debe ver: redactar, solicitudes, calendario, participación, riesgo, contratos, ia
- ❌ No debe ver: geoportal, seguimiento, certificados, configuración

**Usuario: hacienda**
- ✅ Debe ver: redactar, solicitudes, calendario, ia
- ❌ No debe ver: participación, geoportal, seguimiento, riesgo, contratos, certificados, configuración

**Usuario: admin**
- ✅ Debe ver: TODOS los módulos
- ✅ Puede acceder a `/configuracion`

## Logs de Ejecución

La aplicación registra intentos de acceso denegado:

```
WARNING - User planeacion denied access to module: configuracion
WARNING - User hacienda denied access to module: contratos
```

## Compatibilidad

- ✅ SQLite (desarrollo)
- ✅ PostgreSQL (producción en Railway)
- ✅ Navegación iOS dock anterior se mantiene
- ✅ Glassmorphism effects persisten
- ✅ Funcionalidad 2FA no afectada

## Próximas Mejoras Sugeridas

1. **Auditoría de accesos**: Registrar todos los intentos de acceso a módulos
2. **Permisos granulares**: Permitir crear permisos personalizados por usuario
3. **Roles dinámicos**: Permitir crear roles personalizados en UI
4. **Invalidación de caché**: Actualizar permisos sin reiniciar servidor
5. **API de permisos**: Endpoint para cliente JS verificar permisos antes de navegar

## Archivos Afectados

**Creados:**
- `app/utils/rbac.py` - Sistema RBAC completo

**Modificados:**
- `app/__init__.py` - Context processor actualizado
- `app/routes/*.py` - Decoradores `@require_permission` agregados (8 rutas)
- `templates/base.html` - Navegación condicional en dock-container

**Sin cambios (compatibles):**
- Modelos de usuario - `secretaria` ya existía
- Templates existentes - Solo se actualizó base.html
- Database schema - Sin cambios (0 migraciones necesarias)
