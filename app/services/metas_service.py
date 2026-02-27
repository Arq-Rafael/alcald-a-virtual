"""
Servicio de analitica para Seguimiento de Metas.
"""

from __future__ import annotations

import datetime as dt
import re
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

PLAN_START = dt.date(2024, 1, 1)
PLAN_END = dt.date(2027, 12, 31)

UPDATE_STALE_WARNING_DAYS = 45
UPDATE_STALE_CRITICAL_DAYS = 90

RISK_MIN_ELAPSED_PCT = 20
RISK_LOW_GAP = 5
RISK_MEDIUM_GAP = 12
RISK_HIGH_GAP = 25

SCORE_W_AVANCE = 0.50
SCORE_W_FIN = 0.20
SCORE_W_TIME = 0.30

TREND_BONUS = {
    "mejorando": 6.0,
    "estable": 0.0,
    "empeorando": -6.0,
}


def plan_elapsed_pct(reference: Optional[dt.date] = None) -> float:
    today = reference or dt.date.today()
    total_days = max(1, (PLAN_END - PLAN_START).days)
    elapsed_days = (min(today, PLAN_END) - PLAN_START).days
    pct = (elapsed_days / total_days) * 100
    return max(0.0, min(100.0, pct))


PCT_TIEMPO = round(plan_elapsed_pct(), 1)


def score_methodology() -> Dict[str, Any]:
    return {
        "formula": (
            "score = (avance*0.50 + financiero*0.20 + alineacion_tiempo*0.30) "
            "+ bonus_tendencia - penalizacion_desactualizacion"
        ),
        "riesgo_regla": (
            "Riesgo por brecha tiempo-avance con tiempo transcurrido >= 20%: "
            "bajo (>=5), medio (>=12), alto (>=25)."
        ),
        "componentes": {
            "avance": "50%",
            "financiero": "20%",
            "alineacion_tiempo": "30%",
            "bonus_tendencia": "+6 / 0 / -6",
            "penalizacion_desactualizacion": "0..20 puntos",
        },
    }


def _safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip().replace("%", "").replace(",", ".")
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _text(value: Any) -> str:
    return str(value or "").strip()


def _parse_date(value: Any) -> Optional[dt.date]:
    if value is None:
        return None
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, (int, float)) and int(value) == value:
        year = int(value)
        if 2000 <= year <= 2100:
            return dt.date(year, 12, 31)

    raw = str(value).strip()
    if not raw:
        return None
    for pattern in (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
    ):
        try:
            return dt.datetime.strptime(raw, pattern).date()
        except ValueError:
            pass
    match = re.search(r"(20\d{2})", raw)
    if match:
        return dt.date(int(match.group(1)), 12, 31)
    return None


def _iso_date(value: Optional[dt.date]) -> Optional[str]:
    return value.isoformat() if value else None


def _collect_history_points(historico: Iterable[Dict[str, Any]]) -> List[Tuple[dt.date, float]]:
    points: List[Tuple[dt.date, float]] = []
    for row in historico:
        advance = _safe_float(row.get("avance_fisico_pct"))
        if advance < 0:
            continue
        row_date = _parse_date(row.get("fecha_actualizacion") or row.get("fecha_registro"))
        if not row_date:
            year = row.get("ano")
            if isinstance(year, (int, float)) and int(year) == year and 2000 <= int(year) <= 2100:
                row_date = dt.date(int(year), 12, 31)
        if row_date:
            points.append((row_date, advance))
    points.sort(key=lambda item: item[0])
    return points


def _trend(historico: Iterable[Dict[str, Any]]) -> Tuple[str, float]:
    points = _collect_history_points(historico)
    if len(points) < 2:
        return "estable", 0.0
    prev = points[-2][1]
    last = points[-1][1]
    delta = round(last - prev, 1)
    if delta > 2:
        return "mejorando", delta
    if delta < -2:
        return "empeorando", delta
    return "estable", delta


def _escalate_risk(level: str) -> str:
    order = ["ninguno", "bajo", "medio", "alto"]
    try:
        idx = order.index(level)
    except ValueError:
        return "medio"
    return order[min(len(order) - 1, idx + 1)]


