"""
Rutas para Recuperación de Contraseña
Permite a usuarios sin acceso recuperar su contraseña vía email
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask import current_app
from app import db
from app.models.usuario import Usuario, RecuperacionClave, AuditoriaAcceso
from app.utils.seguridad import EmailService, generar_token_seguro
from datetime import datetime, timedelta
import secrets

recuperacion_bp = Blueprint('recuperacion', __name__, url_prefix='/auth/recuperacion')

@recuperacion_bp.route('/solicitar', methods=['GET', 'POST'])
def solicitar_recuperacion():
    """Formulario para solicitar recuperación de contraseña"""
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        # Validar que el email no esté vacío
        if not email:
            flash('Por favor ingresa tu correo electrónico', 'warning')
            return render_template('recuperacion_solicitar.html')
        
        # Buscar usuario por email
        user = Usuario.query.filter_by(email=email).first()
        
        if not user:
            # Por seguridad, NO decimos que el usuario no existe
            flash('Si el correo está registrado, recibirás un enlace de recuperación en breve.', 'info')
            return redirect(url_for('auth.login'))
        
        # Generar token único
        token = secrets.token_urlsafe(32)
        
        # Crear registro de recuperación
        recuperacion = RecuperacionClave(
            usuario_id=user.id,
            token=token,
            email=email,
            expira_en=datetime.utcnow() + timedelta(hours=1)
        )
        
        db.session.add(recuperacion)
        db.session.commit()
        
        # Enviar correo
        EmailService.enviar_enlace_recuperacion(email, user.usuario, token)
        
        # Auditoría
        auditoria = AuditoriaAcceso(
            usuario_id=user.id,
            usuario_nombre=user.usuario,
            accion='solicitar_recuperacion_clave',
            ip_address=request.remote_addr,
            exitoso=True,
            detalles=f'Solicitud desde: {request.remote_addr}'
        )
        db.session.add(auditoria)
        db.session.commit()
        
        flash('Si el correo está registrado, recibirás un enlace de recuperación en breve.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('recuperacion_solicitar.html')


@recuperacion_bp.route('/<token>', methods=['GET', 'POST'])
def recuperar_clave(token):
    """Procesar recuperación de contraseña con token"""
    
    # Validar token
    recuperacion = RecuperacionClave.query.filter_by(token=token).first()
    
    if not recuperacion or not recuperacion.es_valido():
        flash('Enlace inválido o expirado. Solicita un nuevo enlace de recuperación.', 'danger')
        return redirect(url_for('recuperacion.solicitar_recuperacion'))
    
    user = Usuario.query.get(recuperacion.usuario_id)
    if not user:
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        nueva_clave = request.form.get('clave', '').strip()
        confirmar_clave = request.form.get('confirmar_clave', '').strip()
        
        # Validaciones
        if not nueva_clave or not confirmar_clave:
            flash('Por favor llena todos los campos', 'warning')
            return render_template('recuperacion_nueva_clave.html', token=token)
        
        if nueva_clave != confirmar_clave:
            flash('Las contraseñas no coinciden', 'warning')
            return render_template('recuperacion_nueva_clave.html', token=token)
        
        if len(nueva_clave) < 12:
            flash('La contraseña debe tener al menos 12 caracteres', 'warning')
            return render_template('recuperacion_nueva_clave.html', token=token)
        
        try:
            # Validar que no sea igual a anterior
            user.validar_nueva_clave(nueva_clave)
            
            # Cambiar contraseña
            user.set_password(nueva_clave)
            
            # Marcar recuperación como usada
            recuperacion.usado = True
            recuperacion.usado_en = datetime.utcnow()
            
            # Registrar auditoría
            auditoria = AuditoriaAcceso(
                usuario_id=user.id,
                usuario_nombre=user.usuario,
                accion='recuperacion_clave_exitosa',
                ip_address=request.remote_addr,
                exitoso=True,
                detalles=f'Recuperación completada desde: {request.remote_addr}'
            )
            
            db.session.add(auditoria)
            db.session.commit()
            
            # Notificar por email
            EmailService.enviar_notificacion_cambio_clave(
                user.email, 
                user.usuario, 
                request.remote_addr
            )
            
            flash('✅ Contraseña actualizada exitosamente. Por favor inicia sesión con tu nueva contraseña.', 'success')
            return redirect(url_for('auth.login'))
            
        except ValueError as e:
            flash(f'⚠️ {str(e)}', 'warning')
            return render_template('recuperacion_nueva_clave.html', token=token)
    
    return render_template('recuperacion_nueva_clave.html', token=token)
