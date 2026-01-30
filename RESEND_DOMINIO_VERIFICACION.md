# ⚠️ Resend - Verificación de Dominio Requerida

## Problema Actual

Resend en modo **testing/gratuito** solo permite enviar emails a la dirección del propietario de la cuenta:
- ✅ Puede enviar a: `alcaldiavirtual2026@gmail.com`
- ❌ No puede enviar a: otros emails (ej: `planeacion@supata-cundinamarca.gov.co`)

**Error que aparece:**
```
You can only send testing emails to your own email address (alcaldiavirtual2026@gmail.com). 
To send emails to other recipients, please verify a domain at resend.com/domains
```

## Solución: Verificar un Dominio

Para enviar emails a **cualquier destinatario**, debes verificar un dominio propio en Resend.

### Opción 1: Usar dominio de la alcaldía (Recomendado)

Si tienen acceso al dominio `supata-cundinamarca.gov.co`:

1. **Ve a Resend Dashboard**: https://resend.com/domains
2. **Haz clic en "Add Domain"**
3. **Ingresa tu dominio**: `supata-cundinamarca.gov.co`
4. **Resend te dará registros DNS para agregar:**
   ```
   Tipo: TXT
   Nombre: _resend
   Valor: [código proporcionado por Resend]
   
   Tipo: MX
   Nombre: @
   Valor: feedback-smtp.us-east-1.amazonses.com
   Prioridad: 10
   ```

5. **Agrega estos registros en tu proveedor de DNS** (donde está alojado el dominio)
6. **Espera 5-10 minutos** y verifica en Resend
7. **Actualiza el código** en `app/utils/email_resend.py`:
   ```python
   from_email = "noreply@supata-cundinamarca.gov.co"  # Usa tu dominio verificado
   ```

### Opción 2: Usar un subdominio

Si no puedes modificar el DNS principal, puedes usar un subdominio:

1. Crea un subdominio: `mail.supata-cundinamarca.gov.co`
2. Verifica ese subdominio en Resend
3. Usa ese subdominio para enviar emails

### Opción 3: Usar dominio gratuito (temporal)

Para testing rápido, puedes usar servicios como:
- **Vercel Domains** (si usas Vercel)
- **Cloudflare** (gratuito con registro de dominio)

### Opción 4: Solo usar para testing local

Por ahora, solo crear usuarios con email `alcaldiavirtual2026@gmail.com` para pruebas.

## Cambios en el Código

Una vez verificado el dominio, actualiza:

**Archivo**: `app/utils/email_resend.py`

```python
# Cambiar esta línea:
from_email = "onboarding@resend.dev"  # ❌ Modo testing

# Por tu dominio verificado:
from_email = "noreply@supata-cundinamarca.gov.co"  # ✅ Dominio verificado
```

También elimina esta validación (líneas 38-47):
```python
# Remover esta restricción de testing
if to_email != allowed_testing_email:
    logger.warning(f"⚠️ Resend en modo testing...")
    return {"success": False, ...}
```

## Estado Actual del Sistema

Mientras no se verifique un dominio:
- ✅ Usuarios pueden crearse normalmente
- ✅ Sistema funciona sin emails
- ⚠️ Emails solo se envían a `alcaldiavirtual2026@gmail.com`
- ⚠️ Otros usuarios no recibirán códigos de verificación
- ℹ️ El sistema muestra advertencias pero no falla

## Verificación Exitosa

Sabrás que funcionó cuando:
1. En Resend Dashboard aparece ✅ **Verified** junto a tu dominio
2. Los emails se envían sin error a cualquier destinatario
3. Los logs muestran `Email enviado exitosamente` sin advertencias

## Ayuda Adicional

- **Documentación Resend**: https://resend.com/docs/dashboard/domains/introduction
- **Soporte Resend**: https://resend.com/support
- **Verificar DNS**: https://mxtoolbox.com/ (para comprobar registros)

---

**Nota**: Una vez verificado el dominio, haz un commit y push para que Railway use el nuevo `from_email`.
