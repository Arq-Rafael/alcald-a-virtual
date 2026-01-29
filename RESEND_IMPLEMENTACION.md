# Resend Integration - Implementación Completa

## 📧 Características implementadas

### 1. Email de Bienvenida
✅ Se envía cuando se **crea un nuevo usuario**
- Diseño profesional con branding de Alcaldía
- Instrucciones claras de acceso
- Link a soporte

### 2. Verificación de Primer Acceso
✅ En el **primer login** se requiere código de verificación
- Código único de 6 dígitos
- Válido por 15 minutos
- Enviado al email del usuario
- Pantalla dedicada para ingresar el código

### 3. Confirmación de Cambio de Contraseña
✅ Se envía cuando el usuario **cambia su contraseña**
- Confirmación de cambio exitoso
- Alertas de seguridad
- Información de soporte

---

## 🔄 Flujo de Autenticación (Mejorado)

```
┌─────────────────────────────────────┐
│     Usuario intenta Login           │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  ✓ Verifica usuario y contraseña    │
└──────────────┬──────────────────────┘
               │
               ▼
        ┌─────────────┐
        │ ¿Primer     │
        │ Acceso?     │
        └──┬──────┬───┘
      SÍ   │      │   NO
           │      │
    ┌──────▼─┐    │
    │Genera  │    │
    │código  │    │
    │6 dígit.│    │
    └──────┬─┘    │
           │      │
    ┌──────▼──────▼─────────────────────┐
    │  📧 Envía email con código        │ (RESEND)
    │     + Instrucciones               │
    └──────┬────────────────────────────┘
           │
    ┌──────▼──────────────────────────┐
    │  🔐 Redirige a verificación     │
    │  Usuario introduce código       │
    └──────┬─────────────────────────┘
           │
        ┌──┴──┐
        │     │
        │  ¿Es correcto?
        │     │
    SÍ  │     │   NO
    ┌───▼──┐  │  ┌──────────────┐
    │Marca │  │  │Error, reint. │
    │compr.│  │  └──────────────┘
    └───┬──┘  │       ▲
        │     └───────┘
        │
    ┌───▼───────────────────────────┐
    │ ✅ Acceso permitido           │
    │    Usuario va al Dashboard    │
    └───────────────────────────────┘
```

---

## 📁 Archivos creados/modificados

### Nuevos archivos:
- `app/utils/email_resend.py` (284 líneas)
  - Función principal: `send_email_resend()`
  - Plantillas: `send_welcome_email()`, `send_first_login_code_email()`, `send_password_changed_email()`
  
- `templates/verificar_primer_acceso.html`
  - Interfaz moderna para ingreso de código
  - Validación en tiempo real
  - Diseño responsive

- `RESEND_SETUP.md`
  - Guía de configuración paso a paso
  - Troubleshooting

### Archivos modificados:
- `app/config.py`
  - Agregado: `RESEND_API_KEY` config
  - Agregado: `EMAIL_PROVIDER = 'resend'` por defecto

- `app/models/usuario.py`
  - Nuevos campos de BD:
    - `primer_acceso` (bool)
    - `codigo_primer_acceso` (str)
    - `codigo_primer_acceso_expira` (datetime)
    - `primer_acceso_verificado` (datetime)
  - Nuevos métodos:
    - `generar_codigo_primer_acceso()`
    - `verificar_codigo_primer_acceso(codigo)`

- `app/routes/auth.py`
  - Lógica de primer acceso en `login()`
  - Nueva ruta: `@auth_bp.route('/verificar-primer-acceso')`

- `app/utils/seguridad.py`
  - Importados: funciones Resend
  - Actualizado: `enviar_notificacion_registro()` usa Resend primero

- `requirements.txt`
  - Agregado: `resend>=2.21.0`

---

## 🚀 Configuración necesaria en Railway

**Paso 1:** En tu servicio de Railway
1. Ve a **Settings** → **Variables**
2. Agrega:
   ```
   RESEND_API_KEY=re_xxxxxxxxxxxx
   ```

**Paso 2:** Obtén tu API key
- Crea cuenta gratis en https://resend.com
- Dashboard → API Keys
- Copia la key (empieza con `re_`)

---

## ✅ Checklist

- [x] SDK Resend instalado
- [x] Módulo `email_resend.py` creado
- [x] Modelo Usuario actualizado (campos nuevos)
- [x] Rutas de autenticación mejoradas
- [x] Plantilla HTML para verificación
- [x] Documentación completa
- [x] Código subido a GitHub
- [ ] **PENDIENTE:** Agregar RESEND_API_KEY en Railway variables

---

## 📊 Comportamiento esperado

### Escenario 1: Nuevo usuario
```
1. Admin crea usuario "juan@example.com"
2. Juan recibe email de bienvenida
3. Juan intenta login
4. Sistema genera código de 6 dígitos
5. Sistema envía código por email
6. Juan ve pantalla: "Introduce código"
7. Juan copia código del email
8. Juan ingresa código
9. ✅ Acceso permitido
```

### Escenario 2: Usuario ya verificado
```
1. Juan ya pasó primer acceso
2. Juan intenta login
3. Contraseña correcta
4. ✅ Acceso inmediato al dashboard
```

---

## 🔧 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'resend'"
```bash
pip install resend>=2.21.0
```

### Error: "RESEND_API_KEY not configured"
- Verificar que agregaste la variable en Railway
- Verificar en local que está en `.env`

### Emails no llegan
- Comprueba carpeta de spam
- Verifica que la API key sea válida
- En Railway, haz deploy para que tome nueva config

### Código expirado
- Código válido por 15 minutos
- Usuario puede pedir un nuevo code (opcional en futuro)

---

## 💡 Próximas mejoras (opcionales)

- [ ] Botón "Reenviar código" en pantalla de verificación
- [ ] Limitar intentos de código a 3 por usuario
- [ ] Registrar en auditoría cada intento de verificación
- [ ] Enviar email si múltiples fallos (alerta de seguridad)
- [ ] Verificación por SMS (Twilio)
- [ ] Autenticador TOTP (ya implementado)

---

**Creado:** 28/01/2026
**Versión:** 1.0
**Estado:** ✅ Listo para usar
