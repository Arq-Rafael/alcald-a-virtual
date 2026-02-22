from flask import Blueprint, render_template, session, redirect, url_for, current_app, request, flash, jsonify
from app.utils import can_access, normalize_features
import json
import os
import csv as csv_mod

main_bp = Blueprint('main', __name__)

@main_bp.before_app_request
def load_features():
    # Load features from config.json (if present) to override defaults
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

@main_bp.route('/api/dashboard-stats')
def dashboard_stats():
    if not session.get('user'):
        return jsonify({'error': 'unauthorized'}), 401

    stats = {}

    # Solicitudes (CSV)
    if can_access('solicitudes'):
        try:
            path = current_app.config.get('SOLICITUDES_PATH', '')
            total, pendientes = 0, 0
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    for row in csv_mod.reader(f):
                        if row:
                            total += 1
                            if len(row) > 11 and row[11].strip().lower() == 'nuevo':
                                pendientes += 1
            stats['solicitudes'] = {'total': total, 'pendientes': pendientes}
        except Exception as e:
            print(f"Stats error (solicitudes): {e}")

    # PQRS / Participación
    if can_access('participacion'):
        try:
            from app.models.participacion import Radicado
            stats['pqrs'] = {
                'pendiente': Radicado.query.filter_by(estado='PENDIENTE').count(),
                'en_tramite': Radicado.query.filter_by(estado='EN_TRAMITE').count(),
                'total':      Radicado.query.count(),
            }
        except Exception as e:
            print(f"Stats error (pqrs): {e}")

    # Contratos
    if can_access('contratos'):
        try:
            from app.models.contrato import Contrato
            stats['contratos'] = {
                'total': Contrato.query.count(),
                'alerta': Contrato.query.filter_by(alerta_vencimiento=True).count(),
            }
        except Exception as e:
            print(f"Stats error (contratos): {e}")

    # Gestión del Riesgo (Arbórea)
    if can_access('riesgo'):
        try:
            from app.models.riesgo_arborea import RadicadoArborea
            stats['riesgo'] = {
                'total':      RadicadoArborea.query.count(),
                'pendientes': RadicadoArborea.query.filter(
                                  RadicadoArborea.dictamen_decision.is_(None)
                              ).count(),
            }
        except Exception as e:
            print(f"Stats error (riesgo): {e}")

    # Admin: usuarios del sistema
    if session.get('user_role') in ('admin', 'superadmin'):
        try:
            from app.models.usuario import Usuario
            stats['usuarios'] = {
                'total':   Usuario.query.count(),
                'activos': Usuario.query.filter_by(bloqueado=False).count(),
            }
        except Exception as e:
            print(f"Stats error (usuarios): {e}")

    return jsonify(stats)

@main_bp.route('/geoportal')
def geoportal():
    """Catastro Municipal 3D Profesional - Vista unificada estilo Google Maps"""
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    if not can_access('geoportal'):
        flash('No tienes permisos para acceder a este módulo', 'error')
        return redirect(url_for('main.dashboard'))
    return render_template('catastro_3d.html')

@main_bp.route('/gestion-riesgo')
@main_bp.route('/gestion-ambiental')  # Alias para compatibilidad
def gestion_riesgo():
    """Módulo de Gestión del Riesgo (Gestión Arbórea + Actas CMGR + Planes de Contingencia)"""
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    if not can_access('riesgo'):
        flash('No tienes permisos para acceder a este módulo', 'error')
        return redirect(url_for('main.dashboard'))
    return render_template('gestion_riesgo.html')

@main_bp.route('/riesgo/gestion-arborea')
def riesgo_gestion_arborea():
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    if not can_access('riesgo'):
        flash('No tienes permisos para acceder a este módulo', 'error')
        return redirect(url_for('main.dashboard'))
    return render_template('riesgo_gestion_arborea_v2.html', user=session.get('user'))

@main_bp.route('/riesgo/actas-cmgr')
def riesgo_actas_cmgr():
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    if not can_access('riesgo'):
        flash('No tienes permisos para acceder a este módulo', 'error')
        return redirect(url_for('main.dashboard'))
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
