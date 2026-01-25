from flask import Blueprint, render_template
from app.models.contrato import Contrato
import json

contratos_view = Blueprint('contratos_view', __name__)


def _parse_json(text, default):
    try:
        return json.loads(text) if text else default
    except Exception:
        return default


def _fmt_money(value):
    try:
        return f"${value:,.0f}" if value is not None else "—"
    except Exception:
        return str(value) if value is not None else "—"


@contratos_view.route('/contratos/<int:contrato_id>')
def ver_contrato(contrato_id):
    contrato = Contrato.query.get_or_404(contrato_id)

    docs = _parse_json(contrato.documentos_json, [])
    proponentes = _parse_json(contrato.proponentes_json, [])
    modificaciones = _parse_json(contrato.modificaciones_json, [])
    datos_completos = _parse_json(contrato.datos_completos_json, {})

    return render_template(
        'contrato_detalle_view.html',
        contrato=contrato,
        docs=docs,
        proponentes=proponentes,
        modificaciones=modificaciones,
        datos_completos=datos_completos,
        fmt_money=_fmt_money,
    )
