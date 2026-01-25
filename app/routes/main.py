from flask import Blueprint, render_template, session, redirect, url_for, current_app, request
from app.utils import can_access, normalize_features
import json
import os

main_bp = Blueprint('main', __name__)

@main_bp.before_app_request
def load_features():
    if not current_app.config.get("APP_FEATURES"):
        # Load features from config.json (or similar) if not already loaded
        # For this refactor, we attempt to read the original config.json
        try:
            config_path = os.path.join(current_app.config['BASE_DIR'], "config.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    current_app.config["APP_FEATURES"] = normalize_features(cfg.get("features"))
        except Exception as e:
            print(f"Error loading features: {e}")

@main_bp.route('/dashboard')
def dashboard():
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html')

@main_bp.route('/geoportal')
def geoportal():
    """Catastro Municipal 3D Profesional - Vista unificada estilo Google Maps"""
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    return render_template('catastro_3d.html')

@main_bp.route('/gestion-riesgo')
@main_bp.route('/gestion-ambiental')  # Alias para compatibilidad
def gestion_riesgo():
    """Módulo de Gestión del Riesgo (Gestión Arbórea + Actas CMGR + Planes de Contingencia)"""
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    return render_template('gestion_riesgo.html')

@main_bp.route('/riesgo/gestion-arborea')
def riesgo_gestion_arborea():
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    return render_template('riesgo_gestion_arborea_v2.html', user=session.get('user'))

@main_bp.route('/riesgo/actas-cmgr')
def riesgo_actas_cmgr():
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    return render_template('riesgo_actas_cmgr.html')

@main_bp.route('/riesgo/planes-contingencia')
def riesgo_planes_contingencia():
    """Redirecciona a la nueva ruta de planes de contingencia V2"""
    return redirect(url_for('contingencia.listar_planes'))

@main_bp.route('/seguimiento-metas')
def seguimiento_metas():
    """Módulo fusionado de Seguimiento y Metas (Seguimiento + Progreso Metas)"""
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    return redirect(url_for('seguimiento.index'))

@main_bp.app_context_processor
def inject_permissions():
    return dict(
        can=can_access,
        features=current_app.config.get("APP_FEATURES", {}),
        user=session.get('user')
    )
