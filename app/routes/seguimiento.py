import io
import logging
import math
import os
from datetime import datetime

try:
    import pandas as pd
except Exception:
    pd = None

from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, send_file, session, url_for
from markupsafe import Markup
from sqlalchemy import func

from app import db
from app.models.metas import InformeProgresoMetas, InformeProgresoMetasFoto
from app.utils import current_session_secretaria, is_admin

logger = logging.getLogger(__name__)
seguimiento_bp = Blueprint("seguimiento", __name__)

_plan_cache = None
_enriched_cache = None


def _safe_str(value):
    return str(value or "").strip()


def _safe_float(value, default=0.0):
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip().replace("%", "").replace(",", ".")
    if not raw:
        return default
    try:
        return float(raw)
    except Exception:
        return default


def _normalize_col(name):
    txt = _safe_str(name).upper()
    map_chars = str.maketrans(
        {
            "Á": "A",
            "É": "E",
            "Í": "I",
            "Ó": "O",
            "Ú": "U",
            "Ñ": "N",
            " ": "_",
            "-": "_",
        }
    )
    return txt.translate(map_chars)


def _pick_col(index_map, *candidates):
    for candidate in candidates:
        key = _normalize_col(candidate)
        if key in index_map:
            return index_map[key]
    return None


def _to_iso_date(value):
    if value is None:
        return None
    if hasattr(value, "strftime"):
        try:
            return value.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return None
    text = _safe_str(value)
    if not text or text.lower() in ("nat", "nan", "none"):
        return None
    if len(text) >= 10 and text[4] == "-":
        return text[:10]
    return text


def _build_status_from_avance(avance):
    if avance >= 100:
        return "Cumplida"
    if avance <= 0.1:
        return "No iniciada"
    return "En curso"


