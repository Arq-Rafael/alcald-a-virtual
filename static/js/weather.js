/**
 * weather.js — Widget de clima + Módulo Clima Supatá
 * Uso:
 *  - En base.html: WeatherWidget.init()  (widget del sidebar + dashboard banner)
 *  - En clima.html: WeatherModule.init() (página completa)
 */

'use strict';

// ── Constantes ────────────────────────────────────────────────────────────────
const WEATHER_REFRESH_MS = 15 * 60 * 1000; // 15 min

// ── Helpers ───────────────────────────────────────────────────────────────────

function _fmt_time(iso) {
  // iso = "2026-02-25T14:00" o "2026-02-25T14:00:00"
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', hour12: false });
  } catch { return iso; }
}

function _fmt_updated(iso) {
  try {
    const d = new Date(iso);
    return 'Actualizado: ' + d.toLocaleString('es-CO', {
      day: '2-digit', month: 'short',
      hour: '2-digit', minute: '2-digit', hour12: false
    });
  } catch { return ''; }
}

function _wind_dir_arrow(deg) {
  const dirs = ['N','NE','E','SE','S','SO','O','NO'];
  return dirs[Math.round(deg / 45) % 8] || '';
}

// ── Caché local (evita refetch innecesario dentro de la misma pestaña) ────────
let _cachedCurrent  = null;
let _cachedForecast = null;
let _cachedAlerts   = null;
let _lastFetchTs    = 0;

async function _fetchCurrent(force = false) {
  if (!force && _cachedCurrent && (Date.now() - _lastFetchTs < WEATHER_REFRESH_MS)) {
    return _cachedCurrent;
  }
  try {
    const r = await fetch('/api/weather/current');
    if (!r.ok) return null;
    _cachedCurrent = await r.json();
    _lastFetchTs = Date.now();
    return _cachedCurrent;
  } catch { return null; }
}

async function _fetchForecast(force = false) {
  if (!force && _cachedForecast && (Date.now() - _lastFetchTs < WEATHER_REFRESH_MS)) {
    return _cachedForecast;
  }
  try {
    const r = await fetch('/api/weather/forecast');
    if (!r.ok) return null;
    _cachedForecast = await r.json();
    return _cachedForecast;
  } catch { return null; }
}

async function _fetchAlerts() {
  try {
    const r = await fetch('/api/weather/alerts');
    if (!r.ok) return null;
    _cachedAlerts = await r.json();
    return _cachedAlerts;
  } catch { return null; }
}

// ═══════════════════════════════════════════════════════════════════════════════
//  WeatherWidget — widget compacto en dashboard banner + sidebar bubble
// ═══════════════════════════════════════════════════════════════════════════════

window.WeatherWidget = {
  _timer: null,

  async init() {
    await this.refresh();
    this._timer = setInterval(() => this.refresh(), WEATHER_REFRESH_MS);
  },

  async refresh() {
    const data = await _fetchCurrent();
    if (!data) return;
    this._updateDashboardCard(data);
    this._updateSidebarBubble(data);
  },

  /** Actualiza la tarjeta pequeña en el banner del dashboard */
  _updateDashboardCard(d) {
    const card = document.querySelector('.db-weather-card');
    if (!card) return;

    const iconEl = card.querySelector('i');
    const tempEl = card.querySelector('.temp');
    const descEl = card.querySelector('.desc');

    if (iconEl) iconEl.className = `bi ${d.icon}`;
    if (tempEl) tempEl.textContent = `${d.temp}°C`;
    if (descEl) descEl.textContent = d.city || 'Supatá';
  },

  /** Actualiza el bubble modal del sidebar */
  _updateSidebarBubble(d) {
    // Header del bubble (temperatura + descripción)
    const h3 = document.querySelector('#weatherBubble .weather-bubble-header h3');
    const p  = document.querySelector('#weatherBubble .weather-bubble-header p');
    if (h3) h3.textContent = `${d.temp}°C`;
    if (p)  p.textContent  = d.description;

    // ícono en bubble
    const bubbleIcon = document.querySelector('#weatherBubble .weather-bubble-header i');
    if (bubbleIcon) bubbleIcon.className = `bi ${d.icon}`;

    // Items de detalle
    const items = document.querySelectorAll('#weatherBubble .weather-detail-item span');
    if (items.length >= 3) {
      items[0].textContent = `Humedad: ${d.humidity}%`;
      items[1].textContent = `Viento: ${d.wind_speed} km/h ${_wind_dir_arrow(d.wind_dir)}`;
      items[2].textContent = `Sensación: ${d.feels_like}°C`;
    }

    // Enlace "Ver más" si existe
    const moreLink = document.querySelector('#weatherBubble .weather-bubble-more');
    if (moreLink) moreLink.href = '/clima';
  }
};

