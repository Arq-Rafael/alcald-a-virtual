"""Reglas de semaforo y riesgo para correo institucional."""

from datetime import datetime


DEFAULT_SLA_DAYS = {
    'derecho_peticion': 15,
    'peticion': 10,
    'queja': 8,
    'reclamo': 8,
    'solicitud': 7,
    'requerimiento': 5,
    'urgente': 2,
    'invitacion': 6,
    'informativo': 30,
    'interno': 5,
    'otro': 7,
}


def _normalize_category(category):
    return (category or 'otro').strip().lower()


def calculate_attention_status(fecha_recepcion, categoria, requiere_respuesta, urgencia):
    """
    Retorna semaforo, dias transcurridos, prioridad operativa y riesgo de vencimiento.
    """
    now = datetime.utcnow()
    if not fecha_recepcion:
        fecha_recepcion = now

    dias_transcurridos = max(0, (now - fecha_recepcion).days)

    categoria_norm = _normalize_category(categoria)
    sla_days = DEFAULT_SLA_DAYS.get(categoria_norm, DEFAULT_SLA_DAYS['otro'])

    if not requiere_respuesta:
        return {
            'semaforo': 'azul',
            'dias_transcurridos': dias_transcurridos,
            'prioridad': 'baja',
            'riesgo_vencimiento': 'sin_accion',
            'sla_dias': sla_days,
        }

    ratio = dias_transcurridos / float(max(1, sla_days))

    if ratio < 0.5:
        semaforo = 'verde'
        riesgo = 'bajo'
    elif ratio < 0.85:
        semaforo = 'amarillo'
        riesgo = 'medio'
    else:
        semaforo = 'rojo'
        riesgo = 'alto'

    urgencia_norm = (urgencia or 'media').lower()
    if urgencia_norm == 'alta' or categoria_norm in ('derecho_peticion', 'requerimiento', 'urgente'):
        prioridad = 'alta'
    elif urgencia_norm == 'baja':
        prioridad = 'baja'
    else:
        prioridad = 'media'

    return {
        'semaforo': semaforo,
        'dias_transcurridos': dias_transcurridos,
        'prioridad': prioridad,
        'riesgo_vencimiento': riesgo,
        'sla_dias': sla_days,
    }