def _load_plan_excel():
    global _plan_cache
    if _plan_cache is not None:
        return _plan_cache

    if pd is None:
        logger.error("pandas no disponible para cargar plan de metas")
        return None

    base_dir = os.path.join(str(current_app.config["BASE_DIR"]), "documentos_generados", "plan de desarollo")
    file_path = os.path.join(base_dir, "BASE_RENDICION_PLAN_DESARROLLO_SUPATA.xlsx")
    if not os.path.exists(file_path):
        logger.error(f"Excel no encontrado: {file_path}")
        return None

    try:
        plan_df = pd.read_excel(file_path, sheet_name="PLAN_DESARROLLO")
        avances_df = pd.read_excel(file_path, sheet_name="REGISTRO_AVANCES")
    except Exception as exc:
        logger.error(f"Error leyendo excel de metas: {exc}", exc_info=True)
        return None

    avances_map = {_normalize_col(col): col for col in avances_df.columns}
    plan_map = {_normalize_col(col): col for col in plan_df.columns}

    c_id = _pick_col(avances_map, "ID_META")
    c_bpim = _pick_col(avances_map, "BPIM")
    c_eje = _pick_col(avances_map, "EJE")
    c_sector = _pick_col(avances_map, "SECTOR")
    c_meta = _pick_col(avances_map, "META_PRODUCTO")
    c_ano = _pick_col(avances_map, "ANO", "AÑO")
    c_secretaria = _pick_col(avances_map, "SECRETARIA")
    c_estado = _pick_col(avances_map, "ESTADO")
    c_meta_prog = _pick_col(avances_map, "META_PROGRAMADA_ANO", "META_PROGRAMADA_AÑO")
    c_avance_ejec = _pick_col(avances_map, "AVANCE_EJECUTADO_ANO", "AVANCE_EJECUTADO_AÑO")
    c_avance_pct = _pick_col(avances_map, "%_AVANCE_FISICO", "PCT_AVANCE_FISICO")
    c_presup_asig = _pick_col(avances_map, "PRESUPUESTO_ASIGNADO")
    c_presup_ejec = _pick_col(avances_map, "PRESUPUESTO_EJECUTADO")
    c_fin_pct = _pick_col(avances_map, "%_EJEC_FINANCIERA", "PCT_EJEC_FINANCIERA")
    c_proyecto = _pick_col(avances_map, "PROYECTO_ASOCIADO")
    c_fuente = _pick_col(avances_map, "FUENTE_FINANCIACION")
    c_fecha = _pick_col(avances_map, "FECHA_REGISTRO", "FECHA_ACTUALIZACION", "FECHA_CORTE")
    c_criticidad = _pick_col(avances_map, "CRITICIDAD", "NIVEL_CRITICIDAD", "IMPACTO")
    c_responsable = _pick_col(avances_map, "RESPONSABLE")

    if not c_id:
        logger.error("La hoja REGISTRO_AVANCES no tiene columna ID_META")
        return None

    metas_anuales = []
    for _, row in avances_df.iterrows():
        meta_id = _safe_str(row.get(c_id))
        if not meta_id:
            continue

        avance_pct = _safe_float(row.get(c_avance_pct))
        estado = _safe_str(row.get(c_estado))
        if not estado:
            estado = _build_status_from_avance(avance_pct)

        ano = None
        ano_raw = row.get(c_ano) if c_ano else None
        if ano_raw is not None and not pd.isna(ano_raw):
            try:
                ano = int(ano_raw)
            except Exception:
                ano = None

        metas_anuales.append(
            {
                "id_meta": meta_id,
                "bpim": _safe_str(row.get(c_bpim)),
                "eje": _safe_str(row.get(c_eje)),
                "sector": _safe_str(row.get(c_sector)),
                "meta_producto": _safe_str(row.get(c_meta)),
                "ano": ano,
                "secretaria": _safe_str(row.get(c_secretaria)) or None,
                "estado": estado,
                "meta_programada": _safe_float(row.get(c_meta_prog)),
                "avance_ejecutado": _safe_float(row.get(c_avance_ejec)),
                "avance_fisico_pct": avance_pct,
                "presupuesto_asig": _safe_float(row.get(c_presup_asig)),
                "presupuesto_ejec": _safe_float(row.get(c_presup_ejec)),
                "ejec_fin_pct": _safe_float(row.get(c_fin_pct)),
                "proyecto": _safe_str(row.get(c_proyecto)) or None,
                "fuente": _safe_str(row.get(c_fuente)) or None,
                "fecha_actualizacion": _to_iso_date(row.get(c_fecha)) if c_fecha else None,
                "criticidad": _safe_str(row.get(c_criticidad)) or None,
                "responsable": _safe_str(row.get(c_responsable)) or None,
            }
        )

    plan_id_col = _pick_col(plan_map, "ID_META")
    plan_bpim_col = _pick_col(plan_map, "BPIM")
    plan_eje_col = _pick_col(plan_map, "EJE")
    plan_sector_col = _pick_col(plan_map, "SECTOR")
    plan_meta_col = _pick_col(plan_map, "META_PRODUCTO")

    plan_rows = {}
    if plan_id_col:
        for _, row in plan_df.iterrows():
            rid = _safe_str(row.get(plan_id_col))
            if rid:
                plan_rows[rid] = row

    all_ids = sorted(set(plan_rows.keys()) | {m["id_meta"] for m in metas_anuales})
    metas_consolidado = []
    for meta_id in all_ids:
        rows = [m for m in metas_anuales if m["id_meta"] == meta_id]
        if rows:
            rows.sort(key=lambda item: (item.get("ano") or 0, item.get("fecha_actualizacion") or ""), reverse=True)
            current = dict(rows[0])
            current["ano"] = f"CONSOLIDADO ({rows[0].get('ano') or 'N/D'})"
            current["anos_disponibles"] = sorted({r.get("ano") for r in rows if r.get("ano")})
            metas_consolidado.append(current)
            continue

        plan_row = plan_rows.get(meta_id)
        metas_consolidado.append(
            {
                "id_meta": meta_id,
                "bpim": _safe_str(plan_row.get(plan_bpim_col)) if plan_row is not None else None,
                "eje": _safe_str(plan_row.get(plan_eje_col)) if plan_row is not None else None,
                "sector": _safe_str(plan_row.get(plan_sector_col)) if plan_row is not None else None,
                "meta_producto": _safe_str(plan_row.get(plan_meta_col)) if plan_row is not None else None,
                "ano": "CONSOLIDADO (Sin datos)",
                "secretaria": None,
                "estado": "No iniciada",
                "meta_programada": 0.0,
                "avance_ejecutado": 0.0,
                "avance_fisico_pct": 0.0,
                "presupuesto_asig": 0.0,
                "presupuesto_ejec": 0.0,
                "ejec_fin_pct": 0.0,
                "proyecto": None,
                "fuente": None,
                "fecha_actualizacion": None,
                "criticidad": None,
                "responsable": None,
                "anos_disponibles": [],
            }
        )

    total = len(metas_consolidado)
    cumplidas = sum(1 for m in metas_consolidado if "cumplid" in _safe_str(m.get("estado")).lower() or _safe_float(m.get("avance_fisico_pct")) >= 100)
    no_iniciadas = sum(1 for m in metas_consolidado if "no inici" in _safe_str(m.get("estado")).lower() or _safe_float(m.get("avance_fisico_pct")) <= 0.1)
    en_riesgo = sum(1 for m in metas_consolidado if "riesgo" in _safe_str(m.get("estado")).lower())
    en_curso = max(0, total - cumplidas - no_iniciadas - en_riesgo)

    avance_prom = round(sum(_safe_float(m.get("avance_fisico_pct")) for m in metas_consolidado) / total, 1) if total else 0.0
    fin_prom = round(sum(_safe_float(m.get("ejec_fin_pct")) for m in metas_consolidado) / total, 1) if total else 0.0
    presupuesto_total = round(sum(_safe_float(m.get("presupuesto_asig")) for m in metas_consolidado), 0)
    presupuesto_ejec = round(sum(_safe_float(m.get("presupuesto_ejec")) for m in metas_consolidado), 0)

    kpis = {
        "total_metas": total,
        "metas_cumplidas": cumplidas,
        "metas_en_curso": en_curso,
        "metas_en_riesgo": en_riesgo,
        "metas_sin_iniciar": no_iniciadas,
        "avance_prom": avance_prom,
        "ejec_fin_prom": fin_prom,
        "presupuesto_total": presupuesto_total,
        "presupuesto_ejec": presupuesto_ejec,
    }
    distrib_estados = {
        "Cumplida": cumplidas,
        "En curso": en_curso,
        "En riesgo": en_riesgo,
        "No iniciada": no_iniciadas,
    }

    by_eje = {}
    for meta in metas_consolidado:
        eje = _safe_str(meta.get("eje")) or "Sin eje"
        by_eje.setdefault(eje, []).append(meta)
    resumen_eje = [
        {
            "EJE": eje,
            "TOTAL_METAS": len(rows),
            "AVANCE_MEDIO": round(sum(_safe_float(r.get("avance_fisico_pct")) for r in rows) / max(1, len(rows)), 1),
        }
        for eje, rows in by_eje.items()
    ]

    _plan_cache = {
        "kpis": kpis,
        "distrib_estados": distrib_estados,
        "resumen_eje": resumen_eje,
        "metas_consolidado": metas_consolidado,
        "metas_payload": metas_anuales,
    }
    return _plan_cache


