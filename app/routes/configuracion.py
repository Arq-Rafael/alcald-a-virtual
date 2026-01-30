
import os
import json
import pandas as pd
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app, jsonify
from app.utils import admin_required
from app import db
from app.models.usuario import Usuario, AuditoriaAcceso
from app.utils.seguridad import PasswordValidator, EmailService
from app.utils.backup import BackupManager
from werkzeug.utils import secure_filename
from datetime import datetime

configuracion_bp = Blueprint('configuracion', __name__)

def load_config_data():
    path = os.path.join(current_app.config['BASE_DIR'], "config.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

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
                    email=nuevo_e,
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

                # Notificaciones
                admin_alert = current_app.config.get('ADMIN_ALERT_EMAIL')
                correo_ok = True
                # Notificaciones por correo desactivadas (SMTP bloqueado en Railway)
                
                flash(f"✅ Usuario '{nuevo_u}' creado exitosamente", 'success')
            except Exception as e:
                db.session.rollback()
                flash(f"❌ Error al crear usuario: {str(e)}", 'danger')
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

        # ===== IMPORTAR USUARIOS DESDE EXCEL =====
        if 'import_excel' in form:
            file = request.files.get('excel_file')
            if not file or file.filename == '':
                flash('❌ Selecciona un archivo Excel', 'warning')
                return redirect(url_for('configuracion.index'))

            try:
                df = pd.read_excel(file)
                df.columns = df.columns.str.strip().str.lower()
                creados, omitidos = 0, 0
                errores_detail = []
                
                for idx, row in df.iterrows():
                    usuario = str(row.get('usuario', '')).strip()
                    clave = str(row.get('clave', '')).strip()
                    email = str(row.get('email', '')).strip() or None
                    secretaria = str(row.get('secretaria', '')).strip()
                    role = str(row.get('role', 'user')).strip().lower() or 'user'

                    # Validaciones
                    if not usuario or not clave:
                        omitidos += 1
                        errores_detail.append(f"Fila {idx+2}: Usuario o clave vacío")
                        continue

                    if Usuario.query.filter_by(usuario=usuario).first():
                        omitidos += 1
                        errores_detail.append(f"Fila {idx+2}: Usuario '{usuario}' ya existe")
                        continue

                    if email and Usuario.query.filter_by(email=email).first():
                        omitidos += 1
                        errores_detail.append(f"Fila {idx+2}: Email '{email}' ya existe")
                        continue

                    es_valida, _, _ = PasswordValidator.validar_fortaleza(clave)
                    if not es_valida:
                        omitidos += 1
                        errores_detail.append(f"Fila {idx+2}: Contraseña débil para '{usuario}'")
                        continue

                    if role not in ['admin', 'user']:
                        role = 'user'

                    try:
                        u = Usuario(
                            usuario=usuario,
                            clave=clave,
                            email=email,
                            role=role,
                            secretaria=secretaria,
                            activo=True,
                            creado_por=session.get('user'),
                            requiere_2fa=bool(email)
                        )
                        db.session.add(u)
                        creados += 1
                    except:
                        omitidos += 1
                        errores_detail.append(f"Fila {idx+2}: Error al crear usuario '{usuario}'")

                db.session.commit()
                
                msg = f"✅ Importación completada: {creados} creados, {omitidos} omitidos"
                flash(msg, 'success')
                if errores_detail:
                    for error in errores_detail[:5]:
                        flash(f"  ⚠️ {error}", 'info')
                    if len(errores_detail) > 5:
                        flash(f"  ... y {len(errores_detail)-5} errores más", 'info')
            except Exception as e:
                db.session.rollback()
                flash(f"❌ Error importando Excel: {str(e)}", 'danger')
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

        # ===== CREAR BACKUP =====
        if 'do_backup' in form:
            tipo = form.get('backup_tipo', 'completo')
            try:
                bm = BackupManager(current_app)
                if tipo == 'database':
                    exito, ruta, msg = bm.backup_database('manual')
                elif tipo == 'archivos':
                    exito, ruta, msg = bm.backup_archivos(descripcion='manual')
                else:
                    exito, ruta, msg = bm.backup_completo('manual')
                
                if exito:
                    flash(f"✅ Backup creado: {msg}", 'success')
                    
                    # Auditoría
                    auditoria = AuditoriaAcceso(
                        usuario_id=1,
                        usuario_nombre=session.get('user', 'admin'),
                        accion='crear_backup',
                        detalles=f"Backup {tipo} creado",
                        ip_address=request.remote_addr,
                        exitoso=True
                    )
                    db.session.add(auditoria)
                    db.session.commit()
                else:
                    flash(f"❌ Error en backup: {msg}", 'danger')
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
        my_email=my_email
    )