// ═══════════════════════════════════════════════════════════════════════════════
//  WeatherModule — página completa /clima
// ═══════════════════════════════════════════════════════════════════════════════

window.WeatherModule = {
  _timer: null,

  async init() {
    await this.loadAll();
    this._timer = setInterval(() => this.loadAll(), WEATHER_REFRESH_MS);
  },

  async loadAll() {
    const [current, forecast, alerts] = await Promise.all([
      _fetchCurrent(true),
      _fetchForecast(true),
      _fetchAlerts(),
    ]);

    this._renderBanner(current);
    this._renderKpis(current);
    this._renderHourly(forecast);
    this._renderDaily(forecast);
    this._renderRecommendations(alerts);
    this._renderResources(alerts);
  },

  // ── Banner ──────────────────────────────────────────────────────────────────
  _renderBanner(d) {
    if (!d) {
      document.getElementById('clTempBig').textContent = '—';
      document.getElementById('clTempDesc').textContent = 'Sin datos';
      return;
    }
    document.getElementById('clBannerEmoji').textContent = d.emoji || '⛅';
    document.getElementById('clTempBig').textContent     = `${d.temp}°C`;
    document.getElementById('clTempDesc').textContent    = d.description;
    document.getElementById('clUpdatedAt').textContent   = _fmt_updated(d.updated_at);

    if (d.cached) {
      const badge = document.createElement('span');
      badge.className   = 'cl-cache-badge';
      badge.textContent = '⚠ caché';
      document.getElementById('clUpdatedAt').appendChild(badge);
    }
  },

  // ── KPIs actuales ───────────────────────────────────────────────────────────
  _renderKpis(d) {
    const row = document.getElementById('clKpiRow');
    if (!row) return;

    if (!d) {
      row.innerHTML = '<div class="cl-error"><i class="bi bi-exclamation-triangle-fill"></i> No hay datos disponibles.</div>';
      return;
    }

    const items = [
      { icon: 'bi-thermometer-half', val: `${d.feels_like}°C`,       label: 'Sensación térmica' },
      { icon: 'bi-droplet-fill',     val: `${d.humidity}%`,           label: 'Humedad relativa' },
      { icon: 'bi-wind',             val: `${d.wind_speed} km/h ${_wind_dir_arrow(d.wind_dir)}`, label: 'Viento' },
      { icon: 'bi-cloud-rain-fill',  val: `${d.precip} mm`,           label: 'Precipitación' },
      { icon: 'bi-speedometer2',     val: `${d.pressure} hPa`,        label: 'Presión atmosférica' },
      { icon: 'bi-eye-fill',         val: `${d.visibility} km`,       label: 'Visibilidad' },
    ];

    row.innerHTML = items.map(item => `
      <div class="cl-kpi">
        <i class="bi ${item.icon} cl-kpi-icon"></i>
        <div class="cl-kpi-val">${item.val}</div>
        <div class="cl-kpi-label">${item.label}</div>
      </div>
    `).join('');
  },

  // ── Pronóstico horario ──────────────────────────────────────────────────────
  _renderHourly(forecast) {
    const scroll = document.getElementById('clHourlyScroll');
    if (!scroll) return;

    if (!forecast || !forecast.hourly || !forecast.hourly.length) {
      scroll.innerHTML = '<div class="cl-error"><i class="bi bi-exclamation-triangle-fill"></i> Sin pronóstico horario.</div>';
      return;
    }

    const nowHour = new Date().getHours();

    scroll.innerHTML = forecast.hourly.map((h, idx) => {
      const hTime = new Date(h.time);
      const isNow = Math.abs(hTime.getHours() - nowHour) < 1 && idx < 4;
      const ppHtml = h.precip_prob > 0
        ? `<div class="cl-hour-pp">💧 ${h.precip_prob}%</div>`
        : '';
      return `
        <div class="cl-hour-card${isNow ? ' now' : ''}">
          <div class="cl-hour-time">${isNow ? 'Ahora' : _fmt_time(h.time)}</div>
          <div class="cl-hour-icon"><i class="bi ${h.icon}"></i></div>
          <div class="cl-hour-temp">${h.temp ?? '—'}°C</div>
          ${ppHtml}
        </div>
      `;
    }).join('');
  },

  // ── Pronóstico diario ───────────────────────────────────────────────────────
  _renderDaily(forecast) {
    const grid = document.getElementById('clDailyGrid');
    if (!grid) return;

    if (!forecast || !forecast.daily || !forecast.daily.length) {
      grid.innerHTML = '<div class="cl-error"><i class="bi bi-exclamation-triangle-fill"></i> Sin pronóstico semanal.</div>';
      return;
    }

    const todayStr = new Date().toISOString().slice(0, 10);

    grid.innerHTML = forecast.daily.map((d, idx) => {
      const isToday = d.date === todayStr;
      const rainHtml = d.precip_sum > 0
        ? `<div class="cl-day-rain">💧 ${d.precip_sum} mm</div>`
        : '';
      return `
        <div class="cl-day-card${isToday ? ' today' : ''}">
          <div class="cl-day-name">${isToday ? 'Hoy' : d.day_name}</div>
          <div class="cl-day-icon"><i class="bi ${d.icon}" style="color:#1565c0;"></i></div>
          <div class="cl-day-desc">${d.description}</div>
          <div class="cl-day-temps">
            <span class="cl-day-max">${d.temp_max ?? '—'}°</span>
            <span style="color:#cbd5e1;">/</span>
            <span class="cl-day-min">${d.temp_min ?? '—'}°</span>
          </div>
          ${rainHtml}
        </div>
      `;
    }).join('');
  },

  // ── Recomendaciones ─────────────────────────────────────────────────────────
  _renderRecommendations(alerts) {
    const list = document.getElementById('clRecsList');
    if (!list) return;

    const recs = alerts && alerts.recommendations ? alerts.recommendations : [];

    if (!recs.length) {
      list.innerHTML = `
        <div class="cl-rec-item">
          <i class="bi bi-check-circle-fill cl-rec-icon" style="color:#22c55e;"></i>
          Sin alertas operativas en este momento.
        </div>`;
      return;
    }

    list.innerHTML = recs.map(r => `
      <div class="cl-rec-item">
        <i class="bi ${r.icon} cl-rec-icon" style="color:${r.color};"></i>
        ${r.text}
      </div>
    `).join('');
  },

  // ── Recursos IDEAM ──────────────────────────────────────────────────────────
  _renderResources(alerts) {
    const grid = document.getElementById('clResourcesGrid');
    if (!grid) return;

    const resources = alerts && alerts.resources ? alerts.resources : [];

    if (!resources.length) {
      grid.innerHTML = '<p class="text-muted small">No hay recursos disponibles.</p>';
      return;
    }

    grid.innerHTML = resources.map(r => `
      <a href="${r.url}" target="_blank" rel="noopener noreferrer" class="cl-resource-card">
        <i class="bi ${r.icon} cl-resource-icon"></i>
        <div>
          <div class="cl-resource-title">${r.title}</div>
          <div class="cl-resource-desc">${r.desc}</div>
        </div>
      </a>
    `).join('');
  },
};