def _meta_key(raw):
    txt = _safe_str(raw)
    if txt.endswith(".0"):
        txt = txt[:-2]
    return txt


def _db_meta_context():
    info = {}
    try:
        rows = (
            db.session.query(
                InformeProgresoMetas.meta_id.label("meta_id"),
                func.count(InformeProgresoMetas.id).label("informes_count"),
                func.max(InformeProgresoMetas.fecha_informe).label("ultima_fecha"),
            )
            .group_by(InformeProgresoMetas.meta_id)
            .all()
        )
        for row in rows:
            info[_meta_key(row.meta_id)] = {
                "informes_count": int(row.informes_count or 0),
                "fecha_ultimo_informe": row.ultima_fecha.strftime("%Y-%m-%d") if row.ultima_fecha else None,
            }

        photos = (
            db.session.query(
                InformeProgresoMetas.meta_id.label("meta_id"),
                func.count(InformeProgresoMetasFoto.id).label("evidencias_count"),
            )
            .join(InformeProgresoMetasFoto, InformeProgresoMetasFoto.informe_id == InformeProgresoMetas.id)
            .group_by(InformeProgresoMetas.meta_id)
            .all()
        )
        for row in photos:
            key = _meta_key(row.meta_id)
            info.setdefault(key, {})
            info[key]["evidencias_count"] = int(row.evidencias_count or 0)
    except Exception as exc:
        logger.warning(f"[METAS] Sin contexto de informes: {exc}")
    return info


def _get_enriched():
    global _enriched_cache
    if _enriched_cache is not None:
        return _enriched_cache

    data = _load_plan_excel()
    if not data:
        return None

    context = _db_meta_context()
    consolidado = [dict(meta) for meta in data["metas_consolidado"]]
    for meta in consolidado:
        extra = context.get(_meta_key(meta.get("id_meta")), {})
        if extra:
            meta.update(extra)
            if not meta.get("fecha_actualizacion") and extra.get("fecha_ultimo_informe"):
                meta["fecha_actualizacion"] = extra["fecha_ultimo_informe"]
        meta.setdefault("informes_count", 0)
        meta.setdefault("evidencias_count", 0)

    try:
        from app.services import metas_service as svc
        enriched = svc.enrich_metas(consolidado, data["metas_payload"])
    except Exception as exc:
        logger.error(f"[METAS] Fallo enrich_metas: {exc}", exc_info=True)
        enriched = consolidado

    _enriched_cache = {"metas": enriched, "all_years": data["metas_payload"]}
    return _enriched_cache


