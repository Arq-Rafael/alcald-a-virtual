# Guía de Verificación - RBAC y Foto de Perfil

## ✅ Cambios Realizados

### 1. **Arreglo de Persistencia de Fotos de Perfil**

**Problema solucionado:**
- Las fotos de perfil no se guardaban correctamente en la base de datos
- La ruta `UPLOADS_DIR` era un objeto Path y no se convertía a string para `send_from_directory()`
- Resultado: Las fotos se perdían después de logout/login

**Solución implementada:**
- Línea 124 en `app/__init__.py`: Convertir `UPLOADS_DIR` a string
- Línea 72 en `app/routes/perfil.py`: Convertir `BASE_DIR` a string

**Verificación:**
```bash
# El servidor debe estar corriendo
http://localhost:5000/perfil

# Subir una foto
# Logout y Login nuevamente
# La foto debe persistir
```

---

### 2. **Sistema RBAC (Control de Acceso Basado en Roles)**

Se implementó un completo sistema de control de acceso que restringe módulos según la secretaría del usuario.

#### **Matriz de Permisos (Verificado ✅):**

| Secretaría | Módulos Accesibles | No Permite |
|---|---|---|
| **Planeación** | redactar, solicitudes, calendario, participación, geoportal, seguimiento, riesgo, contratos, certificados | ❌ configuracion |
| **Gobierno** | redactar, solicitudes, calendario, participación, riesgo, contratos | ❌ geoportal, seguimiento, certificados, configuracion |
| **Hacienda** | redactar, solicitudes, calendario | ❌ participación, geoportal, seguimiento, riesgo, contratos, configuracion |
| **D. Rural** | redactar, solicitudes, calendario, riesgo | ❌ participación, geoportal, seguimiento, contratos, configuracion |
| **D. Social** | redactar, solicitudes, calendario, riesgo | ❌ participación, geoportal, seguimiento, contratos, configuracion |
| **Admin** | ✅ TODOS los módulos | Ninguno |

---

## 🧪 Cómo Probar

### Test 1: Verificar Persistencia de Fotos

```
1. Inicia sesión como admin (admin / admin123)
2. Ve a http://localhost:5000/perfil
3. Haz clic en "Subir Foto de Perfil"
4. Sube una imagen PNG o JPG
5. Verifica que aparece en la pantalla
6. Cierra sesión (Logout)
7. Inicia sesión nuevamente
8. Ve a /perfil
   ✅ La foto debe seguir ahí
   ✅ La URL en el navegador debe ser /uploads/perfiles/admin.jpg
```

### Test 2: Verificar Control de Acceso - Usuario Planeación

```
1. Inicia sesión como planeacion (planeacion / planeacion123)
2. En el Dock (navegación lateral):
   ✅ VES: Redactar, Solicitudes, Calendario, Ciudadanía, Geoportal, Metas, Riesgo, Contratos, IA
   ❌ NO VES: Configuración
3. Intenta acceder directamente a /configuracion
   ❌ Error 403 Forbidden
```

### Test 3: Verificar Control de Acceso - Usuario Gobierno

```
1. Inicia sesión como gobierno (gobierno / gobierno123)
2. En el Dock:
   ✅ VES: Redactar, Solicitudes, Calendario, Ciudadanía, Riesgo, Contratos, IA
   ❌ NO VES: Geoportal, Metas, Certificados, Configuración
3. Intenta acceder directo a:
   - /geoportal → Error 403 ❌
   - /seguimiento → Error 403 ❌
   - /certificados → Error 403 ❌
```

### Test 4: Verificar Control de Acceso - Usuario Hacienda

```
1. Inicia sesión como hacienda (hacienda / hacienda123)
2. En el Dock:
   ✅ VES: Redactar, Solicitudes, Calendario, IA
   ❌ NO VES: Ciudadanía, Geoportal, Metas, Riesgo, Contratos, Certificados, Configuración
3. Intenta acceder directo a /contratos → Error 403 ❌
```

### Test 5: Verificar Admin Tiene Acceso Completo

```
1. Inicia sesión como admin (admin / admin123)
2. En el Dock:
   ✅ VES: Todos los módulos incluyendo Configuración
3. Puedes acceder a:
   - /solicitudes ✅
   - /certificados ✅
   - /geoportal ✅
   - /riesgo ✅
   - /contratos ✅
   - /configuracion ✅
```

---

## 📁 Archivos Modificados

### Nuevos Archivos:
```
app/utils/rbac.py                    # Sistema RBAC completo (204 líneas)
test_rbac.py                          # Script de prueba automatizado
RBAC_IMPLEMENTATION.md                # Documentación del RBAC
```

