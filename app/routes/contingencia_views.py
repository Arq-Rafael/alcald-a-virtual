from flask import Blueprint, render_template, abort, redirect, url_for
from app.models.plan_contingencia import PlanContingencia
from app.utils.contingencia_helpers import get_datos_supata
from app import db
import json

contingencia_views = Blueprint(
    'contingencia_views', __name__, url_prefix='/gestion-riesgo/planes-contingencia'
)


def _cargar_oficial(plan: PlanContingencia):
    """Extrae la estructura oficial almacenada en multimedia_embed.plan_oficial."""
    try:
        base = json.loads(plan.multimedia_embed) if plan.multimedia_embed else {}
    except Exception:
        base = {}
    return base.get('plan_oficial', {})


@contingencia_views.route('/')
def index():
    # Redirige a la nueva versión V2
    return redirect(url_for('contingencia.listar_planes'))


@contingencia_views.route('/editar/<int:plan_id>')
@contingencia_views.route('/editar/<int:plan_id>/<seccion>')
def editar(plan_id: int, seccion: str = 'introduccion'):
    plan = PlanContingencia.query.get(plan_id)
    if not plan:
        abort(404)

    # Solo permitir edición si no está aprobado
    if plan.estado.lower() in ['aprobado', 'aprobado_comite']:
        return render_template('contingencia_detalle.html', plan=plan, datos_municipio=get_datos_supata(), oficial=_cargar_oficial(plan))

    oficial = _cargar_oficial(plan)
    datos_municipio = get_datos_supata()
    return render_template(
        'contingencia_editar_wizard.html',
        plan=plan,
        seccion_actual=seccion,
        datos_municipio=datos_municipio,
        oficial=oficial,
    )


@contingencia_views.route('/detalle/<int:plan_id>')
def detalle(plan_id: int):
    plan = PlanContingencia.query.get(plan_id)
    if not plan:
        abort(404)
    oficial = _cargar_oficial(plan)
    return render_template(
        'contingencia_detalle.html',
        plan=plan,
        datos_municipio=get_datos_supata(),
        oficial=oficial,
    )
