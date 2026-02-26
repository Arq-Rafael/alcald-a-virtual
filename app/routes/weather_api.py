"""
Rutas del módulo Clima Supatá.
- GET  /clima              — Página completa del módulo
- GET  /api/weather/current   — Datos actuales (JSON)
- GET  /api/weather/forecast  — Pronóstico 24h + 7 días (JSON)
- GET  /api/weather/alerts    — Alertas y recursos IDEAM (JSON)
"""

from flask import Blueprint, jsonify, render_template, session, redirect, url_for
from app.services import weather_service as ws

weather_bp = Blueprint('weather', __name__)


# ── Página del módulo ─────────────────────────────────────────────────────────

@weather_bp.route('/clima')
def clima():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return render_template('clima.html')


# ── API: datos actuales ───────────────────────────────────────────────────────

@weather_bp.route('/api/weather/current')
def api_current():
    data = ws.get_current()
    if data is None:
        return jsonify({'error': 'No hay datos disponibles en este momento'}), 503
    return jsonify(data)


# ── API: pronóstico ───────────────────────────────────────────────────────────

@weather_bp.route('/api/weather/forecast')
def api_forecast():
    data = ws.get_forecast()
    if data is None:
        return jsonify({'error': 'No hay pronóstico disponible en este momento'}), 503
    return jsonify(data)


# ── API: alertas ──────────────────────────────────────────────────────────────

@weather_bp.route('/api/weather/alerts')
def api_alerts():
    """
    Retorna alertas meteorológicas generadas a partir de los datos actuales
    y enlaces a recursos oficiales del IDEAM.
    No depende de ningún RSS externo que pueda fallar.
    """
    current = ws.get_current()
    recs = ws.get_recommendations(current) if current else []

    # Recursos oficiales IDEAM
    resources = [
        {
            'title': 'Boletín Climatológico IDEAM',
            'desc':  'Actualizaciones diarias del estado del clima en Colombia',
            'url':   'http://www.ideam.gov.co/web/tiempo-y-clima/clima',
            'icon':  'bi-newspaper',
        },
        {
            'title': 'Alertas Tempranas IDEAM',
            'desc':  'Sistema de alertas tempranas por eventos hidrometeorológicos',
            'url':   'http://www.ideam.gov.co/web/tiempo-y-clima/alertas-meteorologicas',
            'icon':  'bi-exclamation-triangle-fill',
        },
        {
            'title': 'Pronóstico Departamental Cundinamarca',
            'desc':  'Pronóstico detallado para el departamento de Cundinamarca',
            'url':   'http://www.ideam.gov.co/web/tiempo-y-clima/pronostico-del-tiempo/-/document_library_display/yKhSNLH00XbJ/view/5765',
            'icon':  'bi-map-fill',
        },
        {
            'title': 'UNGRD — Gestión del Riesgo',
            'desc':  'Alertas nacionales de gestión del riesgo de desastres',
            'url':   'https://portal.gestiondelriesgo.gov.co/',
            'icon':  'bi-shield-exclamation',
        },
    ]

    return jsonify({
        'recommendations': recs,
        'resources':       resources,
        'current_summary': {
            'temp':        current.get('temp') if current else None,
            'description': current.get('description') if current else None,
            'icon':        current.get('icon') if current else None,
        }
    })
