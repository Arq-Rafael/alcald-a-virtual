# Configuración de Resend en Railway

## ¿Qué es Resend?
Resend es un servicio de envío de emails vía API REST (HTTPS) que funciona perfectamente en entornos como Railway que bloquean conexiones SMTP (puerto 587).

**Sitio web:** https://resend.com

## Pasos para configurar:

### 1. Obtener la API Key
1. Ve a https://resend.com/dashboard
2. Inicia sesión o crea una cuenta
3. En el dashboard, ve a **API Keys**
4. Copia tu API Key (comienza con `re_`)
   - Puedes usar la key de testing para probar
   - Necesitarás una key de producción para dominio personalizado

### 2. Agregar la variable a Railway

En tu app de Railway:

1. Ve a **Settings** → **Variables**
2. Agrega una nueva variable:
   - **Key:** `RESEND_API_KEY`
   - **Value:** tu_api_key_aqui (ej: `re_xxxxxxxxxxxx`)
3. Haz clic en **Deploy** para aplicar

### 3. (Opcional) Configurar dominio personalizado

Por defecto, Resend usa `onboarding@resend.dev` como remitente. Para un dominio personalizado:

1. En dashboard de Resend → **Domains**
2. Agrega tu dominio (ej: `noreply@alcaldia.local`)
3. Sigue los pasos para verificación DNS
4. Actualiza el email en `app/utils/email_resend.py` línea ~50:
   ```python
   from_email = "noreply@tú-dominio.com"
   ```

## Funcionalidades implementadas:

### 1. Email de Bienvenida
- **Cuándo:** Cuando se crea un nuevo usuario
- **Contenido:** Bienvenida personalizada con instrucciones
- **Función:** `send_welcome_email(email, nombre_usuario)`

### 2. Código de Primer Acceso
- **Cuándo:** En el primer login después de crear la cuenta
- **Contenido:** Código de 6 dígitos para verificar identidad
- **Validez:** 15 minutos
- **Función:** `send_first_login_code_email(email, nombre_usuario, codigo, validez_minutos)`

### 3. Notificación de Cambio de Contraseña
- **Cuándo:** Cuando el usuario cambia su contraseña
- **Contenido:** Confirmación del cambio
- **Función:** `send_password_changed_email(email, nombre_usuario)`

### 4. Email de Contraseña Temporal (opcional)
- **Función:** `send_initial_password_email(email, nombre_usuario, password_temporal)`

## Flujo de autenticación actualizado:

```
Usuario intenta login
      ↓
Verifica usuario y contraseña
      ↓
¿Es primer acceso? 
      ├─ SÍ → Genera código de 6 dígitos
      │       ↓
      │    Envía email con código (Resend)
      │       ↓
      │    Redirecciona a pantalla de verificación
      │       ↓
      │    Usuario introduce código
      │       ↓
      │    ¿Código correcto?
      │       ├─ SÍ → Marca como verificado, acceso al dashboard
      │       └─ NO → Error, permite reintentar
      │
      └─ NO → Acceso directo al dashboard
```

## Prueba rápida (local)

En `.env` local, agrega:
```
RESEND_API_KEY=re_tu_api_key_test
EMAIL_PROVIDER=resend
```

Luego reinicia el servidor:
```bash
python run.py
```

Crea un nuevo usuario en la interfaz y verifica que:
1. Recibas el email de bienvenida
2. En el siguiente login se te pida el código de verificación
3. Funcione correctamente la verificación

## Problemas comunes:

### "Resend not installed"
```bash
pip install resend>=2.21.0
```

### "RESEND_API_KEY not configured"
- Verifica que agregaste la variable en Railway settings
- En local, verifica que está en `.env`

### "Email enviado pero no llega"
- Comprueba la carpeta de spam/promociones
- Verifica que `onboarding@resend.dev` esté en el whitelist
- Si usas dominio personalizado, comprueba registros DNS

### Usar SMTP en lugar de Resend
En `.env`:
```
EMAIL_PROVIDER=smtp
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=tu_app_password
```

## Pricing de Resend

- **Plan Gratuito:** 100 emails/día (perfecto para testing)
- **Pro:** $20/mes, emails ilimitados
- **Enterprise:** Contactar para presupuesto

Para más info: https://resend.com/pricing
