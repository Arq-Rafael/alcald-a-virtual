"""
Servicio de clima para Supatá, Cundinamarca.
Fuente: Open-Meteo API (gratuita, sin clave API).
Coordenadas Supatá: lat=5.0581, lon=-74.4661, alt=1930 m

Caché en memoria con TTL de 15 minutos.
"""

import threading
import time
import logging
import urllib.request
import json

logger = logging.getLogger(__name__)

# ── Coordenadas Supatá ─────────────────────────────────────────────────────────
LAT = 5.0581
LON = -74.4661

# ── Caché en memoria ──────────────────────────────────────────────────────────
_cache_lock = threading.Lock()
_cache = {
    'current':  {'data': None, 'ts': 0},
    'forecast': {'data': None, 'ts': 0},
}
CACHE_TTL = 15 * 60  # 15 minutos

# ── Mapeo de WMO weather codes → descripción + icono Bootstrap Icons ─────────
_WMO_MAP = {
    0:  ('Cielo despejado',          'bi-sun-fill',              '☀️'),
    1:  ('Mayormente despejado',      'bi-cloud-sun-fill',        '🌤️'),
    2:  ('Parcialmente nublado',      'bi-cloud-sun-fill',        '⛅'),
    3:  ('Nublado',                   'bi-cloud-fill',            '☁️'),
    45: ('Niebla',                    'bi-cloud-haze2-fill',      '🌫️'),
    48: ('Niebla con escarcha',       'bi-cloud-haze2-fill',      '🌫️'),
    51: ('Llovizna ligera',           'bi-cloud-drizzle-fill',    '🌦️'),
    53: ('Llovizna moderada',         'bi-cloud-drizzle-fill',    '🌦️'),
    55: ('Llovizna intensa',          'bi-cloud-drizzle-fill',    '🌦️'),
    61: ('Lluvia ligera',             'bi-cloud-rain-fill',       '🌧️'),
    63: ('Lluvia moderada',           'bi-cloud-rain-fill',       '🌧️'),
    65: ('Lluvia intensa',            'bi-cloud-rain-heavy-fill', '🌧️'),
    71: ('Nieve ligera',              'bi-cloud-snow-fill',       '🌨️'),
    73: ('Nieve moderada',            'bi-cloud-snow-fill',       '❄️'),
    75: ('Nieve intensa',             'bi-cloud-snow-fill',       '❄️'),
    77: ('Granizo fino',              'bi-cloud-sleet-fill',      '🌨️'),
    80: ('Chubascos ligeros',         'bi-cloud-rain-fill',       '🌦️'),
    81: ('Chubascos moderados',       'bi-cloud-rain-fill',       '🌧️'),
    82: ('Chubascos violentos',       'bi-cloud-rain-heavy-fill', '⛈️'),
    85: ('Chubascos de nieve',        'bi-cloud-snow-fill',       '🌨️'),
    86: ('Chubascos de nieve fuertes','bi-cloud-snow-fill',       '❄️'),
    95: ('Tormenta',                  'bi-cloud-lightning-fill',  '⛈️'),
    96: ('Tormenta con granizo',      'bi-cloud-lightning-rain-fill','⛈️'),
    99: ('Tormenta con granizo fuerte','bi-cloud-lightning-rain-fill','🌩️'),
}

def _decode_wmo(code):
    """Retorna (descripción, icono_bi, emoji) para un código WMO."""
    return _WMO_MAP.get(code, ('Desconocido', 'bi-question-circle', '❓'))


