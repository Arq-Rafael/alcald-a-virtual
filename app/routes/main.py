from flask import Blueprint, render_template, session, redirect, url_for, current_app, request, flash, jsonify, Response
from app.utils import can_access, normalize_features, is_admin, current_session_user, current_session_secretaria, can_risk_submodule
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

_MODULE_CATALOG = {
    'solicitudes':   {'name': 'Solicitudes',         'url': '/solicitudes',        'icon': 'bi-file-earmark-text-fill', 'accent': 'blue',   'perm': 'solicitudes',        'desc': 'Solicitudes de contratación'},
    'certificados':  {'name': 'Certificados',         'url': '/certificados',       'icon': 'bi-patch-check-fill',       'accent': 'emerald','perm': 'certificados',       'desc': 'Certificados municipales'},
    'licencias':     {'name': 'Licencias',            'url': '/licencias',          'icon': 'bi-buildings-fill',         'accent': 'orange', 'perm': 'licencias',          'desc': 'Licencias urbanísticas'},
    'ia':            {'name': 'IA Municipal',         'url': '/ia',                 'icon': 'bi-cpu-fill',               'accent': 'violet', 'perm': 'ia',                 'desc': 'Asistente de inteligencia artificial'},
    'ia_redactar':   {'name': 'Redactar con IA',      'url': '/ia/redactar',        'icon': 'bi-pencil-square',          'accent': 'amber',  'perm': 'ia',                 'desc': 'Genera documentos institucionales'},
    'participacion': {'name': 'Participación',        'url': '/participacion',      'icon': 'bi-people-fill',            'accent': 'rose',   'perm': 'participacion',      'desc': 'Participación ciudadana'},
    'geoportal':     {'name': 'Geoportal',            'url': '/geoportal',          'icon': 'bi-globe-americas',         'accent': 'teal',   'perm': 'geoportal',          'desc': 'Mapa catastral y uso del suelo'},
    'seguimiento':   {'name': 'Seguimiento',          'url': '/seguimiento/metas',  'icon': 'bi-graph-up-arrow',         'accent': 'indigo', 'perm': 'seguimiento',        'desc': 'Plan de Desarrollo'},
    'riesgo':        {'name': 'Gestión Riesgo',       'url': '/gestion-riesgo',     'icon': 'bi-shield-fill-exclamation','accent': 'green',  'perm': 'riesgo',             'desc': 'Gestión del riesgo y arboleda'},
    'contratos':     {'name': 'Contratación',         'url': '/contratos',          'icon': 'bi-briefcase-fill',         'accent': 'sky',    'perm': 'contratos',          'desc': 'Contratos y convenios'},
    'correo':        {'name': 'Correo Inteligente',   'url': '/correo-inteligente', 'icon': 'bi-envelope-fill',          'accent': 'blue',   'perm': 'correo_inteligente', 'desc': 'Bandeja de correo institucional'},
    'calendario':    {'name': 'Agenda Institucional', 'url': '/calendario',         'icon': 'bi-calendar-event-fill',   'accent': 'sky',    'perm': None,                 'desc': 'Eventos y programación del municipio'},
    'reportes':      {'name': 'Reportes',             'url': '/reportes',           'icon': 'bi-bar-chart-fill',         'accent': 'indigo', 'perm': 'reportes',           'desc': 'Informes y estadísticas'},
}

@main_bp.route('/dashboard')
def dashboard():
    if not session.get('user'):
        return redirect(url_for('auth.login'))

    featured_cards = []
    try:
        from app.models.usuario import Usuario
        user = Usuario.query.filter_by(usuario=session['user']).first()
        if user:
            prefs = user.get_preferencias()
            featured_ids = prefs.get('featured_modules', [])
            for mid in featured_ids[:4]:
                mod = _MODULE_CATALOG.get(mid)
                if not mod:
                    continue
                perm = mod.get('perm')
                if perm is None or can_access(perm):
                    featured_cards.append({'id': mid, **mod})
    except Exception:
        pass

    return render_template('dashboard.html',
                           featured_cards=featured_cards,
                           module_catalog=_MODULE_CATALOG)

