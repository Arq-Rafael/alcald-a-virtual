"""
Sistema de Avatares Predefinidos
Proporciona colecciones de avatares SVG con estilos modernos
"""

def get_avatar_collections():
    """
    Retorna colecciones de avatares predefinidos
    """
    return {
        'siluetas': {
            'name': 'Siluetas Modernas',
            'style': 'monochrome',
            'avatars': [
                {'id': 'sil_1', 'color': '#7cb342', 'icon': '👤'},
                {'id': 'sil_2', 'color': '#00bcd4', 'icon': '👤'},
                {'id': 'sil_3', 'color': '#ff6b6b', 'icon': '👤'},
                {'id': 'sil_4', 'color': '#ffa500', 'icon': '👤'},
                {'id': 'sil_5', 'color': '#9c27b0', 'icon': '👤'},
                {'id': 'sil_6', 'color': '#e91e63', 'icon': '👤'},
            ]
        },
        'gradientes': {
            'name': 'Gradientes Vibrantes',
            'style': 'gradient',
            'avatars': [
                {'id': 'grad_1', 'gradient': '#7cb342,#9ccc65', 'icon': 'leaf'},
                {'id': 'grad_2', 'gradient': '#00bcd4,#80deea', 'icon': 'water'},
                {'id': 'grad_3', 'gradient': '#ff6b6b,#ff8e72', 'icon': 'fire'},
                {'id': 'grad_4', 'gradient': '#ffa500,#ffcc80', 'icon': 'sun'},
                {'id': 'grad_5', 'gradient': '#9c27b0,#ce93d8', 'icon': 'star'},
                {'id': 'grad_6', 'gradient': '#e91e63,#f48fb1', 'icon': 'heart'},
            ]
        },
        'iniciales': {
            'name': 'Iniciales Personalizadas',
            'style': 'initials',
            'avatars': [
                {'id': 'init_1', 'color': '#1b5e20', 'pattern': 'dots'},
                {'id': 'init_2', 'color': '#0277bd', 'pattern': 'waves'},
                {'id': 'init_3', 'color': '#c62828', 'pattern': 'grid'},
                {'id': 'init_4', 'color': '#f57f17', 'pattern': 'stripes'},
                {'id': 'init_5', 'color': '#6a1b9a', 'pattern': 'circles'},
                {'id': 'init_6', 'color': '#00695c', 'pattern': 'hexagon'},
            ]
        },
        'gaming': {
            'name': 'Gaming & Pixel Art',
            'style': 'pixel',
            'avatars': [
                {'id': 'game_1', 'desc': 'Knight', 'color': '#c0392b'},
                {'id': 'game_2', 'desc': 'Mage', 'color': '#8e44ad'},
                {'id': 'game_3', 'desc': 'Ranger', 'color': '#27ae60'},
                {'id': 'game_4', 'desc': 'Rogue', 'color': '#000000'},
                {'id': 'game_5', 'desc': 'Paladin', 'color': '#f39c12'},
                {'id': 'game_6', 'desc': 'Necromancer', 'color': '#34495e'},
            ]
        },
        'minimalistas': {
            'name': 'Minimalistas Elegantes',
            'style': 'minimal',
            'avatars': [
                {'id': 'min_1', 'symbol': '●', 'color': '#7cb342'},
                {'id': 'min_2', 'symbol': '◆', 'color': '#00bcd4'},
                {'id': 'min_3', 'symbol': '■', 'color': '#ff6b6b'},
                {'id': 'min_4', 'symbol': '▲', 'color': '#ffa500'},
                {'id': 'min_5', 'symbol': '◐', 'color': '#9c27b0'},
                {'id': 'min_6', 'symbol': '◇', 'color': '#e91e63'},
            ]
        }
    }


def generate_avatar_svg(avatar_id, collection_type='siluetas'):
    """
    Genera un SVG de avatar basado en ID y colección
    """
    collections = get_avatar_collections()
    
    if collection_type not in collections:
        collection_type = 'siluetas'
    
    collection = collections[collection_type]
    avatars = collection['avatars']
    avatar_data = next((a for a in avatars if a['id'] == avatar_id), avatars[0])
    
    if collection_type == 'siluetas':
        return _generate_silueta(avatar_data)
    elif collection_type == 'gradientes':
        return _generate_gradient(avatar_data)
    elif collection_type == 'iniciales':
        return _generate_initials(avatar_data)
    elif collection_type == 'gaming':
        return _generate_gaming(avatar_data)
    elif collection_type == 'minimalistas':
        return _generate_minimal(avatar_data)
    
    return _generate_silueta(avatar_data)