def _risk(avance: float, is_done: bool, tendencia: str, dias_sin_actualizacion: Optional[int]) -> Tuple[str, float, float, str]:
    expected = PCT_TIEMPO
    gap = round(max(0.0, expected - avance), 1)

    if is_done:
        return "ninguno", gap, expected, "Meta cumplida: sin riesgo operativo."

    if expected < RISK_MIN_ELAPSED_PCT:
        level = "ninguno"
    elif avance <= 0.1 and expected >= 25:
        level = "alto"
    elif gap >= RISK_HIGH_GAP:
        level = "alto"
    elif gap >= RISK_MEDIUM_GAP:
        level = "medio"
    elif gap >= RISK_LOW_GAP:
        level = "bajo"
    else:
        level = "ninguno"

    parts = [
        f"Tiempo transcurrido: {expected:.1f}%.",
        f"Avance real: {avance:.1f}%.",
        f"Brecha: {gap:.1f} puntos.",
    ]

    if tendencia == "empeorando" and level in ("ninguno", "bajo", "medio"):
        level = _escalate_risk(level)
        parts.append("Escala por tendencia negativa.")

    if dias_sin_actualizacion is None:
        if level in ("ninguno", "bajo"):
            level = "medio"
        parts.append("Sin fecha de actualizacion.")
    elif dias_sin_actualizacion > UPDATE_STALE_CRITICAL_DAYS:
        level = _escalate_risk(level)
        parts.append(f"Escala por {dias_sin_actualizacion} dias sin actualizacion.")

    return level, gap, expected, " ".join(parts)


def _score(
    avance: float,
    financiero: float,
    gap_tiempo: float,
    tendencia: str,
    dias_sin_actualizacion: Optional[int],
) -> Tuple[float, Dict[str, float]]:
    avance_norm = _clip(avance, 0.0, 100.0)
    fin_norm = _clip(financiero, 0.0, 100.0)
    time_align = _clip(100.0 - (gap_tiempo * 2.2), 0.0, 100.0)

    base = (avance_norm * SCORE_W_AVANCE) + (fin_norm * SCORE_W_FIN) + (time_align * SCORE_W_TIME)
    bonus = TREND_BONUS.get(tendencia, 0.0)

    if dias_sin_actualizacion is None:
        stale_penalty = 8.0
    elif dias_sin_actualizacion <= UPDATE_STALE_WARNING_DAYS:
        stale_penalty = 0.0
    else:
        stale_penalty = min(20.0, (dias_sin_actualizacion - UPDATE_STALE_WARNING_DAYS) * 0.3)

    final_score = _clip(base + bonus - stale_penalty, 0.0, 100.0)
    return round(final_score, 1), {
        "avance": round(avance_norm, 1),
        "financiero": round(fin_norm, 1),
        "alineacion_tiempo": round(time_align, 1),
        "bonus_tendencia": round(bonus, 1),
        "penalizacion_desactualizacion": round(stale_penalty, 1),
        "score_base": round(base, 1),
    }


def _is_done(meta: Dict[str, Any], avance: float) -> bool:
    estado_raw = _text(meta.get("estado")).lower()
    return "cumplid" in estado_raw or avance >= 100.0


def _estado(meta: Dict[str, Any], avance: float, risk_level: str) -> str:
    if _is_done(meta, avance):
        return "Cumplida"
    estado_raw = _text(meta.get("estado")).lower()
    if "no inici" in estado_raw or avance <= 0.1:
        return "No iniciada"
    if risk_level in ("alto", "medio") or "riesgo" in estado_raw:
        return "En riesgo"
    return "En curso"


def _semaforo(risk_level: str, score: float) -> str:
    if risk_level == "alto":
        return "rojo"
    if risk_level == "medio":
        return "naranja"
    if risk_level == "bajo":
        return "amarillo"
    if score >= 70:
        return "verde"
    if score >= 50:
        return "amarillo"
    if score >= 35:
        return "naranja"
    return "rojo"


