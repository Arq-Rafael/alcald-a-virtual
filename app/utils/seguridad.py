"""
Utilidades de Seguridad
Funciones para 2FA, verificación por correo, validación de contraseñas, etc.
"""

import re
import secrets
import string
from datetime import datetime, timedelta
from flask import current_app
from .email_api import send_email_sendgrid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class PasswordValidator:
    """Validador de fortaleza de contraseñas"""
    
    @staticmethod
    def validar_fortaleza(password):
        """
        Valida que la contraseña cumple con requisitos de seguridad
        
        Returns:
            tuple: (es_valida: bool, errores: list, puntuacion: int)
        """
        errores = []
        puntuacion = 0
        
        # Longitud mínima (reforzado)
        if len(password) < 12:
            errores.append("Debe tener al menos 12 caracteres")
        else:
            puntuacion += 1
            if len(password) >= 12:
                puntuacion += 1
        
        # Contiene mayúsculas
        if not re.search(r'[A-Z]', password):
            errores.append("Debe contener al menos una letra mayúscula")
        else:
            puntuacion += 1
        
        # Contiene minúsculas
        if not re.search(r'[a-z]', password):
            errores.append("Debe contener al menos una letra minúscula")
        else:
            puntuacion += 1
        
        # Contiene números
        if not re.search(r'\d', password):
            errores.append("Debe contener al menos un número")
        else:
            puntuacion += 1
        
        # Contiene caracteres especiales
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\];\'\\\/`~]', password):
            errores.append("Debe contener al menos un carácter especial (!@#$%^&*...)")
        else:
            puntuacion += 2
        
        # No contiene espacios
        if ' ' in password:
            errores.append("No debe contener espacios")
            puntuacion -= 1
        
        # Verificar patrones comunes débiles
        patrones_debiles = ['123456', 'password', 'admin', 'qwerty', 'abc123', '111111']
        for patron in patrones_debiles:
            if patron in password.lower():
                errores.append(f"Contiene un patrón común débil ({patron})")
                puntuacion -= 2
                break
        
        es_valida = len(errores) == 0
        puntuacion = max(0, puntuacion)  # No permitir puntuación negativa
        
        return es_valida, errores, puntuacion
    
    @staticmethod
    def generar_password_segura(longitud=16):
        """Genera una contraseña segura aleatoria"""
        caracteres = string.ascii_letters + string.digits + "!@#$%^&*-_=+"
        
        # Asegurar que tenga al menos uno de cada tipo
        password = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*-_=+")
        ]
        
        # Completar el resto
        for _ in range(longitud - 4):
            password.append(secrets.choice(caracteres))
        
        # Mezclar
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    @staticmethod
    def get_nivel_seguridad(puntuacion):
        """Obtiene el nivel de seguridad basado en puntuación"""
        if puntuacion >= 6:
            return 'Fuerte', 'success', '#16a34a'
        elif puntuacion >= 4:
            return 'Media', 'warning', '#f59e0b'
        else:
            return 'Débil', 'danger', '#ef4444'