@main_bp.route('/api/dashboard-stats')
def dashboard_stats():
    if not session.get('user'):
        return jsonify({'error': 'unauthorized'}), 401

    stats = {}
    _admin   = is_admin()
    _user    = current_session_user()
    _secr    = current_session_secretaria()

    # Solicitudes (CSV) — admin ve todo; otros solo los de su secretaría
    if can_access('solicitudes'):
        try:
            path = current_app.config.get('SOLICITUDES_PATH', '')
            total, pendientes = 0, 0
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    reader = csv_mod.reader(f)
                    for row in reader:
                        if not row:
                            continue
                        if not _admin:
                            # columna 1 → secretaría (ajustar índice si cambia el CSV)
                            row_secr = row[1].strip() if len(row) > 1 else ''
                            row_user = row[0].strip() if row else ''
                            if row_secr != _secr and row_user != _user:
                                continue
                        total += 1
                        if len(row) > 11 and row[11].strip().lower() == 'nuevo':
                            pendientes += 1
            stats['solicitudes'] = {'total': total, 'pendientes': pendientes}
        except Exception as e:
            print(f"Stats error (solicitudes): {e}")

    # PQRS / Participación — admin ve todo; otros solo los suyos
    if can_access('participacion'):
        try:
            from app.models.participacion import Radicado
            base_q = Radicado.query if _admin else Radicado.query.filter_by(creado_por=_user)
            stats['pqrs'] = {
                'pendiente': base_q.filter_by(estado='PENDIENTE').count(),
                'en_tramite': base_q.filter_by(estado='EN_TRAMITE').count(),
                'total':      base_q.count(),
            }
        except Exception as e:
            print(f"Stats error (pqrs): {e}")

    # Contratos — admin ve todo; otros solo los de su secretaría
    if can_access('contratos'):
        try:
            from app.models.contrato import Contrato
            base_q = Contrato.query if _admin else Contrato.query.filter_by(dependencia=_secr)
            stats['contratos'] = {
                'total': base_q.count(),
                'alerta': base_q.filter_by(alerta_vencimiento=True).count(),
            }
        except Exception as e:
            print(f"Stats error (contratos): {e}")

    # Gestión del Riesgo (Arbórea) — admin ve todo; otros solo los suyos
    if can_access('riesgo'):
        try:
            from app.models.riesgo_arborea import RadicadoArborea
            base_q = RadicadoArborea.query if _admin else RadicadoArborea.query.filter_by(usuario_creador=_user)
            stats['riesgo'] = {
                'total':      base_q.count(),
                'pendientes': base_q.filter(
                                  RadicadoArborea.dictamen_decision.is_(None)
                              ).count(),
            }
        except Exception as e:
            print(f"Stats error (riesgo): {e}")

    # Admin: usuarios del sistema (solo admin/superadmin)
    if _admin:
        try:
            from app.models.usuario import Usuario
            stats['usuarios'] = {
                'total':   Usuario.query.count(),
                'activos': Usuario.query.filter_by(bloqueado=False).count(),
            }
        except Exception as e:
            print(f"Stats error (usuarios): {e}")

    return jsonify(stats)

@main_bp.route('/politica-privacidad')
def politica_privacidad():
    """Página pública — no requiere sesión activa."""
    return render_template('politica_privacidad.html')

def _serve_raw_html(filename):
    """Sirve un HTML directamente sin procesamiento Jinja2."""
    path = os.path.join(current_app.root_path, '..', 'templates', filename)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return Response(content, mimetype='text/html')

@main_bp.route('/geoportal')
def geoportal():
    """Pantalla de inicio del Geoportal EOT Supatá"""
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    if not can_access('geoportal'):
        flash('No tienes permisos para acceder a este módulo', 'error')
        return redirect(url_for('main.dashboard'))
    return _serve_raw_html('geoportal_inicio.html')

@main_bp.route('/geoportal/mapa')
def geoportal_mapa():
    """Geoportal EOT Supatá V8 — Visor cartográfico completo"""
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    if not can_access('geoportal'):
        flash('No tienes permisos para acceder a este módulo', 'error')
        return redirect(url_for('main.dashboard'))
    return _serve_raw_html('geoportal_mapa.html')

@main_bp.route('/geoportal/usos-del-suelo')
def geoportal_usos():
    """Generador de Certificado de Uso del Suelo — EOT Supatá V8"""
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    if not can_access('geoportal'):
        flash('No tienes permisos para acceder a este módulo', 'error')
        return redirect(url_for('main.dashboard'))
    return _serve_raw_html('geoportal_usos.html')