def _scope_metas(metas):
    if is_admin():
        return metas
    sec = _safe_str(current_session_secretaria())
    if not sec:
        return metas
    return [meta for meta in metas if _safe_str(meta.get("secretaria")) == sec]


def _scope_all_years(rows):
    if is_admin():
        return rows
    sec = _safe_str(current_session_secretaria())
    if not sec:
        return rows
    return [row for row in rows if _safe_str(row.get("secretaria")) == sec]


def _clean(meta):
    return {k: v for k, v in meta.items() if k != "historico"}


def _api_login_guard():
    if "user" not in session:
        return jsonify({"error": "unauthorized"}), 401
    return None


def _available_filters(metas):
    return {
        "ejes": sorted({_safe_str(m.get("eje")) for m in metas if _safe_str(m.get("eje"))}),
        "secretarias": sorted({_safe_str(m.get("secretaria")) for m in metas if _safe_str(m.get("secretaria"))}),
    }


def _sort_metas(rows, sort_by, order):
    reverse = order == "desc"
    if sort_by == "avance":
        rows.sort(key=lambda m: _safe_float(m.get("avance_fisico_pct")), reverse=reverse)
    elif sort_by == "nombre":
        rows.sort(key=lambda m: _safe_str(m.get("meta_producto")).lower(), reverse=reverse)
    elif sort_by == "actualizacion":
        rows.sort(key=lambda m: _safe_str(m.get("ultima_actualizacion") or ""), reverse=reverse)
    elif sort_by == "rezago":
        rows.sort(key=lambda m: _safe_float(m.get("indice_rezago")), reverse=reverse)
    else:
        rows.sort(key=lambda m: _safe_float(m.get("score")), reverse=reverse)


def _meta_reports(meta_id):
    reports = []
    if not meta_id.isdigit():
        return reports
    mid = int(meta_id)
    rows = (
        InformeProgresoMetas.query.filter_by(meta_id=mid)
        .order_by(InformeProgresoMetas.fecha_informe.desc())
        .all()
    )
    for row in rows:
        evidencias = []
        try:
            photos = row.fotos.all() if hasattr(row.fotos, "all") else row.fotos
        except Exception:
            photos = []
        for photo in photos:
            evidencias.append(
                {
                    "filename": photo.filename,
                    "caption": photo.caption,
                    "url": f"/uploads/informes_metas/{photo.filename}",
                }
            )
        reports.append(
            {
                "id": row.id,
                "fecha": row.fecha_informe.strftime("%Y-%m-%d") if row.fecha_informe else None,
                "contrato_num": row.contrato_num,
                "descripcion": row.descripcion,
                "avance_manual": row.avance_manual,
                "observaciones": row.observaciones,
                "evidencias": evidencias,
            }
        )
    return reports


def _build_meta_detail(meta, all_years):
    meta_id = _meta_key(meta.get("id_meta"))
    timeline = []
    for row in all_years:
        if _meta_key(row.get("id_meta")) != meta_id:
            continue
        timeline.append(
            {
                "periodo": _safe_str(row.get("ano")) or "N/D",
                "estado": _safe_str(row.get("estado")) or "Sin dato",
                "avance_fisico_pct": round(_safe_float(row.get("avance_fisico_pct")), 1),
                "ejec_fin_pct": round(_safe_float(row.get("ejec_fin_pct")), 1),
                "meta_programada": round(_safe_float(row.get("meta_programada")), 2),
                "avance_ejecutado": round(_safe_float(row.get("avance_ejecutado")), 2),
                "fecha_actualizacion": row.get("fecha_actualizacion"),
                "fuente": "avance",
            }
        )
    timeline.sort(key=lambda t: (_safe_str(t.get("periodo")), _safe_str(t.get("fecha_actualizacion") or "")))

    informes = _meta_reports(meta_id)
    for item in informes:
        timeline.append(
            {
                "periodo": item.get("fecha") or "N/D",
                "estado": "Informe de seguimiento",
                "avance_fisico_pct": round(_safe_float(item.get("avance_manual")), 1),
                "ejec_fin_pct": None,
                "meta_programada": None,
                "avance_ejecutado": None,
                "fecha_actualizacion": item.get("fecha"),
                "fuente": "informe",
            }
        )
    timeline.sort(key=lambda t: (_safe_str(t.get("fecha_actualizacion") or "9999-99-99"), _safe_str(t.get("periodo"))))

    evidencias = []
    for item in informes:
        for ev in item.get("evidencias", []):
            evidence = dict(ev)
            evidence["informe_id"] = item["id"]
            evidence["fecha"] = item["fecha"]
            evidencias.append(evidence)

    resumen = (
        f"Meta {meta_id}: {meta.get('estado')} con avance {round(_safe_float(meta.get('avance_fisico_pct')), 1)}% "
        f"y score {round(_safe_float(meta.get('score')), 1)}/100."
    )
    return {
        **meta,
        "resumen_ejecutivo": resumen,
        "timeline": timeline,
        "informes": informes,
        "evidencias": evidencias,
        "causas_probables": meta.get("causas_rezago", []),
        "plan_mejora": meta.get("recomendaciones", []),
    }


