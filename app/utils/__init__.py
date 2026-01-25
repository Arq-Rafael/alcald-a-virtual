"""
Utilidades del sistema Alcaldía Virtual
"""

import unicodedata
import re
import os
import sqlite3
import datetime
from datetime import timedelta
from functools import wraps
from flask import session, current_app, flash, redirect, url_for
import pandas as pd

def _norm(s):
    return str(s or "").strip().lower()

def normalize_features(raw):
    out = {}
    for feat, roles in (raw or {}).items():
        if isinstance(roles, bool):  
            continue
        if isinstance(roles, str):
            roles = [roles]
        out[_norm(feat)] = {_norm(x) for x in roles if x is not None}
    return out

def _session_tokens() -> set:
    tokens = {
        _norm(session.get("user_role")),
        _norm(session.get("user")),
    }
    return {t for t in tokens if t}

def can_access(feature_name: str) -> bool:
    feats = current_app.config.get("APP_FEATURES", {})
    allowed = feats.get(_norm(feature_name), set())  
    tokens = _session_tokens()

    if current_app.config.get("ALWAYS_ADMIN", False) and "admin" in tokens:
        return True

    if {"*", "all", "todos"} & allowed:
        return True

    return bool(tokens & allowed)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tokens = _session_tokens()
        if "admin" not in tokens and not current_app.config.get("ALWAYS_ADMIN", False):
             flash('Acceso denegado: se requiere rol de administrador.', 'danger')
             return redirect(url_for('main.dashboard') if 'main.dashboard' in current_app.view_functions else '/') 
        return f(*args, **kwargs)
    return decorated_function

# --- SQLite Helpers ---
# --- SQLite Helpers ---
def get_sqlite():
    # Detectar entorno Railway para usar /tmp
    db_name = "data.db"
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        db_path = os.path.join('/tmp', db_name)
    else:
        db_path = os.path.join(current_app.root_path, '..', db_name)
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def dias_restantes(fecha_max):
    if not fecha_max: return None
    try:
        f = datetime.datetime.fromisoformat(fecha_max)
    except Exception:
        try: f = datetime.datetime.strptime(fecha_max, "%Y-%m-%d")
        except: return None
    delta = (f.date() - datetime.datetime.now().date()).days
    return delta

def color_semaforo_dias(d):
    if d is None: return 'secondary'
    if d > 10:   return 'success'
    if d >= 0:   return 'warning'
    return 'danger'

def load_plan_desarrollo():
    """Carga y normaliza el Plan de Desarrollo desde Excel (con fallback)."""
    try:
        # Get BASE_DIR from Flask config - this is set in app/config.py
        base_dir = str(current_app.config['BASE_DIR'])
        path = os.path.join(base_dir, 'datos', 'plan_desarrollo', 'plan_desarrollo.xlsx')
        
        if not os.path.exists(path):
            print(f"⚠️ Plan file not found at: {path}. Using fallback data.")
            return _get_fallback_plan()

        df = pd.read_excel(path)
        
        # Rename columns to standard keys if needed
        # Expected keys: 'meta de producto', 'eje', 'sector', 'codigo bpim'
        rename_map = {}
        for col in df.columns:
            str_col = str(col).lower().strip()
            if 'meta' in str_col and 'producto' in str_col:
                rename_map[col] = 'meta de producto'
            elif 'meta' in str_col:
                rename_map[col] = 'meta de producto'
            elif 'bpim' in str_col or 'bpin' in str_col:
                rename_map[col] = 'codigo bpim'
            elif 'eje' in str_col:
                rename_map[col] = 'eje'
            elif 'sector' in str_col:
                rename_map[col] = 'sector'
        
        if rename_map:
            df = df.rename(columns=rename_map)
            
        # Ensure 'meta de producto' exists
        if 'meta de producto' not in df.columns:
            df['meta de producto'] = "Meta desconocida"
            
        # Fill NaNs
        df = df.fillna('')
        
        return df.to_dict('records')
    except Exception as e:
        print(f"Error loading plan desarrollo: {e}. Using fallback data.")
        return _get_fallback_plan()

def _get_fallback_plan():
    """Datos por defecto si falla la carga del Excel"""
    return [
        {
            "eje": "Seguridad y Convivencia",
            "sector": "Justicia y Seguridad",
            "meta de producto": "Implementar estrategia de seguridad integral",
            "codigo bpim": "2024-001"
        },
        {
            "eje": "Infraestructura para el Desarrollo",
            "sector": "Transporte",
            "meta de producto": "Mantenimiento de 50km de vías terciarias",
            "codigo bpim": "2024-002"
        },
        {
            "eje": "Bienestar Social",
            "sector": "Salud",
            "meta de producto": "Cobertura universal de vacunación",
            "codigo bpim": "2024-003"
        },
        {
            "eje": "Desarrollo Económico",
            "sector": "Agricultura",
            "meta de producto": "Asistencia técnica a 200 familias campesinas",
            "codigo bpim": "2024-004"
        },
         {
            "eje": "Educación de Calidad",
            "sector": "Educación",
            "meta de producto": "Mejoramiento de 10 sedes educativas rurales",
            "codigo bpim": "2024-005"
        }
    ]