@main_bp.route('/geoportal/data/<path:filename>')
def geoportal_data(filename):
    """Sirve archivos de datos del geoportal (GeoJSON, JS) protegidos por sesión."""
    if not session.get('user'):
        return '', 401
    from flask import send_from_directory
    data_dir = os.path.join(current_app.root_path, '..', 'static', 'geoportal', 'data')
    return send_from_directory(data_dir, filename)

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
    if not can_risk_submodule('arborea'):
        flash('No tienes permisos para acceder a Gestión Arbórea. Contacta al administrador.', 'danger')
        return redirect(url_for('main.gestion_riesgo'))
    return render_template('riesgo_gestion_arborea_v2.html', user=session.get('user'))

@main_bp.route('/riesgo/actas-cmgr')
def riesgo_actas_cmgr():
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    if not can_access('riesgo'):
        flash('No tienes permisos para acceder a este módulo', 'error')
        return redirect(url_for('main.dashboard'))
    if not can_risk_submodule('actas'):
        flash('No tienes permisos para acceder a Actas CMGR. Contacta al administrador.', 'danger')
        return redirect(url_for('main.gestion_riesgo'))
    return render_template('riesgo_actas_cmgr.html')

@main_bp.route('/riesgo/planes-contingencia')
def riesgo_planes_contingencia():
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    if not can_risk_submodule('planes'):
        flash('No tienes permisos para acceder a Planes de Contingencia. Contacta al administrador.', 'danger')
        return redirect(url_for('main.gestion_riesgo'))
    return redirect(url_for('contingencia.listar_planes'))

# ── Helpers para servir los HTMLs standalone de Gestión del Riesgo ───────────

def _riesgo_html_path(*partes):
    """Devuelve la ruta absoluta a un HTML dentro de documentos_generados/GESTION DEL RIESGO/"""
    base = os.path.join(current_app.root_path, '..', 'documentos_generados', 'GESTION DEL RIESGO')
    return os.path.join(base, *partes)