### Archivos Modificados:

**1. app/__init__.py**
- Línea 8: Agregado import de `rbac`
- Línea 86-113: Actualizado context processor con funciones RBAC
- Línea 124: Convertido `UPLOADS_DIR` a string

**2. app/routes/perfil.py**
- Línea 1: No cambio en imports
- Línea 72: Convertido `BASE_DIR` a string en `os.path.join()`

**3. app/routes/solicitudes.py**
- Línea 11: Agregado `from app.utils.rbac import require_permission`
- Línea 18: Agregado `@require_permission('solicitudes')` a ruta `/solicitudes`

**4. app/routes/certificados.py**
- Línea 11: Agregado `from app.utils.rbac import require_permission`
- Línea 358: Agregado `@require_permission('certificados')` a ruta `/certificados`

**5. app/routes/participacion.py**
- Línea 1: Agregado `from app.utils.rbac import require_permission`
- Línea 56: Agregado `@require_permission('participacion')` a ruta

**6. app/routes/seguimiento.py**
- Línea 8: Agregado `from app.utils.rbac import require_permission`
- Línea 157: Agregado `@require_permission('seguimiento')` a ruta

**7. app/routes/usos.py**
- Línea 10: Agregado `from app.utils.rbac import require_permission`
- Línea 226: Agregado `@require_permission('geoportal')` a ruta

**8. app/routes/riesgo_api.py**
- Línea 5: Agregado `from app.utils.rbac import require_permission`
- Línea 111: Agregado `@require_permission('riesgo')` a POST `/api/riesgo/arborea`
- Línea 251: Agregado `@require_permission('riesgo')` a GET `/api/riesgo/arborea`

**9. app/routes/contratos_api.py**
- Línea 6: Agregado `from app.utils.rbac import require_permission`
- Línea 349: Agregado `@require_permission('contratos')` a `/importar`
- Línea 443: Agregado `@require_permission('contratos')` a GET lista

**10. app/routes/configuracion.py**
- Línea 4: Agregado `from app.utils.rbac import require_permission`
- Línea 6: Corregido import de `jsonify`
- Línea 42: Agregado `@require_permission('configuracion')` antes de `@admin_required`

**11. templates/base.html**
- Líneas 302-430: Reescrita sección `dock-container` con condicionales RBAC
- Cada módulo ahora tiene `{% if has_permission('modulo') %}`

---

## 🔧 Estructura del RBAC

### Componentes Principales:

```python
# 1. Mapeo de Permisos
SECRETARIA_PERMISSIONS = {
    'planeacion': {...},      # 9 módulos
    'gobierno': {...},        # 6 módulos
    'hacienda': {...},        # 3 módulos
    'desarrollo_rural': {...}, # 4 módulos
    'desarrollo_social': {... }, # 4 módulos
}

# 2. Funciones de Verificación
has_permission('modulo')           # Verifica si puede acceder
get_accessible_modules()           # Lista módulos permitidos
get_user_role()                    # Obtiene rol de sesión
get_user_secretaria()              # Obtiene secretaría de sesión

# 3. Decorador de Protección
@require_permission('modulo')      # Protege rutas HTTP
```

---

## 🚀 Próximas Mejoras

1. **Auditoría completa**: Registrar todos los intentos de acceso denegado
2. **Permisos personalizados**: UI para crear/editar permisos por secretaría
3. **Invalidación de caché**: Actualizar permisos sin reiniciar
4. **API de permisos**: Endpoint para verificar permisos desde JavaScript
5. **Reporte de accesos**: Dashboard de intentos de acceso por usuario/módulo

---

## 📞 Soporte

Si encuentras problemas:

1. Verifica que los usuarios tengan `secretaria` definida en BD
2. Revisa los logs del servidor: `[Migration]` o `WARNING - User X denied access`
3. Limpia cache/cookies y reintenta login
4. Reinicia el servidor si hiciste cambios manuales en la BD

---

## ✨ Cambios Resumidos

| Tarea | Estado | Nota |
|---|---|---|
| Arreglar persistencia de fotos ✅ | **COMPLETO** | fotos ahora se mantienen tras logout/login |
| Crear sistema RBAC ✅ | **COMPLETO** | 204 líneas en `rbac.py` |
| Proteger módulos con decoradores ✅ | **COMPLETO** | 8 rutas protegidas |
| Actualizar navegación con condicionales ✅ | **COMPLETO** | Dock dinámico por secretaría |
| Documentación ✅ | **COMPLETO** | RBAC_IMPLEMENTATION.md |
| Pruebas automatizadas ✅ | **COMPLETO** | test_rbac.py pasa todos los tests |

