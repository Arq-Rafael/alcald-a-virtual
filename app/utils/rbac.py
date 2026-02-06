"""
Role-Based Access Control (RBAC) System
Gestiona permisos por secretaría/departamento y roles
"""

from functools import wraps
from flask import session, abort, redirect, url_for, current_app
import logging

# Mapeo de permisos por secretaría/departamento
# Cada secretaría tiene acceso a ciertos módulos
SECRETARIA_PERMISSIONS = {
    'planeacion': {
        'redactar',           # Redactar oficios
        'solicitudes',        # Gestión de solicitudes
        'calendario',         # Calendario
        'participacion',      # Participación ciudadana
        'geoportal',          # Geoportal/SIG
        'seguimiento',        # Seguimiento de metas
        'riesgo',             # Gestión del riesgo
        'contratos',          # Contratación
        'certificados'        # Certificados (lectura)
        # NO tiene: 'configuracion' (solo admin)
    },
    
    'gobierno': {
        'redactar',           # Redactar oficios
        'solicitudes',        # Gestión de solicitudes
        'calendario',         # Calendario
        'participacion',      # Participación ciudadana
        'riesgo',             # Gestión del riesgo
        'contratos',          # Contratación
        # NO tiene: geoportal, seguimiento, certificados, configuracion
    },
    
    'hacienda': {
        'redactar',           # Redactar oficios
        'solicitudes',        # Gestión de solicitudes
        'calendario',         # Calendario
        # NO tiene: participacion, geoportal, seguimiento, riesgo, contratos, certificados, configuracion
    },
    
    'desarrollo_rural': {
        'redactar',           # Redactar oficios
        'solicitudes',        # Gestión de solicitudes
        'calendario',         # Calendario
        'riesgo',             # Gestión del riesgo
        # NO tiene: participacion, geoportal, seguimiento, contratos, certificados, configuracion
    },
    
    'desarrollo_social': {
        'redactar',           # Redactar oficios
        'solicitudes',        # Gestión de solicitudes
        'calendario',         # Calendario
        'riesgo',             # Gestión del riesgo
        # NO tiene: participacion, geoportal, seguimiento, contratos, certificados, configuracion
    },
    
    'user': {
        # Usuarios normales sin departamento específico - acceso mínimo
        # Se puede extender según necesidades
    }
}

# Mapeo de módulos a módulos internos para simplificar validación
MODULES_ALIAS = {
    'redactar': ['redactar_oficios', 'oficios'],
    'solicitudes': ['solicitudes', 'gestionar_solicitudes'],
    'calendario': ['calendario', 'events'],
    'participacion': ['participacion', 'radicados'],
    'geoportal': ['geoportal', 'usos', 'catastro'],
    'seguimiento': ['seguimiento', 'metas', 'informes'],
    'riesgo': ['riesgo', 'contingencia', 'planes_contingencia'],
    'contratos': ['contratos', 'contratacion'],
    'certificados': ['certificados'],
    'ia': ['ia', 'inteligencia_artificial'],
    'configuracion': ['configuracion', 'admin_config'],
}

def get_user_secretaria():
    """Obtiene la secretaría del usuario en sesión"""
    from app.models.usuario import Usuario
    
    if 'user' not in session:
        return None
    
    try:
        user = Usuario.query.filter_by(usuario=session['user']).first()
        if user:
            return user.secretaria or None
    except Exception as e:
        logging.error(f"Error getting user secretaria: {e}")
    
    return None

def get_user_role():
    """Obtiene el rol del usuario en sesión"""
    from app.models.usuario import Usuario
    
    if 'user' not in session:
        return None
    
    try:
        user = Usuario.query.filter_by(usuario=session['user']).first()
        if user:
            return user.role or 'user'
    except Exception as e:
        logging.error(f"Error getting user role: {e}")
    
    return None

def has_permission(module_name):
    """
    Verifica si el usuario actual tiene permiso para acceder a un módulo
    
    Args:
        module_name (str): Nombre del módulo a verificar
    
    Returns:
        bool: True si tiene permiso, False en caso contrario
    """
    role = get_user_role()
    secretaria = get_user_secretaria()
    
    # Admin y superadmin tienen acceso a todo excepto...
    # En realidad, solo admin tiene acceso a configuracion
    if role in ['admin', 'superadmin']:
        return True
    
    # Si no hay secretaría, no tiene permisos especiales (excepto usuarios con rol específico)
    if not secretaria:
        return False
    
    # Normalizar nombre de secretaría a minúsculas y reemplazar espacios
    secretaria_key = secretaria.lower().replace(' ', '_').strip()
    
    # Obtener permisos de la secretaría
    if secretaria_key not in SECRETARIA_PERMISSIONS:
        return False
    
    permissions = SECRETARIA_PERMISSIONS[secretaria_key]
    
    # Normalizar nombre de módulo
    module_key = module_name.lower().replace(' ', '_').strip()
    
    # Buscar en permisos directos
    if module_key in permissions:
        return True
    
    # Buscar en alias de módulos
    for main_module, aliases in MODULES_ALIAS.items():
        if module_key in aliases and main_module in permissions:
            return True
    
    return False

def require_permission(module_name, abort_code=403):
    """
    Decorador para proteger rutas basado en permisos
    
    Uso:
        @app.route('/mi-ruta')
        @require_permission('calendario')
        def mi_ruta():
            pass
    
    Args:
        module_name (str): Nombre del módulo requerido
        abort_code (int): Código HTTP a retornar si no tiene permiso (default 403)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return redirect(url_for('auth.login'))
            
            if not has_permission(module_name):
                logging.warning(f"User {session.get('user')} denied access to module: {module_name}")
                abort(abort_code)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_accessible_modules():
    """
    Retorna lista de módulos a los que el usuario actual tiene acceso
    
    Returns:
        list: Lista de módulos accesibles
    """
    role = get_user_role()
    secretaria = get_user_secretaria()
    
    modules = []
    
    # Admin tiene acceso a todo
    if role in ['admin', 'superadmin']:
        return [
            'redactar', 'solicitudes', 'calendario', 'participacion',
            'geoportal', 'seguimiento', 'riesgo', 'contratos',
            'certificados', 'ia', 'configuracion'
        ]
    
    # Usuarios sin secretaría no tienen acceso especial
    if secretaria:
        secretaria_key = secretaria.lower().replace(' ', '_').strip()
        if secretaria_key in SECRETARIA_PERMISSIONS:
            modules = list(SECRETARIA_PERMISSIONS[secretaria_key])
    
    return modules

def get_all_modules():
    """Retorna lista de todos los módulos disponibles"""
    return [
        'redactar', 'solicitudes', 'calendario', 'participacion',
        'geoportal', 'seguimiento', 'riesgo', 'contratos',
        'certificados', 'ia', 'configuracion'
    ]

def filter_modules_by_permission(modules_list):
    """
    Filtra una lista de módulos dejando solo los que el usuario puede acceder
    
    Args:
        modules_list (list): Lista de módulos a filtrar
    
    Returns:
        list: Módulos filtrados
    """
    return [m for m in modules_list if has_permission(m)]