@seguimiento_bp.route("/seguimiento", endpoint="index")
def seguimiento_plan():
    data = _load_plan_excel()
    if not data:
        abort(500, "No se pudo cargar el excel del plan")
    return render_template(
        "seguimiento_plan_excel.html",
        kpis=data["kpis"],
        distrib_estados=data["distrib_estados"],
        resumen_eje=data["resumen_eje"],
        metas=data["metas_consolidado"],
        metas_consolidado=data["metas_consolidado"],
        metas_anuales=data["metas_payload"],
    )


@seguimiento_bp.route("/seguimiento/api/metas")
def api_seguimiento_metas():
    guard = _api_login_guard()
    if guard:
        return guard
    data = _load_plan_excel()
    if not data:
        abort(500)

    modo = _safe_str(request.args.get("modo") or "CONSOLIDADO").upper()
    metas = data["metas_consolidado"] if modo == "CONSOLIDADO" else data["metas_payload"]

    q = _safe_str(request.args.get("q")).lower()
    estado = _safe_str(request.args.get("estado")).lower()
    eje = _safe_str(request.args.get("eje"))
    sector = _safe_str(request.args.get("sector"))
    ano = _safe_str(request.args.get("ano"))

    rows = _scope_metas(metas)
    filtered = []
    for row in rows:
        if q:
            haystack = " ".join(
                [
                    _safe_str(row.get("meta_producto")),
                    _safe_str(row.get("eje")),
                    _safe_str(row.get("sector")),
                    _safe_str(row.get("secretaria")),
                    _safe_str(row.get("id_meta")),
                ]
            ).lower()
            if q not in haystack:
                continue
        if estado and estado not in _safe_str(row.get("estado")).lower():
            continue
        if eje and _safe_str(row.get("eje")) != eje:
            continue
        if sector and _safe_str(row.get("sector")) != sector:
            continue
        if ano and _safe_str(row.get("ano")) != ano:
            continue
        filtered.append(row)

    return jsonify({"metas": filtered, "total": len(filtered), "distrib_estados": data["distrib_estados"]})


@seguimiento_bp.route("/seguimiento/export/excel")
def export_seguimiento_excel():
    data = _load_plan_excel()
    if not data:
        abort(500)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(data["metas_consolidado"]).to_excel(writer, index=False, sheet_name="Seguimiento")
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name=f"seguimiento_plan_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@seguimiento_bp.route("/metas")
def metas_dashboard():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    return render_template("metas_dashboard.html")


@seguimiento_bp.route("/api/metas/summary")
def api_metas_summary():
    guard = _api_login_guard()
    if guard:
        return guard
    ec = _get_enriched()
    if not ec:
        return jsonify({"error": "Sin datos del plan"}), 503

    from app.services import metas_service as svc

    metas = _scope_metas(ec["metas"])
    kpis = svc.compute_kpis(metas)
    ranking = svc.ranking_secretarias(metas)
    recomendaciones = svc.recomendaciones_generales(metas)
    rezagadas = [_clean(m) for m in svc.top_rezagadas(metas, 15)]
    planes_secretaria = [svc.plan_choque_secretaria(row["secretaria"], metas) for row in ranking[:8]]

    return jsonify(
        {
            "kpis": kpis,
            "ranking": ranking,
            "recomendaciones": recomendaciones,
            "rezagadas": rezagadas,
            "planes_secretaria": planes_secretaria,
            "metodologia": svc.score_methodology(),
            "filtros": _available_filters(metas),
        }
    )


