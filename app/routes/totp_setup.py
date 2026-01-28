"""
Rutas para configuración de TOTP (Autenticador)
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app import db
from app.models.usuario import Usuario
from app.utils.seguridad import TOTPHelper

totp_bp = Blueprint('totp', __name__, url_prefix='/seguridad/totp')


@totp_bp.route('/setup', methods=['GET'])
@login_required
def setup_totp_view():
    """
    Página para configurar TOTP.
    Genera un QR que el usuario escanea.
    """
    # Generar nuevo secreto
    secreto = TOTPHelper.generar_secreto(current_user.email)
    
    # Generar QR
    qr_base64 = TOTPHelper.generar_qr_base64(secreto, current_user.email)
    
    # Almacenar secreto en sesión temporalmente (sin guardar en DB aún)
    session['totp_setup_secret'] = secreto
    session['totp_setup_time'] = str(datetime.now())
    
    return render_template('seguridad/totp_setup.html', 
                          qr_data_url=qr_base64,
                          email=current_user.email)


@totp_bp.route('/verify-setup', methods=['POST'])
@login_required
def verify_totp_setup():
    """
    El usuario escanea el QR, ingresa un código de 6 dígitos.
    Si es correcto, guardamos el secreto.
    """
    data = request.get_json()
    codigo = data.get('codigo', '').strip()
    
    if not codigo or len(codigo) != 6:
        return jsonify({'success': False, 'error': 'Código inválido (debe ser 6 dígitos)'}), 400
    
    # Obtener secreto de sesión
    secreto = session.get('totp_setup_secret')
    if not secreto:
        return jsonify({'success': False, 'error': 'Sesión expirada, intenta de nuevo'}), 400
    
    # Verificar código
    if not TOTPHelper.verificar_codigo(secreto, codigo):
        return jsonify({'success': False, 'error': 'Código incorrecto, intenta de nuevo'}), 400
    
    # ✅ Código correcto: guardar secreto en BD
    current_user.set_totp_secret(secreto)
    db.session.commit()
    
    # Limpiar sesión
    session.pop('totp_setup_secret', None)
    session.pop('totp_setup_time', None)
    
    return jsonify({
        'success': True, 
        'message': '✅ Autenticador configurado correctamente',
        'redirect': url_for('dashboard.index')
    })


@totp_bp.route('/disable', methods=['POST'])
@login_required
def disable_totp():
    """Desactiva TOTP para el usuario actual"""
    current_user.preferencias = current_user.preferencias or {}
    current_user.preferencias['totp_enabled'] = False
    current_user.preferencias['totp_secret'] = None
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Autenticador desactivado'})


@totp_bp.route('/verify', methods=['POST'])
def verify_totp_code():
    """
    Verifica un código TOTP durante el login.
    Usada en la página de 2FA.
    """
    data = request.get_json()
    codigo = data.get('codigo', '').strip()
    user_id = session.get('pending_user_id')
    
    if not codigo or not user_id:
        return jsonify({'success': False, 'error': 'Datos inválidos'}), 400
    
    # Obtener usuario
    user = Usuario.query.get(user_id)
    if not user or not user.is_totp_enabled():
        return jsonify({'success': False, 'error': 'Usuario o TOTP no configurado'}), 400
    
    # Verificar código
    secreto = user.get_totp_secret()
    if not TOTPHelper.verificar_codigo(secreto, codigo):
        return jsonify({'success': False, 'error': 'Código TOTP incorrecto'}), 400
    
    # ✅ Código correcto: completar login (ver app/routes/auth.py para integración)
    return jsonify({'success': True, 'message': 'Verificado correctamente'})


from datetime import datetime
