from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify
from app import db
from app.models.usuario import Usuario
import os
from werkzeug.utils import secure_filename
import json

perfil_bp = Blueprint('perfil', __name__, url_prefix='/perfil')

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}

@perfil_bp.route('', methods=['GET', 'POST'])
def perfil():
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    user = Usuario.query.filter_by(usuario=session['user']).first()
    if not user:
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('auth.logout'))

    if request.method == 'POST':
        accion = request.form.get('accion')
        
        if accion == 'guardar_prefs':
            tema = request.form.get('tema', 'light')
            tamano = request.form.get('tamano_fuente', 'medium')
            tipo = request.form.get('tipo_fuente', 'system')
            idioma = request.form.get('idioma', 'es')
            notificaciones = request.form.get('notificaciones') == 'on'
            avatar_style = request.form.get('avatar_style', 'siluetas')
            avatar_collection = request.form.get('avatar_collection', None)
            
            prefs = {
                'tema': tema,
                'tamano_fuente': tamano,
                'tipo_fuente': tipo,
                'idioma': idioma,
                'notificaciones': notificaciones,
                'avatar_style': avatar_style,
                'avatar_collection': avatar_collection
            }
            user.set_preferencias(prefs)
            db.session.commit()
            
            # Si es solicitud AJAX, responde JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=True, message='Preferencias guardadas')
            
            flash('Preferencias guardadas', 'success')
            return redirect(url_for('perfil.perfil'))
        
        if accion == 'subir_foto':
            file = request.files.get('foto')
            if not file or file.filename == '':
                flash('Selecciona una imagen', 'warning')
                # Si es una solicitud AJAX, responde JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify(success=False, error='Selecciona una imagen')
                return redirect(url_for('perfil.perfil'))
            
            ext = file.filename.rsplit('.', 1)[-1].lower()
            if ext not in ALLOWED_IMAGE_EXTENSIONS:
                flash('Formato de imagen no permitido. Usa PNG/JPG/JPEG', 'danger')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify(success=False, error='Formato de imagen no permitido')
                return redirect(url_for('perfil.perfil'))
            
            upload_dir = os.path.join(str(current_app.config.get('BASE_DIR', os.getcwd())), 'uploads', 'perfiles')
            os.makedirs(upload_dir, exist_ok=True)
            filename = secure_filename(f"{user.usuario}.{ext}")
            path = os.path.join(upload_dir, filename)
            file.save(path)
            
            user.foto_perfil = f"uploads/perfiles/{filename}"
            db.session.commit()
            # Respuesta según tipo de solicitud
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=True, foto_perfil=user.foto_perfil)
            flash('Foto de perfil actualizada', 'success')
            return redirect(url_for('perfil.perfil'))

    # Render
    return render_template('perfil.html', usuario=user, preferencias=user.get_preferencias())
