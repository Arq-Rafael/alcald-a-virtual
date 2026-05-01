from flask import Blueprint, session, Response, current_app, request, jsonify
from app.utils.preferencias import generate_preference_css, get_user_preferences

api_prefs_bp = Blueprint('api_prefs', __name__, url_prefix='/api/prefs')

@api_prefs_bp.route('/css')
def get_preferences_css():
    """
    Endpoint que retorna el CSS dinámico basado en preferencias del usuario
    """
    prefs = get_user_preferences(session)
    css = generate_preference_css(prefs)
    return Response(css, mimetype='text/css')

@api_prefs_bp.route('/featured', methods=['GET'])
def get_featured():
    if not session.get('user'):
        return jsonify({'error': 'unauthorized'}), 401
    try:
        from app.models.usuario import Usuario
        user = Usuario.query.filter_by(usuario=session['user']).first()
        prefs = user.get_preferencias() if user else {}
        return jsonify({'featured': prefs.get('featured_modules', [])})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_prefs_bp.route('/featured', methods=['POST'])
def set_featured():
    if not session.get('user'):
        return jsonify({'error': 'unauthorized'}), 401
    data = request.get_json(silent=True) or {}
    modules = data.get('modules', [])
    if not isinstance(modules, list):
        return jsonify({'error': 'invalid'}), 400
    modules = [str(m) for m in modules[:4]]  # max 4
    try:
        from app.models.usuario import Usuario
        from app import db
        user = Usuario.query.filter_by(usuario=session['user']).first()
        if not user:
            return jsonify({'error': 'user not found'}), 404
        prefs = user.get_preferencias()
        prefs['featured_modules'] = modules
        user.set_preferencias(prefs)
        db.session.commit()
        return jsonify({'ok': True, 'featured': modules})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