@seguimiento_bp.route("/api/metas/charts")
def api_metas_charts():
    guard = _api_login_guard()
    if guard:
        return guard
    ec = _get_enriched()
    if not ec:
        return jsonify({"error": "Sin datos"}), 503
    from app.services import metas_service as svc
    metas = _scope_metas(ec["metas"])
    all_years = _scope_all_years(ec["all_years"])
    return jsonify(svc.charts_data(metas, all_years))


@seguimiento_bp.route("/api/metas/list")
def api_metas_list():
    guard = _api_login_guard()
    if guard:
        return guard
    ec = _get_enriched()
    if not ec:
        return jsonify({"error": "Sin datos"}), 503

    metas = _scope_metas(ec["metas"])
    q = _safe_str(request.args.get("q")).lower()
    estado = _safe_str(request.args.get("estado")).lower()
    eje = _safe_str(request.args.get("eje"))
    sec = _safe_str(request.args.get("sec"))
    riesgo = _safe_str(request.args.get("riesgo")).lower()
    semaforo = _safe_str(request.args.get("semaforo")).lower()
    sort_by = _safe_str(request.args.get("sort") or "indice_rezago")
    order = _safe_str(request.args.get("order") or "desc")
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(60, max(10, int(request.args.get("per_page", 25))))

    filtered = []
    for meta in metas:
        if q:
            haystack = " ".join(
                [
                    _safe_str(meta.get("id_meta")),
                    _safe_str(meta.get("bpim")),
                    _safe_str(meta.get("meta_producto")),
                    _safe_str(meta.get("eje")),
                    _safe_str(meta.get("sector")),
                    _safe_str(meta.get("secretaria")),
                    _safe_str(meta.get("estado")),
                    _safe_str(meta.get("responsable")),
                ]
            ).lower()
            if q not in haystack:
                continue
        if estado and estado not in _safe_str(meta.get("estado")).lower():
            continue
        if eje and _safe_str(meta.get("eje")) != eje:
            continue
        if sec and _safe_str(meta.get("secretaria")) != sec:
            continue
        if riesgo and _safe_str(meta.get("riesgo_nivel")).lower() != riesgo:
            continue
        if semaforo and _safe_str(meta.get("semaforo")).lower() != semaforo:
            continue
        filtered.append(meta)

    _sort_metas(filtered, sort_by, order)
    total = len(filtered)
    pages = max(1, math.ceil(total / per_page))
    start = (page - 1) * per_page
    end = start + per_page
    page_rows = [_clean(m) for m in filtered[start:end]]

    return jsonify(
        {
            "metas": page_rows,
            "total": total,
            "page": page,
            "pages": pages,
            "per_page": per_page,
            "filtros": _available_filters(metas),
        }
    )


@seguimiento_bp.route("/api/metas/<string:meta_id>")
def api_meta_detail(meta_id):
    guard = _api_login_guard()
    if guard:
        return guard
    ec = _get_enriched()
    if not ec:
        return jsonify({"error": "Sin datos"}), 503
    metas = _scope_metas(ec["metas"])
    meta = next((m for m in metas if _meta_key(m.get("id_meta")) == _meta_key(meta_id)), None)
    if not meta:
        return jsonify({"error": "Meta no encontrada"}), 404
    detail = _build_meta_detail(meta, _scope_all_years(ec["all_years"]))
    return jsonify(detail)


