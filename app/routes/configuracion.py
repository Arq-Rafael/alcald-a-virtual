
import os
import json
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app, send_file
from app.utils import admin_required, normalize_features
from app import db
from app.models.usuario import Usuario, AuditoriaAcceso
from app.utils.seguridad import PasswordValidator, EmailService
from app.utils.backup import BackupManager

configuracion_bp = Blueprint('configuracion', __name__)

def load_config_data():
    path = os.path.join(current_app.config['BASE_DIR'], "config.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config_data(cfg):
    path = os.path.join(current_app.config['BASE_DIR'], "config.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def get_module_catalog():
    return [
        {'key': 'redactar', 'label': 'Redactar Oficios'},
        {'key': 'solicitudes', 'label': 'Solicitudes'},
        {'key': 'calendario', 'label': 'Calendario'},
        {'key': 'participacion', 'label': 'Participacion'},
        {'key': 'geoportal', 'label': 'Geoportal'},
        {'key': 'seguimiento', 'label': 'Seguimiento'},
        {'key': 'riesgo', 'label': 'Gestion del Riesgo'},
        {'key': 'contratos', 'label': 'Contratos'},
        {'key': 'certificados', 'label': 'Certificados'},
        {'key': 'ia', 'label': 'IA'},
        {'key': 'configuracion', 'label': 'Configuracion'}
    ]

def build_features_config(cfg, users):
    features = cfg.get('features') or {}
    usernames = [u.usuario for u in users if u.usuario != 'admin']
    updated = False

    for module in get_module_catalog():
        key = module['key']
        allowed = features.get(key)
        if not isinstance(allowed, list):
            allowed = []
        if key not in features:
            allowed = list(usernames)
            updated = True
        features[key] = allowed

    if updated:
        cfg['features'] = features
        save_config_data(cfg)
        current_app.config["APP_FEATURES"] = normalize_features(features)

    return features

def list_users_db():
    users = Usuario.query.order_by(Usuario.usuario.asc()).all()
    return users

def _user_dict(u):
    """Convierte usuario a diccionario"""
    return {
        'id': u.id,
        'usuario': u.usuario,
        'email': u.email,
        'role': u.role,
        'secretaria': u.secretaria,
        'activo': u.activo,
        'bloqueado': u.bloqueado,
        'ultimo_acceso': u.ultimo_acceso.strftime('%d/%m/%Y %H:%M') if u.ultimo_acceso else 'Nunca',
        'creado_en': u.creado_en.strftime('%d/%m/%Y') if u.creado_en else '-'
    }

@configuracion_bp.route('/configuracion', methods=['GET','POST'], endpoint='index')
@admin_required
def configuracion():
    """Panel de administración completo"""
    cfg = load_config_data()
    usuarios = list_users_db()
    auditoria_logs = AuditoriaAcceso.query.order_by(AuditoriaAcceso.timestamp.desc()).limit(10).all()
    current_username = session.get('user')
    my_email = None
    if current_username:
        me = Usuario.query.filter_by(usuario=current_username).first()
        if me:
            my_email = me.email
    
    # Estadísticas
    total_usuarios = len(usuarios)
    usuarios_activos = sum(1 for u in usuarios if u.activo)
    admins = sum(1 for u in usuarios if u.role == 'admin')
    module_catalog = get_module_catalog()
    users_for_permissions = [u for u in usuarios if u.usuario != 'admin']
    features_cfg = build_features_config(cfg, usuarios)

    if request.method == 'POST':
        form = request.form

        # ===== AGREGAR USUARIO MANUAL =====
        if 'add_user' in form:
            nuevo_u = form.get('new_usuario','').strip()
            nuevo_e = form.get('new_email','').strip()
            nuevo_p = form.get('new_clave','').strip()
            nueva_secretaria = form.get('new_secretaria','').strip()
            nuevo_role = form.get('new_role','user').lower().strip()

            if not (nuevo_u and nuevo_p):
                flash('Usuario y contraseña son obligatorios', 'danger')
                return redirect(url_for('configuracion.index'))

            # Validar que el usuario sea único
            existe = Usuario.query.filter_by(usuario=nuevo_u).first()
            if existe:
                flash(f"El usuario '{nuevo_u}' ya existe", 'warning')
                return redirect(url_for('configuracion.index'))

            # Validar email si se proporciona
            if nuevo_e and Usuario.query.filter_by(email=nuevo_e).first():
                flash(f"El email '{nuevo_e}' ya está registrado", 'warning')
                return redirect(url_for('configuracion.index'))

            # Validar fortaleza de contraseña
            es_valida, errores, puntuacion = PasswordValidator.validar_fortaleza(nuevo_p)
            if not es_valida:
                msg = 'Contraseña débil. ' + ', '.join(errores)
                flash(msg, 'danger')
                return redirect(url_for('configuracion.index'))

            # Validar role
            if nuevo_role not in ['admin', 'user']:
                nuevo_role = 'user'

            try:
                user = Usuario(
                    usuario=nuevo_u,
                    clave=nuevo_p,
                    email=nuevo_e if nuevo_e else None,
                    role=nuevo_role,
                    secretaria=nueva_secretaria,
                    activo=True,
                    creado_por=session.get('user'),
                    requiere_2fa=bool(nuevo_e)
                )
                db.session.add(user)
                
                # Registrar en auditoría
                auditoria = AuditoriaAcceso(
                    usuario_id=1,  # Admin que realiza la acción
                    usuario_nombre=session.get('user', 'admin'),
                    accion='crear_usuario',
                    detalles=f"Creado usuario: {nuevo_u}",
                    ip_address=request.remote_addr,
                    exitoso=True
                )
                db.session.add(auditoria)
                db.session.commit()

                # Agregar el usuario nuevo a permisos por modulo (si aplica)
                if cfg.get('features'):
                    for key, allowed in cfg.get('features', {}).items():
                        if isinstance(allowed, list) and nuevo_u not in allowed:
                            allowed.append(nuevo_u)
                    save_config_data(cfg)
                    current_app.config["APP_FEATURES"] = normalize_features(cfg.get('features'))

                # Enviar email de bienvenida si tiene email
                if nuevo_e:
                    try:
                        from app.utils.email_resend import send_initial_password_email
                        resultado = send_initial_password_email(
                            email=nuevo_e,
                            nombre_usuario=nuevo_u,
                            password_temporal=nuevo_p
                        )
                        if resultado.get('success'):
                            flash(f"✅ Usuario '{nuevo_u}' creado. Email de bienvenida enviado a {nuevo_e}", 'success')
                        else:
                            flash(f"✅ Usuario '{nuevo_u}' creado. Email NO enviado (Resend requiere dominio verificado). El usuario puede acceder normalmente.", 'warning')
                    except Exception as email_error:
                        # No fallar si el email falla, solo notificar
                        flash(f"✅ Usuario '{nuevo_u}' creado. Email NO enviado: {str(email_error)}. El usuario puede acceder normalmente.", 'warning')
                else:
                    flash(f"✅ Usuario '{nuevo_u}' creado exitosamente (sin email configurado)", 'success')
            except Exception as e:
                db.session.rollback()
                flash(f"❌ Error al crear usuario: {str(e)}", 'danger')
            return redirect(url_for('configuracion.index'))

        # ===== PERMISOS POR MODULO (POR USUARIO) =====
        if 'update_permissions' in form:
            features = {}
            for module in module_catalog:
                key = module['key']
                allowed_users = []
                for user in users_for_permissions:
                    field_name = f"perm_{key}_{user.usuario}"
                    if form.get(field_name) == 'on':
                        allowed_users.append(user.usuario)
                features[key] = allowed_users

            cfg['features'] = features
            save_config_data(cfg)
            current_app.config["APP_FEATURES"] = normalize_features(features)
            flash('✅ Permisos de modulos actualizados', 'success')
            return redirect(url_for('configuracion.index'))

        # ===== ELIMINAR USUARIO =====
        if 'delete_user' in form:
            to_del = form.get('delete_user')
            
            # No permitir eliminar al usuario actual
            if to_del == session.get('user'):
                flash("❌ No puedes eliminar tu propio usuario", 'danger')
                return redirect(url_for('configuracion.index'))
            
            user = Usuario.query.filter_by(usuario=to_del).first()
            if user:
                try:
                    username_to_delete = user.usuario
                    user_id = user.id
                    
                    # Eliminar sesiones del usuario primero (evitar foreign key constraint)
                    from app.models.usuario import Sesion
                    Sesion.query.filter_by(usuario_id=user_id).delete()
                    
                    # Eliminar auditorías del usuario (si las hay)
                    AuditoriaAcceso.query.filter_by(usuario_id=user_id).delete()
                    
                    # Ahora eliminar el usuario
                    db.session.delete(user)
                    
                    # Auditoría de la eliminación
                    auditoria = AuditoriaAcceso(
                        usuario_id=1,
                        usuario_nombre=session.get('user', 'admin'),
                        accion='eliminar_usuario',
                        detalles=f"Eliminado usuario: {username_to_delete}",
                        ip_address=request.remote_addr,
                        exitoso=True
                    )
                    db.session.add(auditoria)
                    db.session.commit()
                    
                    flash(f"✅ Usuario '{username_to_delete}' eliminado", 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f"❌ Error al eliminar: {str(e)}", 'danger')
            else:
                flash('❌ Usuario no encontrado', 'danger')
            return redirect(url_for('configuracion.index'))

        # ===== CAMBIAR CONTRASEÑA DE USUARIO =====
        if 'change_password' in form:
            user_id = form.get('user_id')
            nueva_clave = form.get('change_password_value','').strip()
            
            if not nueva_clave:
                flash('La contraseña no puede estar vacía', 'danger')
                return redirect(url_for('configuracion.index'))
            
            user = Usuario.query.get(user_id)
            if not user:
                flash('Usuario no encontrado', 'danger')
                return redirect(url_for('configuracion.index'))
            
            # Validar fortaleza
            es_valida, errores, _ = PasswordValidator.validar_fortaleza(nueva_clave)
            if not es_valida:
                flash('Contraseña débil: ' + ', '.join(errores), 'danger')
                return redirect(url_for('configuracion.index'))
            
            try:
                user.set_password(nueva_clave)
                user.intentos_fallidos = 0
                user.bloqueado = False
                
                # Auditoría
                auditoria = AuditoriaAcceso(
                    usuario_id=1,
                    usuario_nombre=session.get('user', 'admin'),
                    accion='cambiar_contrasena',
                    detalles=f"Contraseña cambiada para: {user.usuario}",
                    ip_address=request.remote_addr,
                    exitoso=True
                )
                db.session.add(auditoria)
                db.session.commit()

                # Notificar cambio de clave al usuario
                if user.email:
                    ok_mail = EmailService.enviar_notificacion_cambio_clave(user.email, user.usuario, request.remote_addr)
                    if not ok_mail:
                        flash('Aviso: no se pudo enviar correo de cambio de contraseña. Verifica SMTP.', 'warning')
                
                # Notificaciones por correo desactivadas (SMTP bloqueado en Railway)
                
                flash(f"✅ Contraseña de '{user.usuario}' actualizada", 'success')
            except Exception as e:
                db.session.rollback()
                flash(f"❌ Error: {str(e)}", 'danger')
            return redirect(url_for('configuracion.index'))

        # ===== CAMBIAR ROL DE USUARIO =====
        if 'change_role' in form:
            user_id = form.get('user_id')
            nuevo_role = form.get('change_role_value', 'user').lower()
            
            if nuevo_role not in ['admin', 'user']:
                nuevo_role = 'user'
            
            user = Usuario.query.get(user_id)
            if user:
                try:
                    rol_anterior = user.role
                    user.role = nuevo_role
                    
                    # Auditoría
                    auditoria = AuditoriaAcceso(
                        usuario_id=1,
                        usuario_nombre=session.get('user', 'admin'),
                        accion='cambiar_rol',
                        detalles=f"Rol de {user.usuario}: {rol_anterior} → {nuevo_role}",
                        ip_address=request.remote_addr,
                        exitoso=True
                    )
                    db.session.add(auditoria)
                    db.session.commit()
                    
                    flash(f"✅ Rol de '{user.usuario}' actualizado a '{nuevo_role}'", 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f"❌ Error: {str(e)}", 'danger')
            return redirect(url_for('configuracion.index'))

        # ===== BLOQUEAR/DESBLOQUEAR USUARIO =====
        if 'toggle_block' in form:
            user_id = form.get('user_id')
            user = Usuario.query.get(user_id)
            if user and user.usuario != session.get('user'):
                try:
                    user.bloqueado = not user.bloqueado
                    user.intentos_fallidos = 0
                    
                    # Auditoría
                    accion = 'bloquear_usuario' if user.bloqueado else 'desbloquear_usuario'
                    auditoria = AuditoriaAcceso(
                        usuario_id=1,
                        usuario_nombre=session.get('user', 'admin'),
                        accion=accion,
                        detalles=f"Usuario {user.usuario}: {accion}",
                        ip_address=request.remote_addr,
                        exitoso=True
                    )
                    db.session.add(auditoria)
                    db.session.commit()
                    
                    estado = "bloqueado" if user.bloqueado else "desbloqueado"
                    flash(f"✅ Usuario '{user.usuario}' {estado}", 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f"❌ Error: {str(e)}", 'danger')
            return redirect(url_for('configuracion.index'))

        # ===== ACTUALIZAR MI EMAIL (ADMIN) =====
        if 'update_my_email' in form:
            nuevo_email = form.get('my_email', '').strip()
            current_username = session.get('user')
            if not current_username:
                flash('Sesión expirada. Inicia sesión nuevamente.', 'danger')
                return redirect(url_for('auth.login'))

            if not nuevo_email:
                flash('El correo no puede estar vacío.', 'warning')
                return redirect(url_for('configuracion.index'))

            # Validar unicidad
            existe = Usuario.query.filter(Usuario.email == nuevo_email, Usuario.usuario != current_username).first()
            if existe:
                flash('Ese correo ya está en uso por otro usuario.', 'warning')
                return redirect(url_for('configuracion.index'))

            user = Usuario.query.filter_by(usuario=current_username).first()
            if not user:
                flash('No se encontró el usuario actual.', 'danger')
                return redirect(url_for('configuracion.index'))

            try:
                user.email = nuevo_email
                user.requiere_2fa = True
                user.email_verificado = False

                auditoria = AuditoriaAcceso(
                    usuario_id=user.id,
                    usuario_nombre=current_username,
                    accion='actualizar_email_propio',
                    detalles=f"Nuevo correo: {nuevo_email}",
                    ip_address=request.remote_addr,
                    exitoso=True
                )
                db.session.add(auditoria)
                db.session.commit()

                ok_mail = EmailService.enviar_notificacion_registro(nuevo_email, current_username)
                if not ok_mail:
                    flash('Correo no enviado. Verifica configuración SMTP.', 'warning')

                flash('Correo actualizado y 2FA activado para el usuario actual.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f"Error al actualizar correo: {str(e)}", 'danger')
            return redirect(url_for('configuracion.index'))

        # ===== ENVIAR CORREO RAPIDO =====
        if 'send_quick_email' in form:
            to_email = form.get('quick_email_to', '').strip()
            subject = form.get('quick_email_subject', '').strip()
            message = form.get('quick_email_message', '').strip()

            if not to_email or not subject or not message:
                flash('❌ Completa destinatario, asunto y mensaje', 'warning')
                return redirect(url_for('configuracion.index'))

            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
              <div style="background: #ffffff; border-radius: 12px; padding: 24px; max-width: 640px; margin: 0 auto; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h2 style="margin: 0 0 12px 0; color: #1f2937;">{subject}</h2>
                <p style="color: #374151; font-size: 15px; line-height: 1.6; white-space: pre-wrap;">{message}</p>
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;" />
                <p style="color: #9ca3af; font-size: 12px;">Alcaldia Virtual - Mensaje enviado desde Configuracion</p>
              </div>
            </body>
            </html>
            """

            try:
                from app.utils.email_resend import send_email_resend
                resultado = send_email_resend(to_email, subject, html)
                if resultado.get('success'):
                    flash(f"✅ Email enviado a {to_email}", 'success')
                else:
                    flash(f"❌ No se pudo enviar el correo: {resultado.get('message')}", 'danger')
            except Exception as e:
                flash(f"❌ Error enviando correo: {str(e)}", 'danger')
            return redirect(url_for('configuracion.index'))

        # ===== BACKUP POR MODULOS =====
        if 'backup_modulos' in form:
            seleccion = request.form.getlist('backup_modules')
            if not seleccion:
                flash('❌ Selecciona al menos un modulo para el backup', 'warning')
                return redirect(url_for('configuracion.index'))

            module_paths = {
                'solicitudes': current_app.config.get('SOLICITUDES_PATH'),
                'certificados': str(current_app.config.get('CERTIFICADOS_OUTPUT_DIR')),
                'contratos': str(current_app.config.get('CONTRATOS_OUTPUT_DIR')),
                'riesgo': os.path.join(str(current_app.config.get('DOCUMENTOS_DIR')), 'gestion_riesgo')
            }
            directorios = [module_paths.get(m) for m in seleccion if module_paths.get(m)]

            try:
                bm = BackupManager(current_app)
                exito, ruta, msg = bm.backup_archivos(directorios=directorios, descripcion='modulos')
                if not exito:
                    flash(f"❌ Error en backup: {msg}", 'danger')
                    return redirect(url_for('configuracion.index'))

                auditoria = AuditoriaAcceso(
                    usuario_id=1,
                    usuario_nombre=session.get('user', 'admin'),
                    accion='crear_backup_modulos',
                    detalles=f"Backup modulos: {', '.join(seleccion)}",
                    ip_address=request.remote_addr,
                    exitoso=True
                )
                db.session.add(auditoria)
                db.session.commit()

                return send_file(ruta, as_attachment=True, download_name=os.path.basename(ruta))
            except Exception as e:
                flash(f"❌ Error: {str(e)}", 'danger')
            return redirect(url_for('configuracion.index'))

    return render_template(
        'configuracion.html',
        usuarios=usuarios,
        usuarios_dict=[_user_dict(u) for u in usuarios],
        stats={
            'total': total_usuarios,
            'activos': usuarios_activos,
            'inactivos': total_usuarios - usuarios_activos,
            'admins': admins
        },
        auditoria=auditoria_logs,
        my_email=my_email,
        module_catalog=module_catalog,
        permissions_users=users_for_permissions,
        features_cfg=features_cfg
    )
