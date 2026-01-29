"""
Email service using Resend API (https://resend.com/)
Alternative to SMTP for sending emails via HTTPS in restricted environments like Railway
"""

import logging
from flask import current_app

try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False

logger = logging.getLogger(__name__)


def send_email_resend(to_email, subject, html_content, from_name="Alcaldía Virtual"):
    """
    Envía email usando Resend API
    
    Args:
        to_email: Email del destinatario
        subject: Asunto del email
        html_content: Contenido HTML del email
        from_name: Nombre del remitente (default: Alcaldía Virtual)
    
    Returns:
        dict: {"success": bool, "message": str, "id": str or None}
    """
    
    if not RESEND_AVAILABLE:
        logger.error("Resend not installed. Install with: pip install resend")
        return {"success": False, "message": "Resend not installed"}
    
    api_key = current_app.config.get('RESEND_API_KEY', '')
    
    if not api_key:
        logger.error("RESEND_API_KEY not configured")
        return {"success": False, "message": "RESEND_API_KEY not configured"}
    
    try:
        resend.api_key = api_key
        
        # From email debe ser un dominio autorizado en Resend
        # Por defecto usa onboarding@resend.dev para testing
        from_email = "onboarding@resend.dev"  # Change this after verifying your domain
        
        email_data = {
            "from": f"{from_name} <{from_email}>",
            "to": to_email,
            "subject": subject,
            "html": html_content,
        }
        
        logger.info(f"Enviando email via Resend a {to_email}")
        response = resend.Emails.send(email_data)
        
        if response and "id" in response:
            logger.info(f"Email enviado exitosamente. ID: {response['id']}")
            return {
                "success": True,
                "message": f"Email sent successfully (ID: {response['id']})",
                "id": response["id"]
            }
        else:
            logger.error(f"Resend API error: {response}")
            return {
                "success": False,
                "message": f"Resend API error: {response}"
            }
    
    except Exception as e:
        logger.error(f"Error enviando email con Resend: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


def send_welcome_email(email, nombre_usuario):
    """Envía email de bienvenida al crear usuario"""
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
      <div style="background: white; border-radius: 12px; padding: 30px; max-width: 520px; margin: 0 auto; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <div style="text-align: center; margin-bottom: 20px;">
          <h1 style="color: #1f2937; margin: 0;">🏛️ Alcaldía Virtual</h1>
        </div>
        
        <h2 style="color: #6366f1; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">¡Bienvenido/a, {nombre_usuario}!</h2>
        
        <p style="color: #374151; font-size: 15px; line-height: 1.6;">
          Tu cuenta en Alcaldía Virtual ha sido creada correctamente.
        </p>
        
        <div style="background: #f3f4f6; border-left: 4px solid #6366f1; padding: 15px; margin: 20px 0; border-radius: 4px;">
          <p style="margin: 0; color: #1f2937; font-weight: 500;">Ya puedes acceder con tus credenciales.</p>
          <p style="margin: 8px 0 0 0; color: #4b5563; font-size: 13px;">Si no reconoces esta acción, contacta al administrador inmediatamente.</p>
        </div>
        
        <p style="color: #9ca3af; font-size: 12px; text-align: center; margin-top: 30px; border-top: 1px solid #e5e7eb; padding-top: 15px;">
          Este es un correo automático, no responder. Sistemas de Información - Alcaldía Municipal
        </p>
      </div>
    </body>
    </html>
    """
    
    return send_email_resend(
        to_email=email,
        subject="Bienvenido - Tu cuenta ha sido creada",
        html_content=html
    )


def send_initial_password_email(email, nombre_usuario, password_temporal):
    """Envía email con contraseña temporal para primer acceso"""
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
      <div style="background: white; border-radius: 12px; padding: 30px; max-width: 520px; margin: 0 auto; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <div style="text-align: center; margin-bottom: 20px;">
          <h1 style="color: #1f2937; margin: 0;">🏛️ Alcaldía Virtual</h1>
        </div>
        
        <h2 style="color: #6366f1; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">Tu contraseña temporal</h2>
        
        <p style="color: #374151; font-size: 15px; line-height: 1.6;">
          Hola <strong>{nombre_usuario}</strong>,
        </p>
        
        <p style="color: #374151; font-size: 15px; line-height: 1.6;">
          Tu cuenta ha sido creada en Alcaldía Virtual. Aquí está tu información de acceso:
        </p>
        
        <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 4px;">
          <p style="margin: 0; color: #92400e; font-weight: 500;">⚠️ Información de Acceso</p>
          <p style="margin: 8px 0 0 0; color: #d97706; font-size: 13px;">
            <strong>Usuario:</strong> {email}<br>
            <strong>Contraseña temporal:</strong> {password_temporal}
          </p>
        </div>
        
        <div style="background: #dbeafe; border-left: 4px solid #3b82f6; padding: 15px; margin: 20px 0; border-radius: 4px;">
          <p style="margin: 0; color: #1e40af; font-weight: 500;">✅ Próximos pasos</p>
          <ol style="margin: 8px 0 0 0; color: #1e40af; font-size: 13px; padding-left: 20px;">
            <li>Inicia sesión con tu usuario y contraseña temporal</li>
            <li>Se te solicitará que establezca una nueva contraseña en el primer acceso</li>
            <li>Sigue las instrucciones de seguridad en pantalla</li>
          </ol>
        </div>
        
        <p style="color: #9ca3af; font-size: 12px; text-align: center; margin-top: 30px; border-top: 1px solid #e5e7eb; padding-top: 15px;">
          Este es un correo automático, no responder. Sistemas de Información - Alcaldía Municipal
        </p>
      </div>
    </body>
    </html>
    """
    
    return send_email_resend(
        to_email=email,
        subject="Tu información de acceso a Alcaldía Virtual",
        html_content=html
    )


def send_first_login_code_email(email, nombre_usuario, codigo_temporal, validez_minutos=15):
    """Envía email con código de verificación para primer acceso"""
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
      <div style="background: white; border-radius: 12px; padding: 30px; max-width: 520px; margin: 0 auto; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <div style="text-align: center; margin-bottom: 20px;">
          <h1 style="color: #1f2937; margin: 0;">🏛️ Alcaldía Virtual</h1>
        </div>
        
        <h2 style="color: #6366f1; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">Código de Verificación</h2>
        
        <p style="color: #374151; font-size: 15px; line-height: 1.6;">
          Hola <strong>{nombre_usuario}</strong>,
        </p>
        
        <p style="color: #374151; font-size: 15px; line-height: 1.6;">
          Se ha detectado un primer acceso a tu cuenta. Usa el código de verificación a continuación para completar el proceso de seguridad:
        </p>
        
        <div style="background: #f0fdf4; border: 2px solid #22c55e; padding: 20px; margin: 20px 0; border-radius: 8px; text-align: center;">
          <p style="margin: 0; color: #15803d; font-size: 12px; text-transform: uppercase; letter-spacing: 2px;">Código de Verificación</p>
          <p style="margin: 12px 0 0 0; color: #16a34a; font-size: 36px; font-weight: bold; font-family: 'Courier New', monospace; letter-spacing: 4px;">
            {codigo_temporal}
          </p>
        </div>
        
        <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 4px;">
          <p style="margin: 0; color: #92400e; font-weight: 500;">⏱️ Código válido por {validez_minutos} minutos</p>
          <p style="margin: 8px 0 0 0; color: #d97706; font-size: 13px;">
            No compartas este código. Los administradores nunca lo solicitarán.
          </p>
        </div>
        
        <p style="color: #374151; font-size: 13px; line-height: 1.6; margin: 20px 0;">
          Si no iniciaste sesión, ignora este correo. Tu cuenta permanecerá segura.
        </p>
        
        <p style="color: #9ca3af; font-size: 12px; text-align: center; margin-top: 30px; border-top: 1px solid #e5e7eb; padding-top: 15px;">
          Este es un correo automático, no responder. Sistemas de Información - Alcaldía Municipal
        </p>
      </div>
    </body>
    </html>
    """
    
    return send_email_resend(
        to_email=email,
        subject=f"Código de verificación - Alcaldía Virtual ({codigo_temporal})",
        html_content=html
    )


def send_password_changed_email(email, nombre_usuario):
    """Envía email notificando cambio de contraseña"""
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
      <div style="background: white; border-radius: 12px; padding: 30px; max-width: 520px; margin: 0 auto; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <div style="text-align: center; margin-bottom: 20px;">
          <h1 style="color: #1f2937; margin: 0;">🏛️ Alcaldía Virtual</h1>
        </div>
        
        <h2 style="color: #6366f1; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">Contraseña Modificada</h2>
        
        <p style="color: #374151; font-size: 15px; line-height: 1.6;">
          Hola <strong>{nombre_usuario}</strong>,
        </p>
        
        <div style="background: #d1fae5; border-left: 4px solid #10b981; padding: 15px; margin: 20px 0; border-radius: 4px;">
          <p style="margin: 0; color: #065f46; font-weight: 500;">✅ Tu contraseña ha sido cambiada exitosamente</p>
          <p style="margin: 8px 0 0 0; color: #047857; font-size: 13px;">
            Si no realizaste este cambio, contacta al administrador inmediatamente.
          </p>
        </div>
        
        <p style="color: #374151; font-size: 13px; line-height: 1.6; margin: 20px 0;">
          Por tu seguridad, ahora puedes iniciar sesión con tu nueva contraseña.
        </p>
        
        <p style="color: #9ca3af; font-size: 12px; text-align: center; margin-top: 30px; border-top: 1px solid #e5e7eb; padding-top: 15px;">
          Este es un correo automático, no responder. Sistemas de Información - Alcaldía Municipal
        </p>
      </div>
    </body>
    </html>
    """
    
    return send_email_resend(
        to_email=email,
        subject="Tu contraseña ha sido modificada",
        html_content=html
    )
