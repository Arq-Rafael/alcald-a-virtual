from flask import Blueprint, session, Response, current_app
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
