/* Panel lateral de expedientes — Plataforma Licencias Urbanísticas Supatá */
(function () {
  'use strict';

  /* ── CSS ─────────────────────────────────────────────────────────────── */
  var css =
    '#plt-sb-tog{position:fixed;top:50%;right:0;transform:translateY(-50%);' +
    'background:linear-gradient(135deg,#0f4c81,#1565c0);color:#fff;border:none;' +
    'padding:14px 6px;border-radius:8px 0 0 8px;cursor:pointer;z-index:9998;' +
    'font-size:9px;letter-spacing:2px;writing-mode:vertical-rl;' +
    'text-transform:uppercase;font-weight:700;font-family:Inter,sans-serif;' +
    'box-shadow:-4px 0 16px rgba(0,0,0,.35);transition:padding .2s ease;}' +
    '#plt-sb-tog:hover{padding:14px 11px;}' +

    '#plt-sb-panel{position:fixed;top:0;right:-330px;width:318px;height:100vh;' +
    'background:#0a1528;border-left:1px solid rgba(255,255,255,.1);' +
    'z-index:9999;transition:right .3s ease;display:flex;flex-direction:column;' +
    'font-family:Inter,sans-serif;box-shadow:-8px 0 32px rgba(0,0,0,.45);}' +
    '#plt-sb-panel.open{right:0;}' +

    '#plt-sb-ov{display:none;position:fixed;inset:0;' +
    'background:rgba(0,0,0,.45);z-index:9997;backdrop-filter:blur(2px);}' +
    '#plt-sb-ov.on{display:block;}' +

    '#plt-sb-hdr{padding:14px 16px 12px;border-bottom:1px solid rgba(255,255,255,.1);' +
    'display:flex;align-items:center;justify-content:space-between;flex-shrink:0;}' +
    '#plt-sb-hdr span{color:#fff;font-size:13px;font-weight:700;}' +
    '#plt-sb-close{background:none;border:1px solid rgba(255,255,255,.2);' +
    'color:rgba(255,255,255,.7);width:28px;height:28px;border-radius:6px;' +
    'cursor:pointer;font-size:18px;line-height:1;display:flex;align-items:center;justify-content:center;}' +
    '#plt-sb-close:hover{background:rgba(255,255,255,.12);color:#fff;}' +

    '#plt-sb-search{margin:10px 12px 6px;padding:8px 12px;border-radius:8px;' +
    'background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);' +
    'color:#fff;font-size:12px;outline:none;font-family:Inter,sans-serif;' +
    'width:calc(100% - 24px);box-sizing:border-box;}' +
    '#plt-sb-search::placeholder{color:rgba(255,255,255,.38);}' +
    '#plt-sb-search:focus{border-color:rgba(14,165,233,.6);}' +

    '#plt-sb-count{font-size:10px;color:rgba(255,255,255,.35);' +
    'padding:0 14px 6px;flex-shrink:0;}' +

    '#plt-sb-list{flex:1;overflow-y:auto;padding:4px 8px 16px;' +
    'scrollbar-width:thin;scrollbar-color:rgba(255,255,255,.18) transparent;}' +

    '.plt-sb-item{padding:10px 12px;border-radius:8px;cursor:pointer;' +
    'margin-bottom:4px;border:1px solid rgba(255,255,255,.06);' +
    'background:rgba(255,255,255,.03);transition:all .15s;}' +
    '.plt-sb-item:hover{background:rgba(255,255,255,.09);' +
    'border-color:rgba(14,165,233,.45);transform:translateX(-2px);}' +

    '.plt-sb-rad{font-size:10px;font-weight:700;color:#0ea5e9;' +
    'letter-spacing:.5px;margin-bottom:2px;white-space:nowrap;' +
    'overflow:hidden;text-overflow:ellipsis;}' +
    '.plt-sb-nom{font-size:12px;color:#fff;font-weight:600;' +
    'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}' +
    '.plt-sb-sub{font-size:10px;color:rgba(255,255,255,.42);' +
    'display:flex;gap:8px;margin-top:3px;align-items:center;}' +
    '.plt-sb-est{padding:1px 7px;border-radius:4px;font-size:9px;' +
    'font-weight:700;flex-shrink:0;letter-spacing:.3px;}' +
    '.plt-sb-e-radicada{background:#dbeafe;color:#1d4ed8;}' +
    '.plt-sb-e-revision{background:#fef3c7;color:#b45309;}' +
    '.plt-sb-e-subsanacion{background:#ede9fe;color:#6d28d9;}' +
    '.plt-sb-e-aprobada{background:#d1fae5;color:#065f46;}' +
    '.plt-sb-e-negada{background:#fee2e2;color:#991b1b;}' +

    '.plt-sb-loading{color:rgba(255,255,255,.38);text-align:center;' +
    'padding:36px 16px;font-size:12px;}' +

    '#plt-sb-toast{position:fixed;bottom:80px;right:24px;' +
    'background:linear-gradient(135deg,#065f46,#047857);color:#fff;' +
    'padding:11px 18px;border-radius:10px;font-size:12px;font-weight:600;' +
    'z-index:10000;transform:translateY(20px);opacity:0;' +
    'transition:all .3s ease;pointer-events:none;' +
    'box-shadow:0 6px 20px rgba(0,0,0,.4);max-width:320px;}' +
    '#plt-sb-toast.on{transform:translateY(0);opacity:1;pointer-events:auto;}' +
    '#plt-sb-toast a{color:#6ee7b7;text-decoration:underline;}';

  var styleEl = document.createElement('style');
  styleEl.textContent = css;
  document.head.appendChild(styleEl);

  /* ── DOM ─────────────────────────────────────────────────────────────── */
  var tog = document.createElement('button');
  tog.id = 'plt-sb-tog';
  tog.title = 'Ver expedientes radicados';
  tog.textContent = 'Expedientes';

  var ov = document.createElement('div');
  ov.id = 'plt-sb-ov';

  var panel = document.createElement('div');
  panel.id = 'plt-sb-panel';
  panel.innerHTML =
    '<div id="plt-sb-hdr">' +
    '  <span>📋 Expedientes</span>' +
    '  <button id="plt-sb-close" title="Cerrar">×</button>' +
    '</div>' +
    '<input id="plt-sb-search" type="text" placeholder="Buscar nombre, radicado, dirección…">' +
    '<div id="plt-sb-count"></div>' +
    '<div id="plt-sb-list"><div class="plt-sb-loading">Abriendo panel…</div></div>';

  var toastEl = document.createElement('div');
  toastEl.id = 'plt-sb-toast';

  document.body.appendChild(tog);
  document.body.appendChild(ov);
  document.body.appendChild(panel);
  document.body.appendChild(toastEl);

  var listEl   = null;
  var countEl  = null;
  var searchEl = null;
  var _rads    = null;
  var _toastTimer = null;

  /* ── Init delayed (wait for DOM) ──────────────────────────────────────── */
  function init() {
    listEl   = document.getElementById('plt-sb-list');
    countEl  = document.getElementById('plt-sb-count');
    searchEl = document.getElementById('plt-sb-search');

    document.getElementById('plt-sb-close').addEventListener('click', pltClose);
    ov.addEventListener('click', pltClose);
    tog.addEventListener('click', pltOpen);
    searchEl.addEventListener('input', function () { pltFilter(this.value); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  /* ── Abrir / cerrar ───────────────────────────────────────────────────── */
  function pltOpen() {
    panel.classList.add('open');
    ov.classList.add('on');
    if (!_rads) {
      pltLoad();
    } else {
      pltRender(_rads);
    }
  }

  function pltClose() {
    panel.classList.remove('open');
    ov.classList.remove('on');
  }

  /* ── Cargar lista desde API ───────────────────────────────────────────── */
  function pltLoad() {
    if (listEl) listEl.innerHTML = '<div class="plt-sb-loading">Cargando expedientes…</div>';
    fetch('/licencias/api/lista')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        _rads = Array.isArray(data) ? data : [];
        pltRender(_rads);
      })
      .catch(function () {
        if (listEl) listEl.innerHTML = '<div class="plt-sb-loading">Error al cargar. Verifique sesión.</div>';
      });
  }

  /* ── Filtrar ──────────────────────────────────────────────────────────── */
  function pltFilter(q) {
    if (!_rads) return;
    q = (q || '').toLowerCase().trim();
    var filtered = q ? _rads.filter(function (r) {
      return String(r.consecutivo || '').indexOf(q) > -1
        || (r.solicitante || '').toLowerCase().indexOf(q) > -1
        || (r.radicado_str || '').toLowerCase().indexOf(q) > -1
        || (r.direccion || '').toLowerCase().indexOf(q) > -1;
    }) : _rads;
    pltRender(filtered);
  }

  /* ── Renderizar lista ─────────────────────────────────────────────────── */
  var _eMap = {
    'Radicada': 'radicada', 'En revisión': 'revision',
    'Subsanación': 'subsanacion', 'Aprobada': 'aprobada', 'Negada': 'negada'
  };

  function pltRender(list) {
    if (!listEl) return;
    if (!list || !list.length) {
      listEl.innerHTML = '<div class="plt-sb-loading">Sin expedientes que mostrar</div>';
      if (countEl) countEl.textContent = '';
      return;
    }
    if (countEl) countEl.textContent = list.length + ' expediente' + (list.length !== 1 ? 's' : '');
    listEl.innerHTML = list.map(function (r) {
      var ecls = _eMap[r.estado] || 'radicada';
      var rad  = r.radicado_str || ('#' + r.consecutivo);
      var tipo = (r.tipo || '')
        .replace('Licencia de Construcción', 'Lic. Construcción')
        .replace('Licencia de Parcelación', 'Lic. Parcelación')
        .replace('Licencia de Subdivisión', 'Lic. Subdivisión')
        .replace('Reconocimiento de Edificación', 'Reconocimiento');
      return '<div class="plt-sb-item" onclick="window.pltSel(' + r.consecutivo + ')">' +
        '<div class="plt-sb-rad">' + rad + '</div>' +
        '<div class="plt-sb-nom">' + escH(r.solicitante || 'Sin nombre') + '</div>' +
        '<div class="plt-sb-sub">' +
        '<span class="plt-sb-est plt-sb-e-' + ecls + '">' + escH(r.estado || 'Radicada') + '</span>' +
        '<span>' + tipo + '</span>' +
        '</div></div>';
    }).join('');
  }

  function escH(s) {
    return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  /* ── Seleccionar radicado → cargar en la página actual ───────────────── */
  window.pltSel = function (consecutivo) {
    fetch('/licencias/api/radicado/' + consecutivo)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.error) {
          alert('No se pudo cargar el expediente: ' + data.error);
          return;
        }
        var pkg = data.pkg;
        try { localStorage.setItem('spo_rad_' + consecutivo, JSON.stringify(pkg)); } catch (e) { }
        try { localStorage.setItem('spo_last', String(consecutivo)); } catch (e) { }

        var inp = document.getElementById('rad-input');
        if (inp) {
          inp.value = consecutivo;
          if (typeof loadFromLocalStorage === 'function') {
            loadFromLocalStorage();
          } else if (typeof tryLocalStorage === 'function') {
            tryLocalStorage();
          }
          pltClose();
        } else {
          window.location.reload();
        }
      })
      .catch(function (e) { alert('Error de conexión: ' + e); });
  };

  /* ── Toast helper ────────────────────────────────────────────────────── */
  function pltToast(html) {
    toastEl.innerHTML = html;
    toastEl.classList.add('on');
    if (_toastTimer) clearTimeout(_toastTimer);
    _toastTimer = setTimeout(function () { toastEl.classList.remove('on'); }, 6000);
  }

  /* ── Interceptar localStorage.setItem para auto-guardar radicaciones ─── */
  /* Solo interceptamos spo_rad_* para enviar al servidor                  */
  var _origSet = Storage.prototype.setItem;
  Storage.prototype.setItem = function (key, value) {
    _origSet.call(this, key, value);
    if (this === window.localStorage && key && key.indexOf('spo_rad_') === 0) {
      try {
        var consec = key.replace('spo_rad_', '');
        var pkg = JSON.parse(value);
        fetch('/licencias/api/guardar', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ pkg: pkg, consecutivo: consec })
        })
          .then(function (r) { return r.json(); })
          .then(function (d) {
            if (d.ok) {
              _rads = null; // Forzar recarga en próxima apertura
              pltToast(
                '✓ Guardado en plataforma' +
                (d.nuevo ? ' como nuevo expediente' : '') +
                ' &mdash; <a href="/licencias/plataforma" target="_blank">Ver expedientes</a>'
              );
            }
          })
          .catch(function () { /* silencioso */ });
      } catch (e) { /* silencioso */ }
    }
  };

})();
