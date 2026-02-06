import os
import io
import logging
import pandas as pd
from datetime import datetime

from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, current_app, abort, jsonify
from app.utils.rbac import require_permission
from app import db
from app.models.metas import MetaPlan

logger = logging.getLogger(__name__)
seguimiento_bp = Blueprint('seguimiento', __name__)

_plan_cache = None

def _load_plan_excel():
    """Carga PLAN_DESARROLLO (198 metas) + REGISTRO_AVANCES (datos 2024-2025)"""
    global _plan_cache
    if _plan_cache is not None:
        return _plan_cache

    base_dir = os.path.join(str(current_app.config['BASE_DIR']), 'documentos_generados', 'plan de desarollo')
    file_path = os.path.join(base_dir, 'BASE_RENDICION_PLAN_DESARROLLO_SUPATA.xlsx')
    
    if not os.path.exists(file_path):
        logger.error(f"Excel no encontrado: {file_path}")
        return None

    try:
        excel = pd.ExcelFile(file_path)
        
        # 1. Cargar catálogo de 198 metas (PLAN_DESARROLLO)
        plan_df = pd.read_excel(file_path, sheet_name='PLAN_DESARROLLO')
        logger.info(f"✓ Cargadas {len(plan_df)} metas del Plan de Desarrollo")
        
        # 2. Cargar avances por año (REGISTRO_AVANCES - 324 registros)
        avances = pd.read_excel(file_path, sheet_name='REGISTRO_AVANCES')
        logger.info(f"✓ Cargados {len(avances)} registros de avances")
        
        # 3. Preparar datos por año
        metas_por_ano = []
        for _, row in avances.iterrows():
            metas_por_ano.append({
                'id_meta': str(row['ID_META']),
                'bpim': str(row['BPIM']),
                'eje': str(row['EJE']),
                'sector': str(row['SECTOR']),
                'meta_producto': str(row['META_PRODUCTO']),
                'ano': int(row['AÑO']) if pd.notna(row['AÑO']) else None,
                'secretaria': str(row['SECRETARIA']) if pd.notna(row['SECRETARIA']) else None,
                'estado': str(row['ESTADO']) if pd.notna(row['ESTADO']) else 'No iniciada',
                'meta_programada': float(row['META_PROGRAMADA_AÑO']) if pd.notna(row['META_PROGRAMADA_AÑO']) else 0,
                'avance_ejecutado': float(row['AVANCE_EJECUTADO_AÑO']) if pd.notna(row['AVANCE_EJECUTADO_AÑO']) else 0,
                'avance_fisico_pct': float(row['%_AVANCE_FISICO']) if pd.notna(row['%_AVANCE_FISICO']) else 0,
                'presupuesto_asig': float(row['PRESUPUESTO_ASIGNADO']) if pd.notna(row['PRESUPUESTO_ASIGNADO']) else 0,
                'presupuesto_ejec': float(row['PRESUPUESTO_EJECUTADO']) if pd.notna(row['PRESUPUESTO_EJECUTADO']) else 0,
                'ejec_fin_pct': float(row['%_EJEC_FINANCIERA']) if pd.notna(row['%_EJEC_FINANCIERA']) else 0,
                'proyecto': str(row['PROYECTO_ASOCIADO']) if pd.notna(row['PROYECTO_ASOCIADO']) else None,
                'fuente': str(row['FUENTE_FINANCIACION']) if pd.notna(row['FUENTE_FINANCIACION']) else None,
            })
        
        # 4. Consolidado: 1 registro por meta (año más reciente)
        metas_consolidado = []
        for meta_id in plan_df['ID_META'].unique():
            registros_meta = [m for m in metas_por_ano if m['id_meta'] == meta_id]
            
            if registros_meta:
                # Usar el registro del año más reciente (2025 si existe, sino 2024)
                reg_reciente = sorted(registros_meta, key=lambda x: x['ano'] or 0, reverse=True)[0]
                metas_consolidado.append({
                    **reg_reciente,
                    'ano': f"CONSOLIDADO ({reg_reciente['ano']})",
                    'anos_disponibles': [r['ano'] for r in registros_meta if r['ano']]
                })
            else:
                # Meta sin avances registrados
                meta_info = plan_df[plan_df['ID_META'] == meta_id].iloc[0]
                metas_consolidado.append({
                    'id_meta': str(meta_info['ID_META']),
                    'bpim': str(meta_info['BPIM']),
                    'eje': str(meta_info['EJE']),
                    'sector': str(meta_info['SECTOR']),
                    'meta_producto': str(meta_info['META_PRODUCTO']),
                    'ano': 'CONSOLIDADO (Sin datos)',
                    'estado': 'No iniciada',
                    'avance_fisico_pct': 0,
                    'ejec_fin_pct': 0,
                    'presupuesto_asig': 0,
                    'presupuesto_ejec': 0,
                    'meta_programada': 0,
                    'avance_ejecutado': 0,
                })
        
        # 5. Calcular KPIs desde CONSOLIDADO (198 metas)
        total_metas = len(metas_consolidado)
        
        # Contar por estado
        cumplidas = sum(1 for m in metas_consolidado if 'cumplid' in m['estado'].lower())
        en_curso = sum(1 for m in metas_consolidado if 'ejecuci' in m['estado'].lower() or 'curso' in m['estado'].lower())
        en_riesgo = sum(1 for m in metas_consolidado if 'riesgo' in m['estado'].lower())
        sin_iniciar = sum(1 for m in metas_consolidado if 'no inici' in m['estado'].lower())
        
        # Promedios ponderados por estado
        avance_prom = ((cumplidas * 100) + (en_curso * 60) + (en_riesgo * 30)) / total_metas if total_metas > 0 else 0
        ejec_fin_prom = ((cumplidas * 100) + (en_curso * 60) + (en_riesgo * 30)) / total_metas if total_metas > 0 else 0
        
        presup_total = sum(m['presupuesto_asig'] for m in metas_consolidado)
        presup_ejec = sum(m['presupuesto_ejec'] for m in metas_consolidado)
        
        kpis = {
            'total_metas': total_metas,
            'metas_cumplidas': cumplidas,
            'metas_en_curso': en_curso,
            'metas_en_riesgo': en_riesgo,
            'metas_sin_iniciar': sin_iniciar,
            'avance_prom': round(avance_prom, 1),
            'ejec_fin_prom': round(ejec_fin_prom, 1),
            'presupuesto_total': round(presup_total, 0),
            'presupuesto_ejec': round(presup_ejec, 0),
        }
        
        distrib_estados = {
            'Cumplida': cumplidas,
            'En ejecución': en_curso,
            'En riesgo': en_riesgo,
            'No iniciada': sin_iniciar,
        }
        
        # Resumen por eje (usando consolidado)
        resumen_eje = []
        for eje in plan_df['EJE'].unique():
            metas_eje = [m for m in metas_consolidado if m['eje'] == eje]
            avance_medio = sum(m['avance_fisico_pct'] for m in metas_eje) / len(metas_eje) if metas_eje else 0
            resumen_eje.append({
                'EJE': eje,
                'TOTAL_METAS': len(metas_eje),
                'AVANCE_MEDIO': round(avance_medio, 1)
            })
        
        _plan_cache = {
            'kpis': kpis,
            'distrib_estados': distrib_estados,
            'resumen_eje': resumen_eje,
            'metas_consolidado': metas_consolidado,
            'metas_payload': metas_por_ano,  # Todas las metas por año (2024 y 2025)
        }
        
        logger.info(f"✅ Cache creado: {total_metas} metas consolidadas, {len(metas_por_ano)} registros por año")
        return _plan_cache
        
    except Exception as e:
        logger.error(f"Error cargando Excel: {e}", exc_info=True)
        return None


