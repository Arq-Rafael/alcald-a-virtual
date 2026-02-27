'use strict';

window.MD = (function () {
  const state = {
    filters: { q: '', secretaria: '', eje: '', estado: '', riesgo: '' },
    page: 1,
    perPage: 25,
    sort: 'rezago',
    order: 'desc',
    view: 'table',
    currentMetaId: null,
    filterOptions: { secretarias: [], ejes: [] },
    kpis: null,
    charts: {},
  };

  function el(id) { return document.getElementById(id); }
  function esc(v) {
    return String(v ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function fmtNum(v) {
    const n = Number(v || 0);
    return Number.isFinite(n) ? n.toLocaleString('es-CO') : '0';
  }

  function fmtPct(v) {
    const n = Number(v || 0);
    return `${n.toFixed(1)}%`;
  }

  async function fetchJson(url, params = null) {
    const query = params ? `?${new URLSearchParams(params).toString()}` : '';
    const resp = await fetch(`${url}${query}`, { cache: 'no-store', credentials: 'same-origin' });
    if (resp.status === 401) {
      window.location.href = '/login';
      throw new Error('unauthorized');
    }
    if (!resp.ok) {
      let msg = `Error ${resp.status}`;
      try { const j = await resp.json(); msg = j.error || msg; } catch (_) {}
      throw new Error(msg);
    }
    return resp.json();
  }

  function _showSectionError(elementId, cols, msg) {
    const e = el(elementId);
    if (!e) return;
    e.innerHTML = `<tr><td colspan="${cols}" class="md-empty" style="color:#ef4444">
      ⚠ ${msg || 'Error al cargar datos. Recarga la página.'}
    </td></tr>`;
  }

  function _showDivError(elementId, msg) {
    const e = el(elementId);
    if (!e) return;
    e.innerHTML = `<p style="color:#ef4444;font-size:0.76rem;padding:0.5rem">⚠ ${msg || 'Error al cargar.'}</p>`;
  }

  function bindEvents() {
    el('mdBtnApplyFilters').addEventListener('click', () => applyFilters());
    el('mdBtnClearFilters').addEventListener('click', () => clearFilters());
    el('mdFilterQ').addEventListener('keydown', (ev) => {
      if (ev.key === 'Enter') applyFilters();
    });

    el('mdViewTableBtn').addEventListener('click', () => setView('table'));
    el('mdViewCardsBtn').addEventListener('click', () => setView('cards'));

    el('mdBtnExportPdf').addEventListener('click', () => openPdfPanel());
    el('mdPdfClose').addEventListener('click', () => closePdfPanel());
    el('mdPdfGeneralBtn').addEventListener('click', () => exportPdfGeneral());
    el('mdPdfSecBtn').addEventListener('click', () => exportPdfSecretaria());

    el('mdDetailClose').addEventListener('click', () => closeDetail());
    el('mdDetailModal').addEventListener('click', (ev) => {
      if (ev.target.id === 'mdDetailModal') closeDetail();
    });
    el('mdPdfModal').addEventListener('click', (ev) => {
      if (ev.target.id === 'mdPdfModal') closePdfPanel();
    });
    el('mdDetailExportBtn').addEventListener('click', () => {
      if (!state.currentMetaId) return;
      window.open(`/metas/${encodeURIComponent(state.currentMetaId)}/export/pdf`, '_blank');
    });
  }

  function renderFilterOptions(filters) {
    if (!filters) return;
    state.filterOptions.secretarias = filters.secretarias || [];
    state.filterOptions.ejes = filters.ejes || [];

    const secSelect = el('mdFilterSecretaria');
    const ejeSelect = el('mdFilterEje');
    const pdfSecSelect = el('mdPdfSecSelect');

    secSelect.innerHTML = '<option value="">Todas las secretarias</option>' +
      state.filterOptions.secretarias.map((s) => `<option value="${esc(s)}">${esc(s)}</option>`).join('');
    ejeSelect.innerHTML = '<option value="">Todos los ejes</option>' +
      state.filterOptions.ejes.map((s) => `<option value="${esc(s)}">${esc(s)}</option>`).join('');
    pdfSecSelect.innerHTML = '<option value="">Seleccionar secretaria</option>' +
      state.filterOptions.secretarias.map((s) => `<option value="${esc(s)}">${esc(s)}</option>`).join('');

    secSelect.value = state.filters.secretaria;
    ejeSelect.value = state.filters.eje;
  }

  function semaforoDot(semaforo) {
    const s = String(semaforo || '').toLowerCase();
    if (s.includes('roj')) return 'rojo';
    if (s.includes('naran')) return 'naranja';
    if (s.includes('amar')) return 'amarillo';
    return 'verde';
  }

  function estadoPillClass(estado) {
    const e = String(estado || '').toLowerCase();
    if (e.includes('cumplid')) return 'green';
    if (e.includes('riesgo')) return 'red';
    if (e.includes('curso')) return 'blue';
    return 'orange';
  }

  function trendClass(t) {
    const v = String(t || '').toLowerCase();
    if (v.includes('mejor')) return 'mejorando';
    if (v.includes('empeor')) return 'empeorando';
    return 'estable';
  }

  function renderMethodology(method) {
    if (!method) {
      el('mdMethodology').innerText = 'No hay metodologia disponible.';
      return;
    }
    const comps = method.componentes || {};
    el('mdMethodology').innerHTML = `
      <p><strong>Formula:</strong> ${esc(method.formula || '')}</p>
      <p><strong>Regla de riesgo:</strong> ${esc(method.riesgo_regla || '')}</p>
      <ul>
        ${Object.keys(comps).map((k) => `<li><strong>${esc(k)}:</strong> ${esc(comps[k])}</li>`).join('')}
      </ul>
    `;
  }

  function renderRecommendations(items) {
    const wrap = el('mdRecommendations');
    if (!items || !items.length) {
      wrap.innerHTML = '<p class="md-muted">Sin recomendaciones.</p>';
      return;
    }
    wrap.innerHTML = items.map((r) => `
      <div class="md-recommendation">
        <h4>${esc(r.titulo || 'Recomendacion')}</h4>
        <p>${esc(r.detalle || '')}</p>
      </div>
    `).join('');
  }

  function renderShockPlans(plans) {
    const tbody = el('mdShockBody');
    if (!plans || !plans.length) {
      tbody.innerHTML = '<tr><td colspan="5" class="md-empty">Sin planes de choque.</td></tr>';
      return;
    }
    tbody.innerHTML = plans.map((p) => {
      const first = (p.acciones && p.acciones.length) ? p.acciones[0] : null;
      return `
        <tr>
          <td>${esc(p.secretaria || '-')}</td>
          <td>${Number(p.score_prom || 0).toFixed(1)}</td>
          <td>${fmtNum(p.en_riesgo || 0)}</td>
          <td>${fmtNum(p.no_iniciadas || 0)}</td>
          <td>${esc(first ? first.accion : 'Mantener seguimiento mensual')}</td>
        </tr>
      `;
    }).join('');
  }

  function buildKpiCards(kpis) {
    const cards = [
      { key: 'total', label: 'Total metas', value: fmtNum(kpis.total), filter: null },
      { key: 'cumplidas', label: 'Cumplidas', value: fmtNum(kpis.cumplidas), filter: { estado: 'cumplida' } },
      { key: 'en_curso', label: 'En curso', value: fmtNum(kpis.en_curso), filter: { estado: 'en curso' } },
      { key: 'no_iniciadas', label: 'No iniciadas', value: fmtNum(kpis.no_iniciadas), filter: { estado: 'no iniciada' } },
      { key: 'en_riesgo', label: 'En riesgo', value: fmtNum(kpis.en_riesgo), filter: { estado: 'en riesgo' } },
      { key: 'avance_prom', label: 'Avance fisico', value: fmtPct(kpis.avance_prom), filter: null },
      { key: 'fin_prom', label: 'Avance financiero', value: fmtPct(kpis.fin_prom), filter: null },
      { key: 'score_prom', label: 'Indice de rendimiento', value: `${Number(kpis.score_prom || 0).toFixed(1)}`, filter: null },
    ];
    el('mdKpiRow').innerHTML = cards.map((card) => {
      const active = card.filter && state.filters.estado === card.filter.estado ? 'active' : '';
      return `
        <div class="md-kpi ${active}" data-kpi="${esc(card.key)}">
          <div class="kpi-value">${esc(card.value)}</div>
          <div class="kpi-label">${esc(card.label)}</div>
          ${card.filter ? '<div class="kpi-sub">Click para filtrar</div>' : ''}
        </div>
      `;
    }).join('');

    el('mdKpiRow').querySelectorAll('.md-kpi').forEach((node, idx) => {
      const cfg = cards[idx];
      if (!cfg.filter) return;
      node.addEventListener('click', () => {
        state.filters.estado = cfg.filter.estado;
        el('mdFilterEstado').value = cfg.filter.estado;
        state.page = 1;
        loadList();
        buildKpiCards(kpis);
      });
    });
  }

  function renderPriority(rows) {
    const tbody = el('mdPriorityBody');
    if (!rows || !rows.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="md-empty">No hay metas rezagadas.</td></tr>';
      return;
    }
    tbody.innerHTML = rows.map((m) => `
      <tr>
        <td><span class="md-dot ${semaforoDot(m.semaforo)}"></span></td>
        <td>${Number(m.score || 0).toFixed(1)}</td>
        <td>${esc(m.id_meta || '-')}</td>
        <td>${esc(m.meta_producto || '-')}</td>
        <td>${esc(m.secretaria || '-')}</td>
        <td>${fmtPct(m.avance_fisico_pct)}</td>
        <td>${esc(m.resumen_rezago || '-')}</td>
        <td><button class="md-btn md-btn-sm" data-open="${esc(m.id_meta)}">Detalle</button></td>
      </tr>
    `).join('');
    tbody.querySelectorAll('[data-open]').forEach((btn) => {
      btn.addEventListener('click', () => openDetail(btn.dataset.open));
    });
  }

  function destroyChart(key) {
    if (state.charts[key]) {
      state.charts[key].destroy();
      state.charts[key] = null;
    }
  }

  function renderCharts(data) {
    if (!window.Chart) return;
    const dist = data.distribucion || {};
    const rank = data.ranking_secretarias || {};
    const evo = data.evolucion || {};
    const eje = data.por_eje || {};

    destroyChart('status');
    state.charts.status = new Chart(el('mdChartStatus').getContext('2d'), {
      type: 'doughnut',
      data: {
        labels: dist.labels || [],
        datasets: [{ data: dist.data || [], backgroundColor: ['#16a34a', '#0f4c81', '#f59e0b', '#ef4444'] }],
      },
      options: { plugins: { legend: { position: 'bottom' } } },
    });

    destroyChart('ranking');
    state.charts.ranking = new Chart(el('mdChartRanking').getContext('2d'), {
      type: 'bar',
      data: {
        labels: rank.labels || [],
        datasets: [{ label: 'Score', data: rank.score || [], backgroundColor: '#0f4c81' }],
      },
      options: { indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { min: 0, max: 100 } } },
    });

    destroyChart('evolution');
    state.charts.evolution = new Chart(el('mdChartEvolution').getContext('2d'), {
      type: 'line',
      data: {
        labels: evo.labels || [],
        datasets: [
          { label: 'Fisico', data: evo.avance || [], borderColor: '#0f4c81', backgroundColor: '#0f4c81', tension: 0.2 },
          { label: 'Financiero', data: evo.fin || [], borderColor: '#f59e0b', backgroundColor: '#f59e0b', tension: 0.2 },
        ],
      },
      options: { scales: { y: { min: 0, max: 100 } } },
    });

    destroyChart('axis');
    
    // Clean up long axis labels
    const cleanLabels = (eje.labels || []).map(label => {
      return label.replace(/POR EL SUPATÁ SOÑADO AVANZAMOS JUNTOS EN LA LÍNEA ESTRATÉGICA /i, '')
                  .replace(/POR EL SUPATA SOÑADO AVANZAMOS JUNTOS EN LA LINEA ESTRATEGICA /i, '');
    });

    state.charts.axis = new Chart(el('mdChartAxis').getContext('2d'), {
      type: 'bar',
      data: {
        labels: cleanLabels,
        datasets: [
          { label: 'Avance', data: eje.avance || [], backgroundColor: '#0ea5e9' },
          { label: 'Score', data: eje.score || [], backgroundColor: '#334155' },
        ],
      },
      options: { scales: { y: { min: 0, max: 100 } } },
    });
  }

  function renderTable(rows) {
    const tbody = el('mdListBody');
    if (!rows || !rows.length) {
      tbody.innerHTML = '<tr><td colspan="11" class="md-empty">No se encontraron metas.</td></tr>';
      return;
    }
    tbody.innerHTML = rows.map((m) => `
      <tr>
        <td>${esc(m.id_meta || '-')}</td>
        <td>${esc(m.meta_producto || '-')}</td>
        <td>${esc(m.eje || '-')} / ${esc(m.sector || '-')}</td>
        <td>${esc(m.secretaria || '-')}</td>
        <td><span class="md-pill ${estadoPillClass(m.estado)}">${esc(m.estado || '-')}</span></td>
        <td>${fmtPct(m.avance_fisico_pct)}</td>
        <td><span class="md-trend ${trendClass(m.tendencia)}">${esc(m.tendencia || '-')}</span></td>
        <td><span class="md-dot ${semaforoDot(m.semaforo)}"></span></td>
        <td>${esc(m.ultima_actualizacion || '-')}</td>
        <td>${Number(m.score || 0).toFixed(1)}</td>
        <td><button class="md-btn md-btn-sm" data-open="${esc(m.id_meta)}">Ver</button></td>
      </tr>
    `).join('');
    tbody.querySelectorAll('[data-open]').forEach((btn) => {
      btn.addEventListener('click', () => openDetail(btn.dataset.open));
    });
  }

  function renderCards(rows) {
    const grid = el('mdCardsGrid');
    if (!rows || !rows.length) {
      grid.innerHTML = '<p class="md-empty">No se encontraron metas.</p>';
      return;
    }
    grid.innerHTML = rows.map((m) => `
      <article class="md-meta-card">
        <h4>${esc(m.id_meta || '-')} · ${esc(m.meta_producto || '-')}</h4>
        <p><strong>Secretaria:</strong> ${esc(m.secretaria || '-')}</p>
        <p><strong>Estado:</strong> ${esc(m.estado || '-')} | <strong>Semaforo:</strong> ${esc(m.semaforo || '-')}</p>
        <p><strong>Avance:</strong> ${fmtPct(m.avance_fisico_pct)} | <strong>Score:</strong> ${Number(m.score || 0).toFixed(1)}</p>
        <p><strong>Ult. actualizacion:</strong> ${esc(m.ultima_actualizacion || '-')}</p>
        <button class="md-btn md-btn-sm" data-open="${esc(m.id_meta)}">Ver detalle</button>
      </article>
    `).join('');
    grid.querySelectorAll('[data-open]').forEach((btn) => {
      btn.addEventListener('click', () => openDetail(btn.dataset.open));
    });
  }

  function renderPagination(page, pages, total) {
    el('mdPaginationInfo').innerText = `Pagina ${page} de ${pages} · ${fmtNum(total)} metas`;
    const wrap = el('mdPaginationBtns');
    wrap.innerHTML = '';
    const prev = document.createElement('button');
    prev.className = 'md-btn md-btn-sm';
    prev.innerText = '«';
    prev.disabled = page <= 1;
    prev.addEventListener('click', () => { state.page -= 1; loadList(); });
    wrap.appendChild(prev);

    const from = Math.max(1, page - 2);
    const to = Math.min(pages, page + 2);
    for (let p = from; p <= to; p += 1) {
      const b = document.createElement('button');
      b.className = `md-btn md-btn-sm ${p === page ? 'md-btn-primary' : ''}`;
      b.innerText = String(p);
      b.addEventListener('click', () => { state.page = p; loadList(); });
      wrap.appendChild(b);
    }

    const next = document.createElement('button');
    next.className = 'md-btn md-btn-sm';
    next.innerText = '»';
    next.disabled = page >= pages;
    next.addEventListener('click', () => { state.page += 1; loadList(); });
    wrap.appendChild(next);
  }

  async function loadSummary() {
    let data;
    try {
      data = await fetchJson('/api/metas/summary');
    } catch (err) {
      if (el('mdSubtitle')) el('mdSubtitle').innerText = 'Error al cargar resumen — ' + err.message;
      _showSectionError('mdShockBody', 5, err.message);
      _showSectionError('mdPriorityBody', 8, err.message);
      _showDivError('mdRecommendations', err.message);
      _showDivError('mdMethodology', err.message);
      _showDivError('mdKpiRow', err.message);
      throw err;
    }
    const k = data.kpis || {};
    state.kpis = k;
    if (el('mdSubtitle')) el('mdSubtitle').innerText = `Plan de Desarrollo 2024-2027 · ${fmtNum(k.total)} metas`;
    if (el('mdChipTime')) el('mdChipTime').innerText = `Tiempo transcurrido: ${fmtPct(k.pct_tiempo)}`;
    if (el('mdChipScore')) el('mdChipScore').innerText = `Score promedio: ${Number(k.score_prom || 0).toFixed(1)}/100`;
    if (el('mdChipUpdated')) el('mdChipUpdated').innerText = `Desactualizadas (>45d): ${fmtNum(k.desactualizadas)}`;

    renderFilterOptions(data.filtros || {});
    renderMethodology(data.metodologia || {});
    renderRecommendations(data.recomendaciones || []);
    renderShockPlans(data.planes_secretaria || []);
    renderPriority(data.rezagadas || []);
    buildKpiCards(k);
  }

  async function loadCharts() {
    try {
      const data = await fetchJson('/api/metas/charts');
      renderCharts(data);
    } catch (err) {
      console.warn('Charts no disponibles:', err.message);
    }
  }

  async function loadList() {
    const listBody = el('mdListBody');
    if (listBody) listBody.innerHTML = '<tr><td colspan="11" class="md-empty">Cargando...</td></tr>';
    let data;
    try {
      data = await fetchJson('/api/metas/list', {
        q: state.filters.q,
        sec: state.filters.secretaria,
        eje: state.filters.eje,
        estado: state.filters.estado,
        riesgo: state.filters.riesgo,
        page: state.page,
        per_page: state.perPage,
        sort: state.sort,
        order: state.order,
      });
    } catch (err) {
      _showSectionError('mdListBody', 11, err.message);
      if (el('mdPaginationInfo')) el('mdPaginationInfo').innerText = 'Error al cargar';
      return;
    }
    renderFilterOptions(data.filtros || {});
    renderTable(data.metas || []);
    renderCards(data.metas || []);
    renderPagination(Number(data.page || 1), Number(data.pages || 1), Number(data.total || 0));
  }

  function setView(mode) {
    state.view = mode;
    const tableBtn = el('mdViewTableBtn');
    const cardsBtn = el('mdViewCardsBtn');
    if (mode === 'cards') {
      tableBtn.classList.remove('active');
      cardsBtn.classList.add('active');
      el('mdTableWrap').style.display = 'none';
      el('mdCardsWrap').style.display = 'block';
    } else {
      cardsBtn.classList.remove('active');
      tableBtn.classList.add('active');
      el('mdCardsWrap').style.display = 'none';
      el('mdTableWrap').style.display = 'block';
    }
  }

  function applyFilters() {
    state.filters.q = el('mdFilterQ').value.trim();
    state.filters.secretaria = el('mdFilterSecretaria').value;
    state.filters.eje = el('mdFilterEje').value;
    state.filters.estado = el('mdFilterEstado').value;
    state.filters.riesgo = el('mdFilterRiesgo').value;
    state.page = 1;
    if (state.kpis) buildKpiCards(state.kpis);
    loadList();
  }

  function clearFilters() {
    state.filters = { q: '', secretaria: '', eje: '', estado: '', riesgo: '' };
    el('mdFilterQ').value = '';
    el('mdFilterSecretaria').value = '';
    el('mdFilterEje').value = '';
    el('mdFilterEstado').value = '';
    el('mdFilterRiesgo').value = '';
    state.page = 1;
    if (state.kpis) buildKpiCards(state.kpis);
    loadList();
  }

  async function openDetail(metaId) {
    el('mdDetailModal').classList.add('open');
    el('mdDetailTitle').innerText = 'Cargando...';
    el('mdDetailMeta').innerText = '';
    el('mdDetailSummary').innerText = '';
    el('mdDetailTimelineBody').innerHTML = '<tr><td colspan="5" class="md-empty">Cargando...</td></tr>';
    el('mdDetailEvidence').innerHTML = '';
    el('mdDetailCauses').innerHTML = '<li>Cargando...</li>';
    el('mdDetailPlan').innerHTML = '<li>Cargando...</li>';

    let data;
    try {
      data = await fetchJson(`/api/metas/${encodeURIComponent(metaId)}`);
    } catch (err) {
      el('mdDetailTitle').innerText = 'Error al cargar';
      el('mdDetailSummary').innerText = err.message;
      el('mdDetailTimelineBody').innerHTML = '<tr><td colspan="5" class="md-empty" style="color:#ef4444">Error al cargar detalle</td></tr>';
      return;
    }
    state.currentMetaId = metaId;
    el('mdDetailTitle').innerText = `${data.id_meta || ''} · ${data.meta_producto || 'Meta'}`;
    el('mdDetailMeta').innerText = `${data.secretaria || '-'} · Estado: ${data.estado || '-'} · Score: ${Number(data.score || 0).toFixed(1)}`;
    el('mdDetailSummary').innerText = data.resumen_ejecutivo || 'Sin resumen.';

    const timeline = data.timeline || [];
    el('mdDetailTimelineBody').innerHTML = timeline.length
      ? timeline.map((t) => `
          <tr>
            <td>${esc(t.periodo || '-')}</td>
            <td>${esc(t.estado || '-')}</td>
            <td>${t.avance_fisico_pct == null ? '-' : fmtPct(t.avance_fisico_pct)}</td>
            <td>${t.ejec_fin_pct == null ? '-' : fmtPct(t.ejec_fin_pct)}</td>
            <td>${esc(t.fecha_actualizacion || '-')}</td>
          </tr>
        `).join('')
      : '<tr><td colspan="5" class="md-empty">Sin registros</td></tr>';

    const evidencias = data.evidencias || [];
    el('mdDetailEvidence').innerHTML = evidencias.length
      ? evidencias.map((ev) => `
          <div class="md-evidence-card">
            <a href="${esc(ev.url || '#')}" target="_blank" rel="noopener">
              <img src="${esc(ev.url || '')}" alt="Evidencia" />
            </a>
            <p>${esc(ev.caption || 'Sin leyenda')}</p>
            <p class="md-muted">${esc(ev.fecha || '')}</p>
          </div>
        `).join('')
      : '<p class="md-muted">No hay evidencias registradas.</p>';

    const causas = data.causas_probables || [];
    el('mdDetailCauses').innerHTML = causas.length
      ? causas.map((c) => `<li>${esc(c.detalle || c.tipo || '')}</li>`).join('')
      : '<li>Sin causas registradas.</li>';

    const plan = data.plan_mejora || [];
    el('mdDetailPlan').innerHTML = plan.length
      ? plan.map((p) => `<li><strong>${esc(p.titulo || 'Accion')}:</strong> ${esc(p.detalle || '')}</li>`).join('')
      : '<li>Sin plan de mejora registrado.</li>';

    el('mdDetailModal').classList.add('open');
  }

  function closeDetail() {
    el('mdDetailModal').classList.remove('open');
  }

  function openPdfPanel() { el('mdPdfModal').classList.add('open'); }
  function closePdfPanel() { el('mdPdfModal').classList.remove('open'); }
  function exportPdfGeneral() { window.open('/metas/export/pdf?scope=general', '_blank'); }
  function exportPdfSecretaria() {
    const sec = el('mdPdfSecSelect').value;
    if (!sec) return;
    window.open(`/metas/export/pdf?scope=secretaria&sec=${encodeURIComponent(sec)}`, '_blank');
  }

  async function init() {
    bindEvents();
    setView('table');
    // Mostrar estado inicial de carga
    if (el('mdSubtitle')) el('mdSubtitle').innerText = 'Cargando datos del Plan de Desarrollo...';
    try {
      await loadSummary();
    } catch (err) {
      console.error('Error cargando resumen:', err);
      // loadSummary ya mostró los errores en la UI
    }
    // Cargar gráficas y lista en paralelo, independientemente del resumen
    await Promise.allSettled([loadCharts(), loadList()]);
  }

  return {
    init,
    applyFilters,
    clearFilters,
    setView,
    openDetail,
    openPdfPanel,
    closePdfPanel,
    exportPdfGeneral,
    exportPdfSecretaria,
  };
})();
