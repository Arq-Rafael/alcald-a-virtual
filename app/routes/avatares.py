"""
Rutas para servir avatares dinámicos
"""
from flask import Blueprint, request, Response, session, current_app
from app.utils.avatares import generate_avatar_svg, get_avatar_collections

avatares_bp = Blueprint('avatares', __name__, url_prefix='/api/avatar')

@avatares_bp.route('/<usuario>')
def avatar_dinamico(usuario):
    """
    Sirve un avatar SVG dinámico basado en estilo
    /api/avatar/admin?style=siluetas&collection=sil_1
    """
    style = request.args.get('style', 'siluetas')
    collection = request.args.get('collection', None)
    
    collections = get_avatar_collections()
    
    if style not in collections:
        style = 'siluetas'
    
    # Si no especifica colección, tomar la primera disponible
    if not collection:
        collection = collections[style]['avatars'][0]['id']
    
    svg = generate_avatar_svg(collection, style)
    return Response(svg, mimetype='image/svg+xml', 
                   headers={'Cache-Control': 'max-age=3600'})


@avatares_bp.route('/collections')
def list_collections():
    """
    Lista todas las colecciones de avatares disponibles
    """
    import json
    collections = get_avatar_collections()
    # Simplificar la respuesta para JSON
    response = {}
    for collection_name, collection_data in collections.items():
        response[collection_name] = {
            'name': collection_data['name'],
            'style': collection_data['style'],
            'avatars': [{'id': a['id']} for a in collection_data['avatars']]
        }
    return json.dumps(response), 200, {'Content-Type': 'application/json'}