def _fetch_url(url):
    """GET simple con timeout. Retorna dict o None."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'AlcaldiaVirtualSupata/1.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode())
    except Exception as exc:
        logger.warning(f'[WEATHER] Error fetch {url}: {exc}')
        return None


def _is_stale(key):
    return (time.time() - _cache[key]['ts']) > CACHE_TTL


# ── API pública ───────────────────────────────────────────────────────────────

def get_current():
    """
    Retorna dict con datos actuales del clima.
    Usa caché 15 min. Si falla la API y hay caché viejo, lo devuelve con
    `cached=True`. Si no hay nada, retorna None.
    """
    with _cache_lock:
        if not _is_stale('current') and _cache['current']['data']:
            return dict(_cache['current']['data'], cached=False)

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
        f"weather_code,wind_speed_10m,wind_direction_10m,precipitation,"
        f"surface_pressure,visibility"
        f"&wind_speed_unit=kmh&timezone=America%2FBogota"
    )

    raw = _fetch_url(url)
    if raw and 'current' in raw:
        c = raw['current']
        code = c.get('weather_code', 0)
        desc, icon, emoji = _decode_wmo(code)

        data = {
            'temp':        round(c.get('temperature_2m', 0)),
            'feels_like':  round(c.get('apparent_temperature', 0)),
            'humidity':    round(c.get('relative_humidity_2m', 0)),
            'wind_speed':  round(c.get('wind_speed_10m', 0)),
            'wind_dir':    round(c.get('wind_direction_10m', 0)),
            'precip':      round(c.get('precipitation', 0), 1),
            'pressure':    round(c.get('surface_pressure', 0)),
            'visibility':  round(c.get('visibility', 0) / 1000, 1),  # m → km
            'weather_code': code,
            'description': desc,
            'icon':        icon,
            'emoji':       emoji,
            'updated_at':  c.get('time', ''),
            'city':        'Supatá',
            'cached':      False,
        }
        with _cache_lock:
            _cache['current'] = {'data': data, 'ts': time.time()}
        return data

    # Fallback: caché viejo
    with _cache_lock:
        if _cache['current']['data']:
            logger.warning('[WEATHER] Usando caché de clima antiguo')
            return dict(_cache['current']['data'], cached=True)

    logger.error('[WEATHER] Sin datos de clima disponibles')
    return None


def get_forecast():
    """
    Retorna dict con:
    - hourly: lista próximas 24 h (temp, weather_code, precip_prob)
    - daily:  lista próximos 7 días (min, max, weather_code, precip_sum)
    """
    with _cache_lock:
        if not _is_stale('forecast') and _cache['forecast']['data']:
            return dict(_cache['forecast']['data'], cached=False)

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        f"&hourly=temperature_2m,weather_code,precipitation_probability"
        f"&daily=temperature_2m_max,temperature_2m_min,weather_code,"
        f"precipitation_sum,wind_speed_10m_max"
        f"&wind_speed_unit=kmh&timezone=America%2FBogota&forecast_days=7"
    )

    raw = _fetch_url(url)
    if raw:
        # Hourly: próximas 24 entradas
        h = raw.get('hourly', {})
        times_h    = h.get('time', [])
        temps_h    = h.get('temperature_2m', [])
        codes_h    = h.get('weather_code', [])
        precip_p_h = h.get('precipitation_probability', [])

        hourly = []
        for i in range(min(24, len(times_h))):
            code = codes_h[i] if i < len(codes_h) else 0
            desc, icon, emoji = _decode_wmo(code)
            hourly.append({
                'time':       times_h[i],
                'temp':       round(temps_h[i]) if i < len(temps_h) else None,
                'icon':       icon,
                'emoji':      emoji,
                'precip_prob': precip_p_h[i] if i < len(precip_p_h) else 0,
            })

        # Daily: 7 días
        d = raw.get('daily', {})
        times_d   = d.get('time', [])
        max_d     = d.get('temperature_2m_max', [])
        min_d     = d.get('temperature_2m_min', [])
        codes_d   = d.get('weather_code', [])
        precip_d  = d.get('precipitation_sum', [])
        wind_d    = d.get('wind_speed_10m_max', [])

        DAYS_ES = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

        daily = []
        for i in range(min(7, len(times_d))):
            code = codes_d[i] if i < len(codes_d) else 0
            desc, icon, emoji = _decode_wmo(code)
            date_str = times_d[i]  # YYYY-MM-DD
            try:
                import datetime
                dt = datetime.date.fromisoformat(date_str)
                day_name = DAYS_ES[dt.weekday()]
            except Exception:
                day_name = date_str
            daily.append({
                'date':       date_str,
                'day_name':   day_name,
                'temp_max':   round(max_d[i]) if i < len(max_d) else None,
                'temp_min':   round(min_d[i]) if i < len(min_d) else None,
                'icon':       icon,
                'emoji':      emoji,
                'description': desc,
                'precip_sum': round(precip_d[i], 1) if i < len(precip_d) else 0,
                'wind_max':   round(wind_d[i]) if i < len(wind_d) else 0,
            })

        data = {'hourly': hourly, 'daily': daily, 'cached': False}
        with _cache_lock:
            _cache['forecast'] = {'data': data, 'ts': time.time()}
        return data

    # Fallback
    with _cache_lock:
        if _cache['forecast']['data']:
            return dict(_cache['forecast']['data'], cached=True)

    return None


def get_recommendations(current_data):
    """Genera recomendaciones operativas basadas en los datos del clima."""
    if not current_data:
        return []

    recs = []
    code  = current_data.get('weather_code', 0)
    temp  = current_data.get('temp', 20)
    wind  = current_data.get('wind_speed', 0)
    hum   = current_data.get('humidity', 50)
    prec  = current_data.get('precip', 0)

    # Lluvia
    if prec > 5 or code in (65, 82, 86, 95, 96, 99):
        recs.append({'icon': 'bi-exclamation-triangle-fill', 'color': '#ef4444',
                     'text': 'Lluvias intensas: suspender actividades de campo. Revisar drenajes municipales.'})
    elif prec > 0 or code in (51, 53, 61, 63, 80, 81):
        recs.append({'icon': 'bi-cloud-rain-fill', 'color': '#f59e0b',
                     'text': 'Llovizna o lluvia ligera: precaución en vías rurales. Llevar equipo impermeable.'})

    # Temperatura
    if temp >= 28:
        recs.append({'icon': 'bi-thermometer-high', 'color': '#ef4444',
                     'text': 'Temperatura alta: hidratación constante para personal en campo. Evitar exposición solar en horas pico (12-15 h).'})
    elif temp <= 10:
        recs.append({'icon': 'bi-thermometer-low', 'color': '#3b82f6',
                     'text': 'Temperatura baja: protección térmica para personal en campo. Cuidado con superficies resbaladizas.'})

    # Viento
    if wind >= 40:
        recs.append({'icon': 'bi-wind', 'color': '#ef4444',
                     'text': 'Viento fuerte (≥ 40 km/h): suspender trabajo en alturas y actividades con andamiaje.'})
    elif wind >= 20:
        recs.append({'icon': 'bi-wind', 'color': '#f59e0b',
                     'text': 'Viento moderado: asegurar carpas, señalización y elementos livianos al aire libre.'})

    # Humedad
    if hum >= 85:
        recs.append({'icon': 'bi-droplet-fill', 'color': '#06b6d4',
                     'text': 'Humedad muy alta: mayor riesgo de resbalones. Revisar zonas de riesgo de deslizamiento.'})

    # Niebla
    if code in (45, 48):
        recs.append({'icon': 'bi-cloud-haze2-fill', 'color': '#6b7280',
                     'text': 'Niebla presente: reducir velocidad en vías municipales. Encender luces en vehículos.'})

    # Condiciones favorables
    if not recs and code in (0, 1, 2) and temp < 28 and wind < 20:
        recs.append({'icon': 'bi-check-circle-fill', 'color': '#22c55e',
                     'text': 'Condiciones favorables para actividades de campo y trabajo al aire libre.'})

    return recs