def _criticidad(meta: Dict[str, Any]) -> Tuple[int, str]:
    raw = _text(meta.get("criticidad") or meta.get("nivel_criticidad") or meta.get("impacto")).lower()
    if not raw:
        return 1, "baja"
    if raw.isdigit():
        num = int(raw)
        if num >= 3:
            return 3, "alta"
        if num == 2:
            return 2, "media"
        return 1, "baja"
    if any(token in raw for token in ("alta", "alto", "critica", "critico", "estrategica")):
        return 3, "alta"
    if any(token in raw for token in ("media", "medio", "moderada")):
        return 2, "media"
    return 1, "baja"


def _delay_causes(
    meta: Dict[str, Any],
    estado_meta: str,
    gap_tiempo: float,
    tendencia: str,
    dias_sin_actualizacion: Optional[int],
    criticidad: str,
) -> List[Dict[str, str]]:
    causes: List[Dict[str, str]] = []
    avance = _safe_float(meta.get("avance_fisico_pct"))
    fin = _safe_float(meta.get("ejec_fin_pct"))
    evidencias_count = int(_safe_float(meta.get("evidencias_count"), 0))

    if estado_meta == "No iniciada" and PCT_TIEMPO >= 20:
        causes.append({"tipo": "arranque", "detalle": "No presenta inicio operativo pese al tiempo transcurrido."})
    if gap_tiempo >= RISK_MEDIUM_GAP:
        causes.append({"tipo": "atraso_tiempo", "detalle": f"Brecha alta frente al tiempo esperado ({gap_tiempo:.1f} puntos)."})
    if fin < 30 and _safe_float(meta.get("presupuesto_asig")) > 0:
        causes.append({"tipo": "financiero", "detalle": "Ejecucion financiera baja para el presupuesto asignado."})
    if tendencia == "empeorando":
        causes.append({"tipo": "tendencia", "detalle": "La tendencia de avance muestra deterioro frente al ultimo corte."})
    if dias_sin_actualizacion is None or dias_sin_actualizacion > UPDATE_STALE_WARNING_DAYS:
        text = "sin fecha de actualizacion" if dias_sin_actualizacion is None else f"{dias_sin_actualizacion} dias sin actualizacion"
        causes.append({"tipo": "control", "detalle": f"Riesgo de control por registros desactualizados ({text})."})
    if avance > 0 and evidencias_count == 0:
        causes.append({"tipo": "evidencia", "detalle": "Reporta avance pero no tiene evidencias cargadas."})
    if criticidad == "alta" and estado_meta in ("En riesgo", "No iniciada"):
        causes.append({"tipo": "criticidad", "detalle": "Meta de alta criticidad con riesgo operativo vigente."})

    if not causes:
        causes.append({"tipo": "sin_hallazgos", "detalle": "No se identifican causas criticas adicionales en este corte."})
    return causes


