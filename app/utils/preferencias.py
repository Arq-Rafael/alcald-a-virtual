"""
Sistema de Preferencias de Interfaz
Gestiona temas, fuentes y colores dinámicos por usuario
"""

def get_user_preferences(session):
    """
    Obtiene las preferencias del usuario desde la sesión y BD
    """
    from flask import current_app
    from app import db
    from app.models.usuario import Usuario
    
    default_prefs = {
        'tema': 'light',
        'tamano_fuente': 'medium',
        'tipo_fuente': 'system',
        'idioma': 'es',
        'notificaciones': True,
        'sidebar_colapsado': False
    }
    
    if 'user' not in session:
        return default_prefs
    
    try:
        user = Usuario.query.filter_by(usuario=session['user']).first()
        if user:
            prefs = user.get_preferencias()
            return {**default_prefs, **prefs}
    except:
        pass
    
    return default_prefs


def get_theme_css(tema):
    """
    Retorna las variables CSS para el tema seleccionado
    """
    temas = {
        'light': {
            '--bg-primary': '#ffffff',
            '--bg-secondary': '#f9fafb',
            '--text-primary': '#1f2937',
            '--text-secondary': '#6b7280',
            '--border-color': '#e5e7eb',
            '--button-hover': '#f3f4f6',
            '--accent': '#7cb342',
        },
        'dark': {
            '--bg-primary': '#1f2937',
            '--bg-secondary': '#111827',
            '--text-primary': '#f9fafb',
            '--text-secondary': '#d1d5db',
            '--border-color': '#374151',
            '--button-hover': '#374151',
            '--accent': '#9dcc65',
        }
    }
    
    return temas.get(tema, temas['light'])


def get_font_size_css(tamano):
    """
    Retorna las variables CSS para el tamaño de fuente
    """
    tamaños = {
        'small': {
            '--font-size-base': '12px',
            '--font-size-h1': '24px',
            '--font-size-h2': '20px',
            '--font-size-h3': '18px',
            '--font-size-h4': '16px',
            '--font-size-h5': '14px',
            '--line-height': '1.4',
        },
        'medium': {
            '--font-size-base': '14px',
            '--font-size-h1': '28px',
            '--font-size-h2': '24px',
            '--font-size-h3': '20px',
            '--font-size-h4': '18px',
            '--font-size-h5': '16px',
            '--line-height': '1.6',
        },
        'large': {
            '--font-size-base': '16px',
            '--font-size-h1': '32px',
            '--font-size-h2': '28px',
            '--font-size-h3': '24px',
            '--font-size-h4': '20px',
            '--font-size-h5': '18px',
            '--line-height': '1.8',
        },
        'extra-large': {
            '--font-size-base': '18px',
            '--font-size-h1': '36px',
            '--font-size-h2': '32px',
            '--font-size-h3': '28px',
            '--font-size-h4': '24px',
            '--font-size-h5': '20px',
            '--line-height': '2.0',
        }
    }
    
    return tamaños.get(tamano, tamaños['medium'])


def get_font_family_css(tipo):
    """
    Retorna la familia de fuentes
    """
    fuentes = {
        'system': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        'arial': 'Arial, Helvetica, sans-serif',
        'roboto': '"Roboto", sans-serif',
        'opensans': '"Open Sans", sans-serif'
    }
    
    return fuentes.get(tipo, fuentes['system'])


def generate_preference_css(preferences):
    """
    Genera CSS dinámico basado en preferencias del usuario
    """
    tema_css = get_theme_css(preferences.get('tema', 'light'))
    tamano_css = get_font_size_css(preferences.get('tamano_fuente', 'medium'))
    fuente = get_font_family_css(preferences.get('tipo_fuente', 'system'))
    
    css = ':root {\n'
    
    # Variables de tema
    for key, value in tema_css.items():
        css += f'    {key}: {value};\n'
    
    # Variables de tamaño
    for key, value in tamano_css.items():
        css += f'    {key}: {value};\n'
    
    css += f'    --font-family: {fuente};\n'
    css += '}\n\n'
    
    # Aplicar fuente global
    css += '''body {
    font-family: var(--font-family);
    font-size: var(--font-size-base);
    line-height: var(--line-height);
    color: var(--text-primary);
    background-color: var(--bg-primary);
    transition: background-color 0.3s ease, color 0.3s ease;
}

h1 { font-size: var(--font-size-h1); font-weight: 600; }
h2 { font-size: var(--font-size-h2); font-weight: 600; }
h3 { font-size: var(--font-size-h3); font-weight: 600; }
h4 { font-size: var(--font-size-h4); font-weight: 600; }
h5 { font-size: var(--font-size-h5); font-weight: 600; }
h6 { font-size: var(--font-size-base); font-weight: 600; }

a {
    color: var(--accent);
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

.text-primary { color: var(--text-primary); }
.text-secondary { color: var(--text-secondary); }
.bg-primary { background-color: var(--bg-primary); }
.bg-secondary { background-color: var(--bg-secondary); }

.form-control {
    background-color: var(--bg-primary);
    color: var(--text-primary);
    border-color: var(--border-color);
}

.btn-primary {
    background-color: var(--accent);
    border-color: var(--accent);
}

.btn-primary:hover {
    background-color: #689f38;
    border-color: #689f38;
}

.card {
    background-color: var(--bg-primary);
    border-color: var(--border-color);
    color: var(--text-primary);
}

.table {
    color: var(--text-primary);
    border-color: var(--border-color);
}

.table thead {
    background-color: var(--bg-secondary);
    color: var(--text-primary);
}

.modal-content {
    background-color: var(--bg-primary);
    color: var(--text-primary);
    border-color: var(--border-color);
}

.navbar {
    background-color: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
}

.sidebar {
    background-color: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
}
'''
    
    return css
