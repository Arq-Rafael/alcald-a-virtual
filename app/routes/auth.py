from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask import current_app
from app import db
from app.models.usuario import Usuario, AuditoriaAcceso, Sesion
from app.utils.seguridad import EmailService
from datetime import datetime, timedelta
import secrets
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, go to dashboard
    if session.get('user'):
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        u = request.form.get('usuario','').strip()
        p = request.form.get('clave','').strip()

        # Buscar usuario en base de datos
        user = Usuario.query.filter(Usuario.usuario == u).first()

        if not user:
            flash('Usuario o clave inválidos', 'danger')
            return render_template('login.html')

        # Restricción por IP (whitelist opcional)
        allowed_ips = current_app.config.get('ALLOWED_IPS', [])
        if allowed_ips and request.remote_addr not in allowed_ips:
            flash('Acceso no permitido desde esta red. Contacta al administrador.', 'danger')
            return render_template('login.html')

        # Verificar si puede acceder (bloqueo temporal, activo, etc.)
        puede, motivo = user.puede_acceder()
        if not puede:
            flash(motivo, 'danger')
            return render_template('login.html')

        # Verificar contraseña
        if not user.check_password(p):
            user.registrar_acceso_fallido()
            db.session.commit()

            # Si quedó bloqueado, notificar
            if user.bloqueado:
                EmailService.enviar_alerta_bloqueo(user.email, user.usuario, request.remote_addr)

            flash('Usuario o clave inválidos', 'danger')
            return render_template('login.html')

        # Verificar si la contraseña ha expirado (más de 90 días)
        if user.clave_expirada() or user.requiere_cambio_clave:
            flash('⚠️ Tu contraseña ha expirado. Debes cambiarla para continuar.', 'warning')
            session['pending_user_id'] = user.id
            return redirect(url_for('auth.cambiar_clave_forzado'))

        # Contraseña correcta ✅
        
        # === VERIFICAR PRIMER ACCESO (si existe la columna) ===
        try:
            if user.primer_acceso and user.email:
                # Generar código de verificación
                codigo = user.generar_codigo_primer_acceso()
                db.session.commit()
                
                # Enviar código por email
                from app.utils.email_resend import send_first_login_code_email
                resultado = send_first_login_code_email(user.email, user.usuario, codigo)
                
                # Guardar user_id en sesión temporal para verificación
                session['pending_first_login_user_id'] = user.id
                
                flash(f'Se ha enviado un código de verificación a {user.email}. Por favor verifica tu identidad para continuar.', 'info')
                return redirect(url_for('auth.verificar_primer_acceso'))
        except (AttributeError, Exception) as e:
            # Columna primer_acceso no existe aún o no se puede usar
            # Continuar con login normal
            pass
        
        # === CREAR SESIÓN Y ACCESO ===
        user.registrar_acceso_exitoso()
        token = user.generar_token_sesion()
        
        # Detectar dispositivo
        user_agent = request.headers.get('User-Agent', '')
        if 'Mobile' in user_agent or 'Android' in user_agent:
            dispositivo = 'mobile'
        elif 'Tablet' in user_agent or 'iPad' in user_agent:
            dispositivo = 'tablet'
        else:
            dispositivo = 'desktop'
        
        # Crear registro de sesión
        sesion = Sesion(
            usuario_id=user.id,
            usuario_nombre=user.usuario,
            token=secrets.token_urlsafe(32),
            ip_address=request.remote_addr,
            user_agent=user_agent,
            dispositivo=dispositivo
        )
        
        db.session.add(sesion)
        db.session.commit()

        # Persistir datos en sesión
        session['user'] = user.usuario
        session['role'] = user.role.lower() if user.role else 'user'
        session['user_role'] = session['role']
        session['secretaria'] = user.secretaria or ''
        session['token'] = token
        session['sesion_id'] = sesion.id

        return redirect(url_for('main.dashboard'))

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Cerrar sesión del usuario"""
    username = session.get('user')
    sesion_id = session.get('sesion_id')
    
    # Cerrar sesión en BD
    if sesion_id:
        sesion = Sesion.query.get(sesion_id)
        if sesion:
            sesion.cerrar_sesion()
            db.session.commit()
    
    # Registrar logout en auditoría
    if username:
        auditoria = AuditoriaAcceso(
            usuario_nombre=username,
            accion='logout',
            ip_address=request.remote_addr,
            exitoso=True
        )
        db.session.add(auditoria)
        db.session.commit()
    
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/verificacion', methods=['GET', 'POST'])
def verificacion():
    """Verificación de código 2FA"""
    pending_id = session.get('pending_user_id')
    if not pending_id:
        return redirect(url_for('auth.login'))

    user = Usuario.query.get(pending_id)
    if not user:
        session.pop('pending_user_id', None)
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip()
        if not codigo:
            flash('Ingresa el código de verificación', 'warning')
            return render_template('verify_2fa.html', usuario=user.usuario)

        if not user.verificar_codigo(codigo):
            flash('Código inválido o expirado', 'danger')
            return render_template('verify_2fa.html', usuario=user.usuario)

        # Verificación exitosa
        user.email_verificado = True
        user.email_ultimo_verificado = datetime.utcnow()  # Guardar cuándo fue verificado (válido por 30 días)
        user.registrar_acceso_exitoso()
        token = user.generar_token_sesion()
        db.session.commit()

        session.pop('pending_user_id', None)
        session['user'] = user.usuario
        session['role'] = user.role.lower() if user.role else 'user'
        session['user_role'] = session['role']
        session['secretaria'] = user.secretaria or ''
        session['token'] = token

        return redirect(url_for('main.dashboard'))

    return render_template('verify_2fa.html', usuario=user.usuario)


@auth_bp.route('/cambiar-clave-forzado', methods=['GET', 'POST'])
def cambiar_clave_forzado():
    """Cambio forzado de contraseña (cuando ha expirado)"""
    pending_id = session.get('pending_user_id')
    if not pending_id:
        return redirect(url_for('auth.login'))
    
    user = Usuario.query.get(pending_id)
    if not user:
        session.pop('pending_user_id', None)
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        clave_actual = request.form.get('clave_actual', '').strip()
        clave_nueva = request.form.get('clave_nueva', '').strip()
        confirmar_clave = request.form.get('confirmar_clave', '').strip()
        
        # Validaciones
        if not clave_actual or not clave_nueva or not confirmar_clave:
            flash('Por favor completa todos los campos', 'warning')
            return render_template('cambiar_clave_forzado.html', usuario=user.usuario)
        
        # Verificar contraseña actual
        if not user.check_password(clave_actual):
            flash('La contraseña actual es incorrecta', 'danger')
            return render_template('cambiar_clave_forzado.html', usuario=user.usuario)
        
        # Verificar que coincidan
        if clave_nueva != confirmar_clave:
            flash('Las contraseñas no coinciden', 'warning')
            return render_template('cambiar_clave_forzado.html', usuario=user.usuario)
        
        # Validar fortaleza y historial
        try:
            user.validar_nueva_clave(clave_nueva)
            user.set_password(clave_nueva)
            user.requiere_cambio_clave = False
            db.session.commit()
            
            # Auditoría
            auditoria = AuditoriaAcceso(
                usuario_id=user.id,
                usuario_nombre=user.usuario,
                accion='cambio_clave_forzado',
                ip_address=request.remote_addr,
                exitoso=True
            )
            db.session.add(auditoria)
            db.session.commit()
            
            session.pop('pending_user_id', None)
            
            # Crear sesión
            sesion = Sesion(
                usuario_id=user.id,
                usuario_nombre=user.usuario,
                token=secrets.token_urlsafe(32),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', ''),
                dispositivo='desktop'
            )
            db.session.add(sesion)
            db.session.commit()
            
            session['user'] = user.usuario
            session['role'] = user.role.lower()
            session['sesion_id'] = sesion.id
            
            flash('✅ Contraseña actualizada. Ahora puedes acceder.', 'success')
            return redirect(url_for('main.dashboard'))
            
        except ValueError as e:
            flash(f'⚠️ {str(e)}', 'warning')
            return render_template('cambiar_clave_forzado.html', usuario=user.usuario)
    
    return render_template('cambiar_clave_forzado.html', usuario=user.usuario)


# ===== VERIFICACIÓN DE PRIMER ACCESO =====
@auth_bp.route('/verificar-primer-acceso', methods=['GET', 'POST'])
def verificar_primer_acceso():
    """Verifica el código de primer acceso enviado por email"""
    
    user_id = session.get('pending_first_login_user_id')
    if not user_id:
        flash('Sesión inválida. Inicia sesión nuevamente.', 'danger')
        return redirect(url_for('auth.login'))
    
    user = Usuario.query.get(user_id)
    if not user:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip()
        
        if not codigo or len(codigo) != 6:
            flash('⚠️ El código debe tener exactamente 6 dígitos.', 'warning')
            return render_template('verificar_primer_acceso.html', usuario=user.usuario)
        
        # Verificar código
        if user.verificar_codigo_primer_acceso(codigo):
            db.session.commit()
            
            # Registrar acceso exitoso
            user.registrar_acceso_exitoso()
            token = user.generar_token_sesion()
            
            # Crear sesión
            sesion = Sesion(
                usuario_id=user.id,
                usuario_nombre=user.usuario,
                token=secrets.token_urlsafe(32),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', ''),
                dispositivo='desktop'
            )
            db.session.add(sesion)
            
            # Auditoría
            auditoria = AuditoriaAcceso(
                usuario_id=user.id,
                usuario_nombre=user.usuario,
                accion='primer_acceso_verificado',
                detalles=f'Verificación de primer acceso completada',
                ip_address=request.remote_addr,
                exitoso=True
            )
            db.session.add(auditoria)
            db.session.commit()
            
            # Persistir en sesión
            session.pop('pending_first_login_user_id', None)
            session['user'] = user.usuario
            session['role'] = user.role.lower() if user.role else 'user'
            session['user_role'] = session['role']
            session['secretaria'] = user.secretaria or ''
            session['token'] = token
            session['sesion_id'] = sesion.id
            
            flash('✅ Primer acceso verificado. Bienvenido/a.', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('⚠️ Código incorrecto o expirado. Intenta nuevamente.', 'warning')
            return render_template('verificar_primer_acceso.html', usuario=user.usuario)
    
    return render_template('verificar_primer_acceso.html', usuario=user.usuario)


