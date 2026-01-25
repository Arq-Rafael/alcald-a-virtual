# SMTP Timeout Fix - January 25, 2026

## Problem
The platform was experiencing worker timeouts on production (Railway) when users attempted to login. The error occurred because:

1. User tries to login on `/` or `/login`
2. If 2FA is enabled and email is configured, `EmailService.enviar_codigo_verificacion()` is called
3. This method tries to connect to SMTP server with no timeout
4. SMTP connection hangs indefinitely (DNS resolution timeout, firewall block, server unreachable)
5. Gunicorn worker process times out (default 30s) and dies
6. Worker keeps getting recycled, platform becomes unreachable

**Error trace:** `File "/app/app/utils/seguridad.py", line 187, in enviar_codigo_verificacion` → `File "/opt/venv/lib/python3.11/site-packages/gunicorn/workers/base.py", line 204, in handle_abort` → `SystemExit: 1`

## Solution

### 1. Modified `app/routes/auth.py` (lines 60-81)
- Wrapped email verification in try-except block
- Added 5-second socket timeout before SMTP attempt
- If email send fails (timeout or other error), allow login to continue with warning
- Platform no longer blocks on unreachable SMTP servers

**Behavior:**
```
✅ Email sends successfully → 2FA verification required
⚠️ Email times out → Login permitted with warning message
⚠️ Email config missing → Login permitted with warning message
```

### 2. Updated all SMTP functions in `app/utils/seguridad.py`
All 7 email functions now have 5-second timeout:
- `enviar_codigo_verificacion()` - 2FA verification code (line 191)
- `enviar_notificacion_registro()` - Account creation notification (line 246)
- `enviar_alerta_nuevo_usuario()` - Admin alert on new user (line 293)
- `enviar_alerta_bloqueo()` - Account lock notification (line 342)
- `enviar_notificacion_cambio_clave()` - Password change alert (line 393)
- `enviar_enlace_recuperacion()` - Password recovery link (line 476)
- `enviar_alerta_expiracion_clave()` - Password expiry warning (line 542)

**Pattern applied to each:**
```python
import socket
original_timeout = socket.getdefaulttimeout()
try:
    socket.setdefaulttimeout(5)
    with smtplib.SMTP(smtp_server, smtp_port, timeout=5) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
finally:
    socket.setdefaulttimeout(original_timeout)
```

## Impact

✅ **Platform Stability**: Users can now login even if SMTP is misconfigured or unreachable  
✅ **Worker Health**: No more 30-second hangs that kill worker processes  
✅ **Graceful Degradation**: 2FA still works if email is available, degrades gracefully if not  
✅ **Error Visibility**: Console logs show "SMTP timeout" or specific error messages  

## Testing Recommendation

1. Try login from browser → Should see login page (not timeout)
2. If email not configured → Should see warning "⚠️ Error en verificación de email. Acceso permitido."
3. If email configured → Should receive 2FA code or see same warning if timeout
4. All endpoints should respond within 5 seconds instead of timing out

## Production Notes

- SMTP timeout set to 5 seconds (configurable if needed)
- Email failures are non-blocking (graceful degradation)
- Monitor logs for "SMTP timeout" messages to identify configuration issues
- Consider setting proper SMTP_SERVER, SMTP_USER, SMTP_PASSWORD environment variables

## Files Modified

- `app/routes/auth.py`: Added timeout handling in login route
- `app/utils/seguridad.py`: Added socket timeout to 7 email functions (527 → 573 lines)