class EmailService:
    """Servicio de envío de correos para verificación y notificaciones"""
    
    @staticmethod
    def enviar_codigo_verificacion(email, codigo, nombre_usuario='Usuario'):
        """
        Envía código de verificación por correo
        Función ROBUSTA que maneja errores gracefully
        
        Args:
            email: Correo del destinatario
            codigo: Código de 6 dígitos
            nombre_usuario: Nombre del usuario
        
        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        print(f"\n📧 Intentando enviar código a {email}...")
        
        try:
            # 1️⃣ VERIFICAR CONFIGURACIÓN
            smtp_server = current_app.config.get('SMTP_SERVER')
            smtp_port = current_app.config.get('SMTP_PORT')
            smtp_user = current_app.config.get('SMTP_USER')
            smtp_password = current_app.config.get('SMTP_PASSWORD')
            sg_api_key = current_app.config.get('SENDGRID_API_KEY')
            email_provider = current_app.config.get('EMAIL_PROVIDER', 'auto')
            
            print(f"   Server: {smtp_server}:{smtp_port}")
            print(f"   User: {smtp_user}")
            
            if not smtp_server or not smtp_port or not smtp_user or not smtp_password:
                print("   ❌ Configuración SMTP incompleta")
                return False
            
            # 2️⃣ CREAR MENSAJE
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Código de Verificación - Alcaldía Virtual'
            msg['From'] = smtp_user
            msg['To'] = email
            
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="background: white; border-radius: 12px; padding: 30px; max-width: 500px; margin: 0 auto; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                    <h2 style="text-align: center; color: #7cb342;">🔐 Código de Verificación</h2>
                    
                    <p>Hola <strong>{nombre_usuario}</strong>,</p>
                    <p>Tu código de verificación es:</p>
                    
                    <div style="background: #f0f9ff; border: 2px solid #7cb342; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                        <div style="font-size: 36px; font-weight: bold; color: #7cb342; letter-spacing: 10px;">{codigo}</div>
                    </div>
                    
                    <p><strong>⏱️ Este código expira en 10 minutos.</strong></p>
                    <p>Si no solicitaste este código, ignora este mensaje.</p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    <p style="text-align: center; color: #666; font-size: 12px;">
                        Alcaldía Municipal - Sistema de Gestión Virtual<br>
                        Este es un correo automático, por favor no responder.
                    </p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            print("   ✅ Mensaje creado")

            # 3️⃣ ENVIAR por API si está configurado o si SMTP falla
            html_body = html
            if sg_api_key and (email_provider == 'sendgrid' or email_provider == 'auto'):
                print("   ⏳ Enviando vía SendGrid API...")
                sent = send_email_sendgrid(sg_api_key, smtp_user, email, 'Código de Verificación - Alcaldía Virtual', html_body)
                if sent:
                    print("   ✅ Mensaje enviado (API)")
                    print(f"✅ ÉXITO: Código enviado a {email}\n")
                    return True
                else:
                    print("   ⚠️ Falló API, intentando SMTP...")

            print("   ⏳ Conectando a SMTP...")
            with smtplib.SMTP(smtp_server, int(smtp_port), timeout=10) as server:
                print("   ✅ Conectado")
                server.starttls()
                print("   ✅ TLS activado")
                server.login(smtp_user, smtp_password)
                print("   ✅ Autenticado")
                server.send_message(msg)
                print("   ✅ Mensaje enviado")
            
            print(f"✅ ÉXITO: Código enviado a {email}\n")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ ERROR AUTENTICACIÓN: {str(e)}")
            print(f"   Verifica usuario y contraseña SMTP")
            return False
            
        except smtplib.SMTPException as e:
            print(f"❌ ERROR SMTP: {str(e)}")
            return False
            
        except Exception as e:
            # Si hay API y estamos en auto, intentar por API como fallback final
            if sg_api_key and email_provider == 'auto':
                ok = send_email_sendgrid(sg_api_key, smtp_user, email, 'Código de Verificación - Alcaldía Virtual', html)
                if ok:
                    print("   ✅ Mensaje enviado (fallback API)")
                    print(f"✅ ÉXITO: Código enviado a {email}\n")
                    return True
            print(f"❌ ERROR: {type(e).__name__}: {str(e)}")
            return False
    
    @staticmethod
    def enviar_notificacion_registro(email, nombre_usuario):
        """Notifica creación de cuenta al usuario con logging detallado"""
        print(f"\n📧 Intentando enviar notificación de registro a {email}...")
        
        try:
            smtp_server = current_app.config.get('SMTP_SERVER')
            smtp_port = current_app.config.get('SMTP_PORT')
            smtp_user = current_app.config.get('SMTP_USER')
            smtp_password = current_app.config.get('SMTP_PASSWORD')
            sg_api_key = current_app.config.get('SENDGRID_API_KEY')
            email_provider = current_app.config.get('EMAIL_PROVIDER', 'auto')

            print(f"   Server: {smtp_server}:{smtp_port}")
            print(f"   User: {smtp_user}")

            if not smtp_user or not smtp_password:
                print("   ❌ Configuración SMTP incompleta")
                return False

            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Bienvenido - Tu cuenta ha sido creada'
            msg['From'] = smtp_user
            msg['To'] = email

            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
              <div style="background: white; border-radius: 12px; padding: 30px; max-width: 520px; margin: 0 auto;">
                <h2 style="color:#6366f1;">¡Bienvenido/a, {nombre_usuario}!</h2>
                <p>Tu cuenta en Alcaldía Virtual ha sido creada correctamente.</p>
                <p>Ya puedes iniciar sesión con tus credenciales. Si no reconoces esta acción, contacta al administrador.</p>
                <p style="color:#555; font-size:12px;">Este es un correo automático, no responder.</p>
              </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(html, 'html'))
            print("   ✅ Mensaje creado")

            if sg_api_key and (email_provider == 'sendgrid' or email_provider == 'auto'):
                print("   ⏳ Enviando vía SendGrid API...")
                if send_email_sendgrid(sg_api_key, smtp_user, email, 'Bienvenido - Tu cuenta ha sido creada', html):
                    print("   ✅ Mensaje enviado (API)")
                    print(f"✅ ÉXITO: Notificación enviada a {email}\n")
                    return True
                else:
                    print("   ⚠️ Falló API, intentando SMTP...")

            print("   ⏳ Conectando...")
            with smtplib.SMTP(smtp_server, int(smtp_port), timeout=10) as server:
                print("   ✅ Conectado")
                server.starttls()
                print("   ✅ TLS activado")
                server.login(smtp_user, smtp_password)
                print("   ✅ Autenticado")
                server.send_message(msg)
                print("   ✅ Mensaje enviado")

            print(f"✅ ÉXITO: Notificación enviada a {email}\n")
            return True
            
        except Exception as e:
            # Fallback API
            if sg_api_key and email_provider == 'auto':
                if send_email_sendgrid(sg_api_key, smtp_user, email, 'Bienvenido - Tu cuenta ha sido creada', html):
                    print("   ✅ Mensaje enviado (fallback API)")
                    print(f"✅ ÉXITO: Notificación enviada a {email}\n")
                    return True
            print(f"❌ ERROR: {type(e).__name__}: {str(e)}\n")
            return False

    @staticmethod
    def enviar_alerta_nuevo_usuario(email_admin, nombre_usuario, creador):
        """Alerta al admin que se creó un usuario"""
        try:
            import socket
            smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = current_app.config.get('SMTP_PORT', 587)
            smtp_user = current_app.config.get('SMTP_USER', '')
            smtp_password = current_app.config.get('SMTP_PASSWORD', '')

            if not smtp_user or not smtp_password or not email_admin:
                return False

            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Nuevo usuario creado'
            msg['From'] = smtp_user
            msg['To'] = email_admin

            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
              <div style="background: white; border-radius: 12px; padding: 30px; max-width: 520px; margin: 0 auto;">
                <h3 style="color:#ea580c;">Nuevo usuario creado</h3>
                <p>Usuario: <strong>{nombre_usuario}</strong></p>
                <p>Creado por: <strong>{creador or 'admin'}</strong></p>
                <p>Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
              </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(html, 'html'))

            original_timeout = socket.getdefaulttimeout()
            try:
                socket.setdefaulttimeout(5)
                with smtplib.SMTP(smtp_server, smtp_port, timeout=5) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
            finally:
                socket.setdefaulttimeout(original_timeout)

            return True
        except (socket.timeout, Exception):
            return False

    @staticmethod
    def enviar_alerta_bloqueo(email, nombre_usuario, ip_address=None):
        """Notifica que la cuenta fue bloqueada por intentos fallidos"""
        try:
            import socket
            smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = current_app.config.get('SMTP_PORT', 587)
            smtp_user = current_app.config.get('SMTP_USER', '')
            smtp_password = current_app.config.get('SMTP_PASSWORD', '')

            if not smtp_user or not smtp_password or not email:
                return False

            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Cuenta bloqueada por seguridad'
            msg['From'] = smtp_user
            msg['To'] = email

            ip_info = f"<p><strong>IP:</strong> {ip_address}</p>" if ip_address else ""

            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background:#f5f5f5; padding:20px;">
              <div style="background:white; border-radius:12px; padding:30px; max-width:520px; margin:0 auto;">
                <h3 style="color:#dc2626;">Tu cuenta fue bloqueada</h3>
                <p>Hola <strong>{nombre_usuario}</strong>, detectamos múltiples intentos fallidos y tu cuenta fue bloqueada por 30 minutos.</p>
                {ip_info}
                <p>Si fuiste tú, espera el desbloqueo automático. Si no reconoces la actividad, contacta al administrador.</p>
              </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(html, 'html'))

            original_timeout = socket.getdefaulttimeout()
            try:
                socket.setdefaulttimeout(5)
                with smtplib.SMTP(smtp_server, smtp_port, timeout=5) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
            finally:
                socket.setdefaulttimeout(original_timeout)

            return True
        except (socket.timeout, Exception):
            return False

    @staticmethod
    def enviar_notificacion_cambio_clave(email, nombre_usuario, ip_address=None):
        """Notifica cambio de contraseña"""
        try:
            import socket
            smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = current_app.config.get('SMTP_PORT', 587)
            smtp_user = current_app.config.get('SMTP_USER', '')
            smtp_password = current_app.config.get('SMTP_PASSWORD', '')
            
            if not smtp_user or not smtp_password:
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = '⚠ Cambio de Contraseña Detectado'
            msg['From'] = smtp_user
            msg['To'] = email
            
            ip_info = f"<p><strong>Dirección IP:</strong> {ip_address}</p>" if ip_address else ""
            
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="background: white; border-radius: 12px; padding: 30px; max-width: 500px; margin: 0 auto;">
                    <h2 style="color: #f59e0b;">⚠ Cambio de Contraseña</h2>
                    <p>Hola <strong>{nombre_usuario}</strong>,</p>
                    <p>Se ha cambiado la contraseña de tu cuenta.</p>
                    {ip_info}
                    <p><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                    <p>Si no realizaste este cambio, contacta inmediatamente al administrador del sistema.</p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            original_timeout = socket.getdefaulttimeout()
            try:
                socket.setdefaulttimeout(5)
                with smtplib.SMTP(smtp_server, smtp_port, timeout=5) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
            finally:
                socket.setdefaulttimeout(original_timeout)
            
            return True
        except (socket.timeout, Exception):
            return False


    @staticmethod
    def enviar_enlace_recuperacion(email, nombre_usuario, token):
        """Envía enlace para recuperar contraseña"""
        try:
            import socket
            smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(current_app.config.get('SMTP_PORT', 587))
            smtp_user = current_app.config.get('SMTP_USER', '')
            smtp_password = current_app.config.get('SMTP_PASSWORD', '')
            
            if not smtp_user or not smtp_password:
                print("⚠️  SMTP_USER o SMTP_PASSWORD no configurados")
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = '🔑 Recuperar Contraseña - Alcaldía Virtual'
            msg['From'] = smtp_user
            msg['To'] = email
            
            # Generar link (Aquí deberías usar request.host)
            link_recuperacion = f"http://localhost:5000/auth/recuperacion/{token}"
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px; }}
                    .container {{ background: white; border-radius: 12px; padding: 30px; max-width: 500px; margin: 0 auto; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
                    .header {{ text-align: center; color: #d32f2f; margin-bottom: 20px; }}
                    .button {{ background: #7cb342; color: white; padding: 12px 30px; text-align: center; border-radius: 6px; text-decoration: none; display: inline-block; margin: 20px 0; }}
                    .warning {{ background: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; padding: 15px; margin: 20px 0; color: #856404; }}
                    .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>🔑 Recuperar Contraseña</h2>
                    </div>
                    <p>Hola <strong>{nombre_usuario}</strong>,</p>
                    <p>Recibimos una solicitud para recuperar tu contraseña. Haz clic en el botón de abajo para establecer una nueva contraseña:</p>
                    
                    <center>
                        <a href="{link_recuperacion}" class="button">Recuperar Contraseña</a>
                    </center>
                    
                    <p>O copia y pega este enlace en tu navegador:</p>
                    <p style="background: #f0f0f0; padding: 10px; word-break: break-all; font-size: 12px;">{link_recuperacion}</p>
                    
                    <div class="warning">
                        <strong>⚠️ IMPORTANTE:</strong> Este enlace expira en 1 hora. Si no lo usas en ese tiempo, deberás solicitar otro.
                    </div>
                    
                    <p>Si <strong>no</strong> solicitaste recuperar tu contraseña, puedes ignorar este correo de forma segura.</p>
                    
                    <div class="footer">
                        <p>Alcaldía Municipal - Sistema de Gestión Virtual</p>
                        <p>Este es un correo automático, por favor no responder.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            original_timeout = socket.getdefaulttimeout()
            try:
                socket.setdefaulttimeout(5)
                with smtplib.SMTP(smtp_server, smtp_port, timeout=5) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
            finally:
                socket.setdefaulttimeout(original_timeout)
            
            return True
        except (socket.timeout, Exception) as e:
            print(f"❌ Error al enviar enlace de recuperación: {e}")
            return False
    
    @staticmethod
    def enviar_alerta_expiracion_clave(email, nombre_usuario, dias_restantes):
        """Notifica al usuario que su contraseña está por expirar"""
        try:
            import socket
            smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(current_app.config.get('SMTP_PORT', 587))
            smtp_user = current_app.config.get('SMTP_USER', '')
            smtp_password = current_app.config.get('SMTP_PASSWORD', '')
            
            if not smtp_user or not smtp_password:
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'⏰ Tu contraseña expira en {dias_restantes} días'
            msg['From'] = smtp_user
            msg['To'] = email
            
            urgencia = "rojo" if dias_restantes <= 7 else "naranja"
            color = "#d32f2f" if dias_restantes <= 7 else "#ff9800"
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px; }}
                    .container {{ background: white; border-radius: 12px; padding: 30px; max-width: 500px; margin: 0 auto; }}
                    .alert {{ background: {color}; color: white; padding: 15px; border-radius: 6px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>⏰ Alerta de Expiración de Contraseña</h2>
                    <p>Hola <strong>{nombre_usuario}</strong>,</p>
                    
                    <div class="alert">
                        <strong>Tu contraseña expirará en {dias_restantes} días.</strong>
                    </div>
                    
                    <p>Por razones de seguridad, debes cambiar tu contraseña regularmente.</p>
                    <p>Puedes cambiarla iniciando sesión y yendo a: <strong>Configuración → Cambiar Contraseña</strong></p>
                    
                    <p>Alcaldía Municipal - Sistema de Gestión Virtual</p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            original_timeout = socket.getdefaulttimeout()
            try:
                socket.setdefaulttimeout(5)
                with smtplib.SMTP(smtp_server, smtp_port, timeout=5) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
            finally:
                socket.setdefaulttimeout(original_timeout)
            
            return True
        except (socket.timeout, Exception):
            return False


def generar_token_seguro(longitud=32):
    """Genera un token seguro para sesiones"""
    return secrets.token_urlsafe(longitud)


def validar_email(email):
    """Valida formato de email"""
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None


def sanitizar_entrada(texto):
    """Sanitiza entrada de usuario para prevenir inyecciones"""
    if not texto:
        return ''
    
    # Eliminar caracteres peligrosos
    texto = re.sub(r'[<>\"\'%;()&+]', '', str(texto))
    
    # Limitar longitud
    return texto[:500].strip()