def _svg_escape(text):
    return (
        _safe_str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _svg_line(labels, serie_a, serie_b, title):
    width, height = 740, 280
    pad_l, pad_r, pad_t, pad_b = 50, 30, 30, 40
    inner_w = width - pad_l - pad_r
    inner_h = height - pad_t - pad_b
    max_v = max(1.0, max(serie_a + serie_b + [0]))

    def xy(idx, value, count):
        x = pad_l if count <= 1 else pad_l + (inner_w * idx / (count - 1))
        y = pad_t + (inner_h * (1 - (value / max_v)))
        return x, y

    count = max(len(labels), 1)
    line_a = " ".join([f"{xy(i, serie_a[i] if i < len(serie_a) else 0, count)[0]:.2f},{xy(i, serie_a[i] if i < len(serie_a) else 0, count)[1]:.2f}" for i in range(count)])
    line_b = " ".join([f"{xy(i, serie_b[i] if i < len(serie_b) else 0, count)[0]:.2f},{xy(i, serie_b[i] if i < len(serie_b) else 0, count)[1]:.2f}" for i in range(count)])

    label_svg = []
    for i, lbl in enumerate(labels):
        x, _ = xy(i, 0, count)
        label_svg.append(f'<text x="{x:.2f}" y="{height - 12}" text-anchor="middle" font-size="11" fill="#475569">{_svg_escape(lbl)}</text>')

    return Markup(
        f"""
        <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
          <rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>
          <text x="16" y="20" font-size="14" font-weight="700" fill="#0f172a">{_svg_escape(title)}</text>
          <line x1="{pad_l}" y1="{height-pad_b}" x2="{width-pad_r}" y2="{height-pad_b}" stroke="#cbd5e1"/>
          <line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{height-pad_b}" stroke="#cbd5e1"/>
          <polyline points="{line_a}" fill="none" stroke="#0f4c81" stroke-width="3" />
          <polyline points="{line_b}" fill="none" stroke="#f59e0b" stroke-width="3" />
          <text x="{width-210}" y="24" font-size="11" fill="#0f4c81">Avance fisico</text>
          <text x="{width-120}" y="24" font-size="11" fill="#f59e0b">Avance financiero</text>
          {''.join(label_svg)}
        </svg>
        """
    )


def _svg_bar(labels, values, title, color="#0f4c81"):
    width, height = 740, 300
    pad_l, pad_r, pad_t, pad_b = 220, 30, 28, 24
    inner_w = width - pad_l - pad_r
    row_h = max(22, int((height - pad_t - pad_b) / max(1, len(labels))))
    max_v = max(1.0, max(values or [0]))
    bars = []
    for i, label in enumerate(labels):
        val = values[i] if i < len(values) else 0
        y = pad_t + i * row_h + 2
        bar_w = (val / max_v) * inner_w
        bars.append(
            f'<text x="12" y="{y+12}" font-size="11" fill="#334155">{_svg_escape(label)}</text>'
            f'<rect x="{pad_l}" y="{y}" width="{bar_w:.2f}" height="{row_h-6}" fill="{color}" rx="5"/>'
            f'<text x="{pad_l + bar_w + 6:.2f}" y="{y+12}" font-size="11" fill="#0f172a">{val:.1f}</text>'
        )

    return Markup(
        f"""
        <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
          <rect width="{width}" height="{height}" fill="#ffffff"/>
          <text x="16" y="20" font-size="14" font-weight="700" fill="#0f172a">{_svg_escape(title)}</text>
          {''.join(bars)}
        </svg>
        """
    )


def _svg_donut(labels, values, title):
    width, height = 420, 260
    cx, cy, radius = 110, 130, 70
    total = max(1.0, sum(values or [0]))
    colors = ["#16a34a", "#0f4c81", "#f59e0b", "#ef4444", "#94a3b8"]

    pieces = []
    legend = []
    offset = 0.0
    circ = 2 * math.pi * radius
    for i, label in enumerate(labels):
        value = values[i] if i < len(values) else 0
        color = colors[i % len(colors)]
        frac = value / total
        seg = circ * frac
        pieces.append(
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{color}" stroke-width="26" '
            f'stroke-dasharray="{seg:.2f} {circ-seg:.2f}" stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 {cx} {cy})"/>'
        )
        legend.append(
            f'<rect x="220" y="{40 + i*28}" width="12" height="12" fill="{color}"/>'
            f'<text x="238" y="{50 + i*28}" font-size="11" fill="#334155">{_svg_escape(label)}: {int(value)}</text>'
        )
        offset += seg

    return Markup(
        f"""
        <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
          <rect width="{width}" height="{height}" fill="#ffffff"/>
          <text x="14" y="22" font-size="14" font-weight="700" fill="#0f172a">{_svg_escape(title)}</text>
          <circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="#e2e8f0" stroke-width="26"/>
          {''.join(pieces)}
          <text x="{cx}" y="{cy+4}" text-anchor="middle" font-size="16" font-weight="700" fill="#0f172a">{int(total)}</text>
          <text x="{cx}" y="{cy+20}" text-anchor="middle" font-size="10" fill="#64748b">Metas</text>
          {''.join(legend)}
        </svg>
        """
    )


def _render_pdf_response(html_str, filename):
    try:
        from weasyprint import HTML

        pdf_bytes = HTML(string=html_str, base_url=request.host_url).write_pdf()
        return send_file(io.BytesIO(pdf_bytes), as_attachment=True, download_name=filename, mimetype="application/pdf")
    except ImportError:
        return html_str, 200, {"Content-Type": "text/html; charset=utf-8"}
    except Exception as exc:
        logger.error(f"[METAS PDF] Error: {exc}", exc_info=True)
        abort(500, f"Error al generar PDF: {exc}")


@seguimiento_bp.route("/metas/export/pdf")
def metas_export_pdf():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    ec = _get_enriched()
    if not ec:
        abort(500, "Sin datos del plan")

    from app.services import metas_service as svc

    scope = _safe_str(request.args.get("scope") or "general").lower()
    sec = _safe_str(request.args.get("sec"))

    metas = _scope_metas(ec["metas"])
    all_years = _scope_all_years(ec["all_years"])

    plan_choque = None
    if scope == "secretaria":
        if not sec:
            abort(400, "Debe indicar sec para scope=secretaria")
        metas = [m for m in metas if _safe_str(m.get("secretaria")) == sec]
        all_years = [r for r in all_years if _safe_str(r.get("secretaria")) == sec]
        plan_choque = svc.plan_choque_secretaria(sec, metas)
    if not metas:
        abort(404, "No hay metas para el alcance solicitado")

    kpis = svc.compute_kpis(metas)
    charts = svc.charts_data(metas, all_years)
    ranking = svc.ranking_secretarias(metas) if scope == "general" else []
    rezagadas = svc.top_rezagadas(metas, 15)
    recomendaciones = svc.recomendaciones_generales(metas)

    chart_estado_svg = _svg_donut(
        charts.get("distribucion", {}).get("labels", []),
        charts.get("distribucion", {}).get("data", []),
        "Distribucion por estado",
    )
    chart_ranking_svg = _svg_bar(
        charts.get("ranking_secretarias", {}).get("labels", [])[:10],
        charts.get("ranking_secretarias", {}).get("score", [])[:10],
        "Ranking de secretarias por score",
        color="#0f4c81",
    )
    chart_evol_svg = _svg_line(
        charts.get("evolucion", {}).get("labels", []),
        charts.get("evolucion", {}).get("avance", []),
        charts.get("evolucion", {}).get("fin", []),
        "Evolucion del avance 2024-2025",
    )

    titulo = "Reporte General del Plan de Desarrollo" if scope == "general" else f"Reporte por Secretaria: {sec}"
    html_str = render_template(
        "metas_pdf.html",
        titulo=titulo,
        fecha=datetime.now().strftime("%Y-%m-%d %H:%M"),
        scope=scope,
        sec=sec,
        kpis=kpis,
        ranking=ranking,
        rezagadas=rezagadas,
        recomendaciones=recomendaciones,
        plan_choque=plan_choque,
        metodologia=svc.score_methodology(),
        chart_estado_svg=chart_estado_svg,
        chart_ranking_svg=chart_ranking_svg,
        chart_evol_svg=chart_evol_svg,
    )
    filename = f"metas_{scope}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return _render_pdf_response(html_str, filename)


@seguimiento_bp.route("/metas/<string:meta_id>/export/pdf")
def meta_export_pdf(meta_id):
    if "user" not in session:
        return redirect(url_for("auth.login"))

    ec = _get_enriched()
    if not ec:
        abort(500, "Sin datos del plan")

    metas = _scope_metas(ec["metas"])
    meta = next((m for m in metas if _meta_key(m.get("id_meta")) == _meta_key(meta_id)), None)
    if not meta:
        abort(404, "Meta no encontrada")

    detail = _build_meta_detail(meta, _scope_all_years(ec["all_years"]))
    line_rows = [row for row in detail["timeline"] if row.get("fuente") == "avance"]
    labels = [str(r.get("periodo")) for r in line_rows]
    avances = [round(_safe_float(r.get("avance_fisico_pct")), 1) for r in line_rows]
    finanzas = [round(_safe_float(r.get("ejec_fin_pct")), 1) for r in line_rows]
    chart_meta_svg = _svg_line(labels, avances, finanzas, f"Evolucion de la meta {meta_id}")

    html_str = render_template(
        "meta_detail_pdf.html",
        fecha=datetime.now().strftime("%Y-%m-%d %H:%M"),
        meta=detail,
        chart_meta_svg=chart_meta_svg,
    )
    filename = f"meta_{meta_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return _render_pdf_response(html_str, filename)