@seguimiento_bp.route('/seguimiento', endpoint='index')
@require_permission('seguimiento')
def seguimiento_plan():
    data = _load_plan_excel()
    if not data:
        abort(500, description='No se pudo cargar el Excel del plan de desarrollo')

    return render_template(
        'seguimiento_plan_excel.html',
        kpis=data['kpis'],
        distrib_estados=data['distrib_estados'],
        resumen_eje=data['resumen_eje'],
        metas=data['metas_consolidado'],
        metas_consolidado=data['metas_consolidado'],
        metas_anuales=data['metas_payload']
    )


@seguimiento_bp.route('/seguimiento/api/metas')
def api_seguimiento_metas():
    data = _load_plan_excel()
    if not data:
        abort(500)

    # Filtros
    modo = (request.args.get('modo') or 'CONSOLIDADO').strip().upper()
    metas_base = data['metas_consolidado'] if modo == 'CONSOLIDADO' else data['metas_payload']

    q = (request.args.get('q') or '').strip().lower()
    estado = (request.args.get('estado') or '').strip().upper()
    eje = (request.args.get('eje') or '').strip()
    sector = (request.args.get('sector') or '').strip()
    ano = (request.args.get('ano') or '').strip()

    def matches(meta):
        if q:
            texto = ' '.join(str(v) for v in [
                meta.get('meta_producto'),
                meta.get('eje'),
                meta.get('sector'),
                meta.get('secretaria')
            ]).lower()
            if q not in texto:
                return False
        if estado and estado not in meta.get('estado', '').upper():
            return False
        if eje and meta.get('eje') != eje:
            return False
        if sector and meta.get('sector') != sector:
            return False
        if ano and str(meta.get('ano')) != ano:
            return False
        return True

    filtradas = [m for m in metas_base if matches(m)]
    
    return jsonify({
        'metas': filtradas,
        'total': len(filtradas),
        'distrib_estados': data['distrib_estados']
    })


@seguimiento_bp.route('/seguimiento/export/excel')
def export_seguimiento_excel():
    data = _load_plan_excel()
    if not data:
        abort(500)
    
    df = pd.DataFrame(data['metas_consolidado'])
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Seguimiento')
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f'seguimiento_plan_{datetime.now().strftime("%Y%m%d")}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