def _meta_recommendations(
    meta: Dict[str, Any],
    estado_meta: str,
    risk_level: str,
    tendencia: str,
    dias_sin_actualizacion: Optional[int],
    criticidad: str,
) -> List[Dict[str, str]]:
    recs: List[Dict[str, str]] = []
    secretaria = _text(meta.get("secretaria") or "la secretaria responsable")
    avance = _safe_float(meta.get("avance_fisico_pct"))
    fin = _safe_float(meta.get("ejec_fin_pct"))
    evidencias_count = int(_safe_float(meta.get("evidencias_count"), 0))

    if estado_meta == "No iniciada" and PCT_TIEMPO >= 20:
        recs.append(
            {
                "prioridad": "alta",
                "icono": "bi-play-circle-fill",
                "titulo": "Plan de arranque inmediato",
                "detalle": (
                    f"1) Designar lider operativo en {secretaria}. "
                    "2) Cronograma minimo de 90 dias con hitos semanales. "
                    "3) Estimacion de recursos y gestion administrativa. "
                    "4) Primer avance reportado en el proximo corte."
                ),
            }
        )

    if risk_level in ("alto", "medio"):
        recs.append(
            {
                "prioridad": "alta" if risk_level == "alto" else "media",
                "icono": "bi-shield-exclamation",
                "titulo": "Plan de contencion del rezago",
                "detalle": (
                    "Ajustar alcance y priorizar hitos criticos. "
                    "Convocar mesa tecnica intersecretarial para destrabar contratacion y presupuesto."
                ),
            }
        )

    if _safe_float(meta.get("presupuesto_asig")) > 0 and fin < 30:
        recs.append(
            {
                "prioridad": "media",
                "icono": "bi-cash-stack",
                "titulo": "Activar gestion presupuestal",
                "detalle": "Revisar compromisos contractuales y calendarizar compras para acelerar ejecucion financiera.",
            }
        )

    if evidencias_count == 0 and avance > 0:
        recs.append(
            {
                "prioridad": "media",
                "icono": "bi-images",
                "titulo": "Estandarizar evidencias",
                "detalle": "Cargar evidencias tecnicas y documentales en formato institucional.",
            }
        )

    if dias_sin_actualizacion is None or dias_sin_actualizacion > UPDATE_STALE_WARNING_DAYS:
        recs.append(
            {
                "prioridad": "media",
                "icono": "bi-calendar-check",
                "titulo": "Control mensual obligatorio",
                "detalle": "Implementar corte mensual con responsable nominal y validacion por Planeacion.",
            }
        )

    if tendencia == "empeorando":
        recs.append(
            {
                "prioridad": "media",
                "icono": "bi-graph-down-arrow",
                "titulo": "Corregir tendencia negativa",
                "detalle": "Definir plan de recuperacion con hitos de 30/60 dias y seguimiento semanal.",
            }
        )

    if not recs:
        recs.append(
            {
                "prioridad": "baja",
                "icono": "bi-check-circle-fill",
                "titulo": "Mantener disciplina de ejecucion",
                "detalle": "Mantener ritmo, actualizacion mensual y consolidacion de evidencias.",
            }
        )

    if criticidad == "alta" and recs:
        recs[0]["prioridad"] = "alta"
    return recs


def _ultima_actualizacion(meta: Dict[str, Any], historico: Iterable[Dict[str, Any]]) -> Optional[dt.date]:
    candidates: List[dt.date] = []
    primary = _parse_date(meta.get("fecha_actualizacion") or meta.get("fecha_registro"))
    if primary:
        candidates.append(primary)
    for row in historico:
        d = _parse_date(row.get("fecha_actualizacion") or row.get("fecha_registro"))
        if d:
            candidates.append(d)
    return max(candidates) if candidates else None


def _sanitize_historico_row(row: Dict[str, Any]) -> Dict[str, Any]:
    clean = dict(row)
    clean["avance_fisico_pct"] = round(_safe_float(row.get("avance_fisico_pct")), 1)
    clean["ejec_fin_pct"] = round(_safe_float(row.get("ejec_fin_pct")), 1)
    for key in ("fecha_actualizacion", "fecha_registro"):
        parsed = _parse_date(row.get(key))
        if parsed:
            clean[key] = parsed.isoformat()
    year = row.get("ano")
    if isinstance(year, (int, float)) and int(year) == year:
        clean["ano"] = int(year)
    return clean