def _generate_silueta(data):
    """SVG silueta con color sólido"""
    color = data.get('color', '#7cb342')
    return f'''<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <style>
                .avatar-bg {{ fill: {color}; }}
                .avatar-circle {{ fill: rgba(255,255,255,0.15); }}
                .avatar-head {{ fill: white; opacity: 0.9; }}
            </style>
        </defs>
        <rect class="avatar-bg" width="200" height="200" rx="100"/>
        <circle class="avatar-circle" cx="100" cy="60" r="45"/>
        <ellipse class="avatar-circle" cx="100" cy="140" rx="55" ry="50"/>
        <circle class="avatar-head" cx="100" cy="55" r="35"/>
        <ellipse class="avatar-head" cx="100" cy="130" rx="50" ry="45"/>
    </svg>'''


def _generate_gradient(data):
    """SVG con gradiente vibrante"""
    colors = data.get('gradient', '#7cb342,#9ccc65').split(',')
    gradient_id = data.get('id', 'grad')
    return f'''<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="{gradient_id}" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:{colors[0]};stop-opacity:1" />
                <stop offset="100%" style="stop-color:{colors[1]};stop-opacity:1" />
            </linearGradient>
        </defs>
        <rect fill="url(#{gradient_id})" width="200" height="200" rx="100"/>
        <circle fill="rgba(255,255,255,0.2)" cx="100" cy="70" r="40"/>
        <ellipse fill="rgba(255,255,255,0.15)" cx="100" cy="140" rx="50" ry="45"/>
        <circle fill="white" opacity="0.8" cx="100" cy="65" r="32"/>
        <ellipse fill="white" opacity="0.8" cx="100" cy="135" rx="45" ry="40"/>
    </svg>'''


def _generate_initials(data):
    """SVG con patrón decorativo"""
    color = data.get('color', '#1b5e20')
    pattern = data.get('pattern', 'dots')
    return f'''<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <style>
                .bg {{ fill: {color}; }}
                .pattern {{ fill: rgba(255,255,255,0.1); }}
                .accent {{ fill: white; opacity: 0.9; }}
            </style>
        </defs>
        <rect class="bg" width="200" height="200" rx="100"/>
        <circle class="accent" cx="100" cy="70" r="38"/>
        <ellipse class="accent" cx="100" cy="145" rx="48" ry="43"/>
        <g class="pattern">
            {''.join([f'<circle cx="{30 + i*20}" cy="{25 + j*20}" r="2"/>' 
                     for i in range(9) for j in range(9) if (i+j) % 3 == 0])}
        </g>
    </svg>'''


def _generate_gaming(data):
    """SVG estilo pixel art / gaming"""
    desc = data.get('desc', 'Knight')
    color = data.get('color', '#c0392b')
    return f'''<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <style>
                .pixel-bg {{ fill: {color}; }}
                .pixel-light {{ fill: rgba(255,255,255,0.3); }}
                .pixel-dark {{ fill: rgba(0,0,0,0.2); }}
            </style>
        </defs>
        <rect class="pixel-bg" width="200" height="200" rx="20"/>
        <rect class="pixel-light" x="50" y="40" width="100" height="50" rx="8"/>
        <rect class="pixel-light" x="60" y="80" width="30" height="80" rx="4"/>
        <rect class="pixel-light" x="110" y="80" width="30" height="80" rx="4"/>
        <circle class="pixel-dark" cx="75" cy="55" r="6"/>
        <circle class="pixel-dark" cx="125" cy="55" r="6"/>
        <path class="pixel-dark" d="M 100 65 Q 95 70 100 75 Q 105 70 100 65" fill="currentColor"/>
        <text x="100" y="165" font-size="16" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-weight="bold">{desc[:3]}</text>
    </svg>'''


def _generate_minimal(data):
    """SVG minimalista con símbolos geométricos"""
    symbol = data.get('symbol', '●')
    color = data.get('color', '#7cb342')
    return f'''<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <style>
                .minimal-bg {{ fill: {color}; opacity: 0.15; }}
                .minimal-symbol {{ font-size: 80px; fill: {color}; text-anchor: middle; dominant-baseline: middle; font-weight: bold; }}
                .minimal-accent {{ fill: {color}; opacity: 0.3; }}
            </style>
        </defs>
        <rect class="minimal-bg" width="200" height="200" rx="100"/>
        <circle class="minimal-accent" cx="100" cy="100" r="80"/>
        <text class="minimal-symbol" x="100" y="100">{symbol}</text>
        <circle class="minimal-accent" cx="100" cy="100" r="85" fill="none" stroke="{color}" stroke-width="2" opacity="0.5"/>
    </svg>'''


def get_user_avatar_url(user, avatar_type='foto_perfil'):
    """
    Obtiene la URL del avatar del usuario (foto o predefinido)
    """
    if hasattr(user, 'foto_perfil') and user.foto_perfil:
        return f'/{user.foto_perfil}'
    
    # Si no tiene foto, usar avatar predefinido
    if hasattr(user, 'avatar_style') and user.avatar_style:
        return f'/api/avatar/{user.usuario}?style={user.avatar_style}'
    
    # Por defecto, silueta verde
    return f'/api/avatar/{user.usuario}?style=siluetas'
