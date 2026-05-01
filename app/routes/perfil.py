from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify, send_from_directory
from app import db
from app.models.usuario import Usuario
import os
import time
from werkzeug.utils import secure_filename
import json

perfil_bp = Blueprint('perfil', __name__, url_prefix='/perfil')

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2 MB

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
            
            upload_dir = _avatar_upload_dir()
            filename = secure_filename(f"{user.usuario}.{ext}")
            path = os.path.join(upload_dir, filename)
            file.save(path)

            user.foto_perfil = f"perfil/foto/{filename}"
            db.session.commit()
            # Respuesta según tipo de solicitud
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=True, foto_perfil=user.foto_perfil)
            flash('Foto de perfil actualizada', 'success')
            return redirect(url_for('perfil.perfil'))

    # Render
    return render_template('perfil.html', usuario=user, preferencias=user.get_preferencias())


# ══════════════════════════════════════════════════════════════════════════════
#  ENDPOINTS DEDICADOS — AVATAR & PERFIL
# ══════════════════════════════════════════════════════════════════════════════

def _avatar_upload_dir():
    """Devuelve la ruta absoluta de la carpeta de avatares y la crea si falta."""
    base = str(current_app.config.get('BASE_DIR', os.getcwd()))
    path = os.path.join(base, 'uploads', 'perfiles')
    os.makedirs(path, exist_ok=True)
    return path


@perfil_bp.route('/avatar/upload', methods=['POST'])
def avatar_upload():
    """Subida segura de foto de perfil.
    Valida extensión, tamaño ≤ 2 MB y renombra con timestamp para evitar colisiones.
    """
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401

    user = Usuario.query.filter_by(usuario=session['user']).first()
    if not user:
        return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404

    file = request.files.get('foto')
    if not file or file.filename == '':
        return jsonify({'success': False, 'error': 'Selecciona una imagen'}), 400

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({'success': False,
                        'error': 'Formato no permitido. Usa JPG, PNG o WEBP'}), 400

    # Validar tamaño antes de guardar
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_AVATAR_SIZE:
        return jsonify({'success': False, 'error': 'La imagen supera 2 MB'}), 400

    upload_dir = _avatar_upload_dir()
    filename = secure_filename(f"avatar_{user.id}_{int(time.time())}.{ext}")
    file.save(os.path.join(upload_dir, filename))

    # Eliminar foto anterior si era una subida personalizada
    old_foto = user.foto_perfil or ''
    old_name = None
    if old_foto.startswith('perfil/foto/'):
        old_name = old_foto.replace('perfil/foto/', '')
    elif old_foto.startswith('uploads/perfiles/'):
        old_name = old_foto.replace('uploads/perfiles/', '')
    if old_name:
        old_path = os.path.join(upload_dir, old_name)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass

    user.foto_perfil = f"perfil/foto/{filename}"
    db.session.commit()

    return jsonify({
        'success': True,
        'foto_perfil': user.foto_perfil,
        'url': '/' + user.foto_perfil,
    })


@perfil_bp.route('/avatar/select', methods=['POST'])
def avatar_select():
    """Guarda la elección de avatar alternativo (colección SVG) para el usuario."""
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401

    user = Usuario.query.filter_by(usuario=session['user']).first()
    if not user:
        return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404

    data = request.get_json(silent=True) or {}
    avatar_style      = data.get('avatar_style', 'siluetas')
    avatar_collection = data.get('avatar_key') or data.get('avatar_collection', '')

    prefs = user.get_preferencias()
    prefs['avatar_style']      = avatar_style
    prefs['avatar_collection'] = avatar_collection
    user.set_preferencias(prefs)
    db.session.commit()

    return jsonify({'success': True, 'avatar_style': avatar_style,
                    'avatar_collection': avatar_collection})


@perfil_bp.route('/foto/<path:filename>')
def servir_foto(filename):
    """Sirve fotos de perfil subidas por los usuarios."""
    return send_from_directory(_avatar_upload_dir(), filename)


@perfil_bp.route('/update', methods=['POST'])
def perfil_update():
    """Actualiza datos básicos del perfil: nombre visible y/o preferencias de tema."""
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401

    user = Usuario.query.filter_by(usuario=session['user']).first()
    if not user:
        return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404

    data = request.get_json(silent=True) or {}

    nombre = data.get('nombre_completo', '').strip()
    if nombre:
        user.nombre_completo = nombre

    prefs = user.get_preferencias()
    for campo in ('tema', 'tamano_fuente', 'tipo_fuente', 'idioma', 'color_acento'):
        if campo in data:
            prefs[campo] = data[campo]
    if 'notificaciones' in data:
        prefs['notificaciones'] = bool(data['notificaciones'])
    user.set_preferencias(prefs)

    db.session.commit()
    return jsonify({'success': True, 'nombre_completo': user.nombre_completo})