def _serve_riesgo_html(*partes, inject_before_body=''):
    """Lee un HTML standalone, opcionalmente inyecta un <script> antes de </body>, y lo devuelve."""
    path = _riesgo_html_path(*partes)
    try:
        with open(path, encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return f'<p>Archivo no encontrado: {path}</p>', 404
    if inject_before_body:
        content = content.replace('</body>', inject_before_body + '\n</body>', 1)
    return Response(content, mimetype='text/html')

# ── Tala de Árboles ──────────────────────────────────────────────────────────

@main_bp.route('/riesgo/tala')
def riesgo_tala():
    """Hub integrado de Tala de Árboles (Visita Técnica + Aprobación Comité)"""
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    if not can_access('riesgo'):
        flash('Sin permisos para este módulo.', 'danger')
        return redirect(url_for('main.dashboard'))
    return render_template('riesgo_tala_hub.html')

@main_bp.route('/riesgo/tala/visita')
def riesgo_tala_visita():
    """Informe de Visita Técnica Arbórea (HTML standalone)"""
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    if not can_access('riesgo'):
        return redirect(url_for('main.dashboard'))
    # Inyectar bridge: al exportar para Comité, también guarda en localStorage
    bridge = """<script>
(function(){
  var _orig = window.exportarParaComite;
  window.exportarParaComite = function(){
    if(_orig) _orig();
    try {
      var data = _collectFormData();
      data.selectedReg = typeof selectedReg !== 'undefined' ? selectedReg : null;
      localStorage.setItem('tala_visita_data', JSON.stringify(data));
      localStorage.setItem('tala_visita_ts', new Date().toISOString());
      var banner = document.getElementById('_tala_bridge_ok');
      if(!banner){
        banner = document.createElement('div');
        banner.id = '_tala_bridge_ok';
        banner.style.cssText = 'position:fixed;bottom:16px;right:16px;background:#1a5c2e;color:#b8d400;padding:10px 16px;border-radius:8px;font-size:11px;font-family:"IBM Plex Sans",sans-serif;font-weight:700;z-index:99999;box-shadow:0 4px 16px rgba(0,0,0,.4)';
        banner.textContent = '✅ Datos listos para Aprobación del Comité';
        document.body.appendChild(banner);
        setTimeout(function(){ banner.remove(); }, 4000);
      }
    } catch(e){}
  };
})();
</script>"""
    return _serve_riesgo_html('tala', 'visita_arboles.html', inject_before_body=bridge)

@main_bp.route('/riesgo/tala/aprobacion')
def riesgo_tala_aprobacion():
    """Acta de Aprobación del Comité CMGRD (HTML standalone con auto-carga desde Visita)"""
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    if not can_access('riesgo'):
        return redirect(url_for('main.dashboard'))
    # Inyectar auto-carga desde localStorage si hay datos de visita
    bridge = """<script>
(function(){
  document.addEventListener('DOMContentLoaded', function(){
    try {
      var raw = localStorage.getItem('tala_visita_data');
      if(!raw) return;
      var ts = localStorage.getItem('tala_visita_ts') || '';
      var data = JSON.parse(raw);
      var banner = document.createElement('div');
      banner.style.cssText = 'position:fixed;top:0;left:0;right:0;background:#1a3a6a;color:#a8d0f8;padding:10px 20px;font-size:11px;font-family:"IBM Plex Sans",sans-serif;font-weight:600;z-index:99999;display:flex;align-items:center;gap:12px;box-shadow:0 2px 12px rgba(0,0,0,.4)';
      var fecha = ts ? new Date(ts).toLocaleString('es-CO') : 'recientemente';
      banner.innerHTML = '<span>📋 Hay datos de Visita Técnica guardados (' + fecha + '). <b>Radicado: ' + (data.radicado||'—') + '</b></span>' +
        '<button id="_auto_load_btn" style="margin-left:auto;background:#b8d400;color:#0e1e0e;border:none;border-radius:6px;padding:5px 14px;font-weight:700;cursor:pointer;font-size:11px;">Cargar automáticamente</button>' +
        '<button id="_auto_dismiss_btn" style="background:transparent;color:#a8d0f8;border:1px solid #2a4a7a;border-radius:6px;padding:5px 10px;cursor:pointer;font-size:11px;">Ignorar</button>';
      document.body.appendChild(banner);
      document.getElementById('_auto_load_btn').addEventListener('click', function(){
        var mapped = {
          radicado: data.radicado || '',
          fvisita: data.fvisita || '',
          tecnico: data.tecnico || '',
          solicitante: data.solicitante || '',
          sol_id: data.sol_id || '',
          especie: data.especie || '',
          esp_cientifico: data.esp_cientifico || '',
          num_arb: data.num_arb || '1',
          dap: data.dap || '',
          altura: data.altura || '',
          edad: data.edad || '',
          coords: data.coords || '',
          riesgo: data.riesgo || '',
          direccion: data.dir_predio || data.direccion || '',
          codigo_predial: data.codigo_predial || '',
          matricula: data.matricula || '',
          area_terreno: data.area_terreno || '',
          area_construida: data.area_construida || '',
          destino: data.destino_economico || '',
          tipo_predio: data.tipo_predio || '',
          firma_nom: data.firma_nom || '',
          firma_car: data.firma_car || '',
          es_tala: data.es_tala || false,
          es_poda: data.es_poda || false,
          obs_desc: data.obs_desc || '',
          obs_just: data.obs_just || '',
          obs_rec: data.obs_rec || ''
        };
        if(typeof _handleExtractedData === 'function'){
          _handleExtractedData(mapped, 'localStorage');
          if(typeof setStatus === 'function') setStatus('✅ Datos de Visita Técnica cargados automáticamente');
        }
        banner.remove();
      });
      document.getElementById('_auto_dismiss_btn').addEventListener('click', function(){ banner.remove(); });
    } catch(e){}
  });
})();
</script>"""
    return _serve_riesgo_html('tala', 'aprobacion_comite.html', inject_before_body=bridge)

# ── Amenazas ─────────────────────────────────────────────────────────────────

@main_bp.route('/riesgo/amenazas')
def riesgo_amenazas():
    """Certificado de Amenaza (HTML standalone)"""
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    if not can_access('riesgo'):
        flash('Sin permisos para este módulo.', 'danger')
        return redirect(url_for('main.dashboard'))
    return _serve_riesgo_html('AMENAZAS', 'certificado_amenaza_supata_formato_oficial_v2.html')

# ── Plan de Contingencia (HTML standalone) ───────────────────────────────────

@main_bp.route('/riesgo/plan-contingencia')
def riesgo_plan_contingencia():
    """Plan de Contingencia (HTML standalone)"""
    if not session.get('user'):
        return redirect(url_for('auth.login'))
    if not can_access('riesgo'):
        flash('Sin permisos para este módulo.', 'danger')
        return redirect(url_for('main.dashboard'))
    return _serve_riesgo_html('PLANES DE CONTINGENCIA', 'plan_contingencia_v1.html')

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