def enrich_metas(consolidado: List[Dict[str, Any]], all_years: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrega score, riesgo, semaforo, causas y recomendaciones por meta."""
    by_id: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in all_years:
        meta_id = _text(row.get("id_meta"))
        if meta_id:
            by_id[meta_id].append(row)

    enriched: List[Dict[str, Any]] = []
    today = dt.date.today()

    for meta in consolidado:
        meta_id = _text(meta.get("id_meta"))
        historico = by_id.get(meta_id, [meta])

        avance = round(_safe_float(meta.get("avance_fisico_pct")), 1)
        financiero = round(_safe_float(meta.get("ejec_fin_pct")), 1)
        tendencia, delta_tendencia = _trend(historico)
        ultima = _ultima_actualizacion(meta, historico)
        dias_sin_actualizacion = (today - ultima).days if ultima else None

        done = _is_done(meta, avance)
        risk_level, gap_tiempo, expected, risk_reason = _risk(
            avance=avance,
            is_done=done,
            tendencia=tendencia,
            dias_sin_actualizacion=dias_sin_actualizacion,
        )

        score, component_scores = _score(
            avance=avance,
            financiero=financiero,
            gap_tiempo=gap_tiempo,
            tendencia=tendencia,
            dias_sin_actualizacion=dias_sin_actualizacion,
        )

        estado_calc = _estado(meta, avance, risk_level)
        semaforo = _semaforo(risk_level, score)
        criticidad_valor, criticidad_label = _criticidad(meta)

        causes = _delay_causes(
            meta=meta,
            estado_meta=estado_calc,
            gap_tiempo=gap_tiempo,
            tendencia=tendencia,
            dias_sin_actualizacion=dias_sin_actualizacion,
            criticidad=criticidad_label,
        )
        recs = _meta_recommendations(
            meta=meta,
            estado_meta=estado_calc,
            risk_level=risk_level,
            tendencia=tendencia,
            dias_sin_actualizacion=dias_sin_actualizacion,
            criticidad=criticidad_label,
        )

        if estado_calc == "Cumplida":
            indice_rezago = 0.0
        else:
            risk_weight = {"ninguno": 0.0, "bajo": 8.0, "medio": 16.0, "alto": 24.0}.get(risk_level, 12.0)
            criticidad_weight = {"baja": 0.0, "media": 6.0, "alta": 12.0}.get(criticidad_label, 0.0)
            stale_weight = 8.0 if (dias_sin_actualizacion is None or dias_sin_actualizacion > UPDATE_STALE_WARNING_DAYS) else 0.0
            indice_rezago = round((100.0 - score) + gap_tiempo + risk_weight + criticidad_weight + stale_weight, 1)

        es_rezagada = (
            estado_calc != "Cumplida"
            and (
                risk_level in ("alto", "medio")
                or score < 55
                or tendencia == "empeorando"
                or indice_rezago >= 45
            )
        )

        resumen_rezago = "; ".join(cause["detalle"] for cause in causes[:2])

        enriched.append(
            {
                **meta,
                "estado_raw": _text(meta.get("estado")),
                "estado": estado_calc,
                "score": score,
                "score_componentes": component_scores,
                "semaforo": semaforo,
                "riesgo_nivel": risk_level,
                "riesgo_brecha": gap_tiempo,
                "avance_esperado_pct": round(expected, 1),
                "riesgo_regla_explicacion": risk_reason,
                "tendencia": tendencia,
                "tendencia_delta": delta_tendencia,
                "criticidad_valor": criticidad_valor,
                "criticidad": criticidad_label,
                "causas_rezago": causes,
                "recomendaciones": recs,
                "indice_rezago": indice_rezago,
                "es_rezagada": es_rezagada,
                "resumen_rezago": resumen_rezago,
                "ultima_actualizacion": _iso_date(ultima),
                "dias_sin_actualizacion": dias_sin_actualizacion,
                "historico": [_sanitize_historico_row(row) for row in historico],
            }
        )

    return enriched


def compute_kpis(metas: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(metas)
    if total == 0:
        return {
            "total": 0,
            "cumplidas": 0,
            "en_curso": 0,
            "no_iniciadas": 0,
            "en_riesgo": 0,
            "avance_prom": 0.0,
            "fin_prom": 0.0,
            "score_prom": 0.0,
            "pct_tiempo": PCT_TIEMPO,
            "actualizadas_45d": 0,
            "desactualizadas": 0,
            "presup_asig": 0.0,
            "presup_ejec": 0.0,
        }

    cumplidas = sum(1 for meta in metas if meta.get("estado") == "Cumplida")
    en_curso = sum(1 for meta in metas if meta.get("estado") == "En curso")
    no_iniciadas = sum(1 for meta in metas if meta.get("estado") == "No iniciada")
    en_riesgo = sum(1 for meta in metas if meta.get("estado") == "En riesgo")
    avance_prom = sum(_safe_float(meta.get("avance_fisico_pct")) for meta in metas) / total
    fin_prom = sum(_safe_float(meta.get("ejec_fin_pct")) for meta in metas) / total
    score_prom = sum(_safe_float(meta.get("score")) for meta in metas) / total

    actualizadas_45d = sum(
        1
        for meta in metas
        if meta.get("dias_sin_actualizacion") is not None
        and meta.get("dias_sin_actualizacion") <= UPDATE_STALE_WARNING_DAYS
    )
    desactualizadas = total - actualizadas_45d
    presup_asig = sum(_safe_float(meta.get("presupuesto_asig")) for meta in metas)
    presup_ejec = sum(_safe_float(meta.get("presupuesto_ejec")) for meta in metas)

    return {
        "total": total,
        "cumplidas": cumplidas,
        "en_curso": en_curso,
        "no_iniciadas": no_iniciadas,
        "en_riesgo": en_riesgo,
        "avance_prom": round(avance_prom, 1),
        "fin_prom": round(fin_prom, 1),
        "score_prom": round(score_prom, 1),
        "pct_tiempo": round(PCT_TIEMPO, 1),
        "actualizadas_45d": actualizadas_45d,
        "desactualizadas": desactualizadas,
        "presup_asig": round(presup_asig, 0),
        "presup_ejec": round(presup_ejec, 0),
    }


def ranking_secretarias(metas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for meta in metas:
        grouped[_text(meta.get("secretaria") or "Sin asignar")].append(meta)

    ranking: List[Dict[str, Any]] = []
    for secretaria, rows in grouped.items():
        n = len(rows)
        score_avg = sum(_safe_float(item.get("score")) for item in rows) / max(1, n)
        avance_avg = sum(_safe_float(item.get("avance_fisico_pct")) for item in rows) / max(1, n)
        riesgo_count = sum(1 for item in rows if item.get("riesgo_nivel") in ("alto", "medio"))
        no_iniciadas = sum(1 for item in rows if item.get("estado") == "No iniciada")
        desactualizadas = sum(
            1
            for item in rows
            if item.get("dias_sin_actualizacion") is None
            or item.get("dias_sin_actualizacion") > UPDATE_STALE_WARNING_DAYS
        )

        recomendacion = "Mantener ejecucion y control mensual"
        if riesgo_count > 0:
            recomendacion = "Activar plan de choque y mesa tecnica de seguimiento"
        elif no_iniciadas > 0:
            recomendacion = "Priorizar plan de arranque para metas sin inicio"
        elif desactualizadas > 0:
            recomendacion = "Actualizar reportes y evidencias antes del siguiente corte"

        ranking.append(
            {
                "secretaria": secretaria,
                "total": n,
                "score_avg": round(score_avg, 1),
                "avance_avg": round(avance_avg, 1),
                "cumplidas": sum(1 for item in rows if item.get("estado") == "Cumplida"),
                "en_riesgo": riesgo_count,
                "no_iniciadas": no_iniciadas,
                "desactualizadas": desactualizadas,
                "recomendacion": recomendacion,
            }
        )

    ranking.sort(key=lambda row: (row["score_avg"], -row["en_riesgo"]), reverse=True)
    return ranking


def top_rezagadas(metas: List[Dict[str, Any]], n: int = 15) -> List[Dict[str, Any]]:
    candidates = [meta for meta in metas if meta.get("estado") != "Cumplida"]
    candidates.sort(
        key=lambda meta: (_safe_float(meta.get("indice_rezago")), -_safe_float(meta.get("score"))),
        reverse=True,
    )
    return candidates[: max(1, n)]


def _build_evolution(all_years: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    by_period: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    period_order: Dict[str, dt.date] = {}

    for row in all_years:
        row_date = _parse_date(row.get("fecha_actualizacion") or row.get("fecha_registro"))
        label = ""
        if row_date:
            label = row_date.strftime("%Y-%m")
            period_order[label] = dt.date(row_date.year, row_date.month, 1)
        else:
            year = row.get("ano")
            if isinstance(year, (int, float)) and int(year) == year:
                y = int(year)
                label = str(y)
                period_order[label] = dt.date(y, 12, 1)
        if label:
            by_period[label].append(row)

    if len(by_period) < 2:
        by_period.clear()
        period_order.clear()
        for row in all_years:
            year = row.get("ano")
            if isinstance(year, (int, float)) and int(year) == year:
                label = str(int(year))
                by_period[label].append(row)
                period_order[label] = dt.date(int(year), 12, 1)

    if not by_period:
        return {"labels": ["2024", "2025"], "avance": [0.0, 0.0], "fin": [0.0, 0.0]}

    labels = sorted(by_period.keys(), key=lambda key: period_order.get(key, dt.date(2100, 1, 1)))
    avance = []
    fin = []
    for label in labels:
        rows = by_period[label]
        avance.append(round(sum(_safe_float(item.get("avance_fisico_pct")) for item in rows) / max(1, len(rows)), 1))
        fin.append(round(sum(_safe_float(item.get("ejec_fin_pct")) for item in rows) / max(1, len(rows)), 1))
    return {"labels": labels, "avance": avance, "fin": fin}


def charts_data(metas: List[Dict[str, Any]], all_years: List[Dict[str, Any]]) -> Dict[str, Any]:
    estados_labels = ["Cumplida", "En curso", "No iniciada", "En riesgo"]
    estado_counts = {label: 0 for label in estados_labels}
    for meta in metas:
        label = meta.get("estado")
        if label in estado_counts:
            estado_counts[label] += 1

    ranking = ranking_secretarias(metas)[:10]
    by_eje: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for meta in metas:
        by_eje[_text(meta.get("eje") or "Sin eje")].append(meta)

    eje_rows = []
    for eje, rows in by_eje.items():
        eje_rows.append(
            {
                "eje": eje,
                "avance": round(sum(_safe_float(item.get("avance_fisico_pct")) for item in rows) / max(1, len(rows)), 1),
                "score": round(sum(_safe_float(item.get("score")) for item in rows) / max(1, len(rows)), 1),
                "total": len(rows),
            }
        )
    eje_rows.sort(key=lambda item: item["total"], reverse=True)
    eje_rows = eje_rows[:8]

    rezagadas = top_rezagadas(metas, 10)

    return {
        "distribucion": {"labels": estados_labels, "data": [estado_counts[label] for label in estados_labels]},
        "ranking_secretarias": {
            "labels": [row["secretaria"] for row in ranking],
            "score": [row["score_avg"] for row in ranking],
            "avance": [row["avance_avg"] for row in ranking],
        },
        "evolucion": _build_evolution(all_years),
        "por_eje": {
            "labels": [row["eje"] for row in eje_rows],
            "avance": [row["avance"] for row in eje_rows],
            "score": [row["score"] for row in eje_rows],
        },
        "top_rezagadas": [
            {
                "id_meta": row.get("id_meta"),
                "meta_producto": row.get("meta_producto"),
                "secretaria": row.get("secretaria"),
                "avance_fisico_pct": round(_safe_float(row.get("avance_fisico_pct")), 1),
                "score": round(_safe_float(row.get("score")), 1),
                "semaforo": row.get("semaforo"),
                "resumen_rezago": row.get("resumen_rezago"),
            }
            for row in rezagadas
        ],
        "pct_tiempo": round(PCT_TIEMPO, 1),
    }


def recomendaciones_generales(metas: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    kpis = compute_kpis(metas)
    if kpis["total"] == 0:
        return []

    recs: List[Dict[str, str]] = []
    if kpis["no_iniciadas"] > 0 and PCT_TIEMPO >= 20:
        recs.append(
            {
                "nivel": "plan",
                "prioridad": "alta",
                "icono": "bi-play-circle-fill",
                "titulo": f"Activar {kpis['no_iniciadas']} metas no iniciadas",
                "detalle": "Instruccion ejecutiva con responsables, cronograma minimo y control quincenal.",
            }
        )
    if kpis["en_riesgo"] > 0:
        recs.append(
            {
                "nivel": "plan",
                "prioridad": "alta",
                "icono": "bi-shield-exclamation",
                "titulo": f"Intervenir {kpis['en_riesgo']} metas en riesgo",
                "detalle": "Convocar comite de seguimiento y aprobar acciones correctivas con fechas.",
            }
        )
    if kpis["desactualizadas"] > 0:
        recs.append(
            {
                "nivel": "plan",
                "prioridad": "media",
                "icono": "bi-calendar-check",
                "titulo": f"Regularizar {kpis['desactualizadas']} metas desactualizadas",
                "detalle": "Aplicar calendario de reporte mensual y validacion de calidad de datos.",
            }
        )

    sin_evidencias = sum(
        1
        for meta in metas
        if _safe_float(meta.get("avance_fisico_pct")) > 0 and int(_safe_float(meta.get("evidencias_count"), 0)) == 0
    )
    if sin_evidencias > 0:
        recs.append(
            {
                "nivel": "plan",
                "prioridad": "media",
                "icono": "bi-images",
                "titulo": f"Estandarizar evidencias en {sin_evidencias} metas",
                "detalle": "Definir formato institucional de evidencias y exigir carga por corte.",
            }
        )

    if kpis["score_prom"] < 60:
        recs.append(
            {
                "nivel": "plan",
                "prioridad": "media",
                "icono": "bi-graph-up-arrow",
                "titulo": "Reforzar rendimiento global del plan",
                "detalle": (
                    f"Score promedio {kpis['score_prom']:.1f}/100 con "
                    f"{kpis['pct_tiempo']:.1f}% del tiempo transcurrido. Ajustar POA y metas intermedias."
                ),
            }
        )
    return recs[:5]


def plan_choque_secretaria(secretaria: str, metas: List[Dict[str, Any]]) -> Dict[str, Any]:
    sec = _text(secretaria)
    rows = [meta for meta in metas if _text(meta.get("secretaria")) == sec]
    if not rows:
        return {"secretaria": sec, "total": 0, "score_prom": 0.0, "en_riesgo": 0, "no_iniciadas": 0, "acciones": [], "metas_prioritarias": []}

    score_prom = round(sum(_safe_float(meta.get("score")) for meta in rows) / len(rows), 1)
    en_riesgo = sum(1 for meta in rows if meta.get("riesgo_nivel") in ("alto", "medio"))
    no_iniciadas = sum(1 for meta in rows if meta.get("estado") == "No iniciada")
    desactualizadas = sum(
        1
        for meta in rows
        if meta.get("dias_sin_actualizacion") is None
        or meta.get("dias_sin_actualizacion") > UPDATE_STALE_WARNING_DAYS
    )

    acciones: List[Dict[str, str]] = []
    if no_iniciadas > 0:
        acciones.append({"prioridad": "alta", "accion": f"Arrancar {no_iniciadas} meta(s) no iniciada(s) con lider y cronograma.", "plazo": "15 dias"})
    if en_riesgo > 0:
        acciones.append({"prioridad": "alta", "accion": f"Plan de recuperacion para {en_riesgo} meta(s) en riesgo con seguimiento semanal.", "plazo": "Inmediato"})
    if desactualizadas > 0:
        acciones.append({"prioridad": "media", "accion": f"Actualizar registros y evidencias de {desactualizadas} meta(s).", "plazo": "10 dias"})
    if score_prom < 60:
        acciones.append({"prioridad": "media", "accion": "Mesa tecnica con Planeacion para ajustar hitos y cuellos de botella.", "plazo": "20 dias"})

    metas_prioritarias = top_rezagadas(rows, 6)
    return {
        "secretaria": sec,
        "total": len(rows),
        "score_prom": score_prom,
        "en_riesgo": en_riesgo,
        "no_iniciadas": no_iniciadas,
        "desactualizadas": desactualizadas,
        "acciones": acciones,
        "metas_prioritarias": [
            {
                "id_meta": meta.get("id_meta"),
                "meta_producto": meta.get("meta_producto"),
                "score": meta.get("score"),
                "avance_fisico_pct": meta.get("avance_fisico_pct"),
                "resumen_rezago": meta.get("resumen_rezago"),
            }
            for meta in metas_prioritarias
        ],
    }
