(function () {
  function renderBars(containerId, dataObj) {
    var container = document.getElementById(containerId);
    if (!container || !dataObj) return;

    var entries = Object.entries(dataObj);
    if (!entries.length) {
      container.innerHTML = '<p class="text-muted small mb-0">Sin datos.</p>';
      return;
    }

    var maxValue = Math.max.apply(null, entries.map(function (entry) { return entry[1]; }));
    var html = entries
      .sort(function (a, b) { return b[1] - a[1]; })
      .map(function (entry) {
        var label = entry[0];
        var value = entry[1];
        var width = Math.max(8, Math.round((value / (maxValue || 1)) * 100));
        return (
          '<div class="bar-row">' +
            '<span class="bar-label">' + label + '</span>' +
            '<div class="bar-track"><div class="bar-fill" style="width:' + width + '%"></div></div>' +
            '<span class="bar-count">' + value + '</span>' +
          '</div>'
        );
      })
      .join('');

    container.innerHTML = html;
  }

  async function postJson(url, payload) {
    var response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {}),
    });
    return response.json();
  }

  async function generateDraft(messageId, tone) {
    var result = await postJson('/correo-inteligente/api/message/' + messageId + '/draft', { tone: tone });
    if (!result.success) throw new Error(result.error || 'No se pudo generar borrador');
    return result.draft;
  }

  async function reanalyze(messageId) {
    var result = await postJson('/correo-inteligente/api/message/' + messageId + '/reanalyze', {});
    if (!result.success) throw new Error(result.error || 'No se pudo reanalizar');
  }

  async function updateStatus(messageId, status) {
    var result = await postJson('/correo-inteligente/api/message/' + messageId + '/status', { status: status });
    if (!result.success) throw new Error(result.error || 'No se pudo actualizar estado');
  }

  document.addEventListener('DOMContentLoaded', function () {
    var analyticsRoot = document.getElementById('mail-analytics');
    if (analyticsRoot) {
      try {
        renderBars('categoriaBars', JSON.parse(analyticsRoot.dataset.categoria || '{}'));
        renderBars('estadoBars', JSON.parse(analyticsRoot.dataset.estado || '{}'));
        renderBars('tendenciaBars', JSON.parse(analyticsRoot.dataset.tendencia || '{}'));
      } catch (e) {
        console.warn('No se pudieron renderizar barras analiticas', e);
      }
    }

    var openDraftBtn = document.getElementById('openDraftModalBtn');
    var draftModal = document.getElementById('draftComposeModal');
    var closeDraftBtn = document.getElementById('closeDraftModalBtn');
    var generateDraftBtn = document.getElementById('generateDraftBtn');
    var draftTone = document.getElementById('draftTone');
    var draftResult = document.getElementById('draftResult');
    var loadingOverlay = document.getElementById('draftLoadingOverlay');
    var btnMinimize = document.querySelector('.btn-minimize');
    var btnExpand = document.querySelector('.btn-expand');
    var discardDraftBtn = document.getElementById('discardDraftBtn');

    // UI Controls for Modal
    if (openDraftBtn && draftModal) {
      openDraftBtn.addEventListener('click', function () {
        draftModal.classList.add('show');
        draftModal.classList.remove('minimized');
      });
    }

    if (closeDraftBtn && draftModal) {
      closeDraftBtn.addEventListener('click', function () {
        draftModal.classList.remove('show');
      });
    }
    
    if (discardDraftBtn && draftModal) {
      discardDraftBtn.addEventListener('click', function () {
        draftModal.classList.remove('show');
        if (draftResult) draftResult.value = '';
      });
    }

    if (btnMinimize && draftModal) {
      btnMinimize.addEventListener('click', function (e) {
        e.stopPropagation();
        draftModal.classList.toggle('minimized');
      });
    }

    if (btnExpand && draftModal) {
      btnExpand.addEventListener('click', function (e) {
        e.stopPropagation();
        draftModal.classList.toggle('expanded');
        var icon = btnExpand.querySelector('i');
        if (draftModal.classList.contains('expanded')) {
          icon.classList.remove('bi-arrows-angle-expand');
          icon.classList.add('bi-arrows-angle-contract');
        } else {
          icon.classList.remove('bi-arrows-angle-contract');
          icon.classList.add('bi-arrows-angle-expand');
        }
      });
    }
    
    // Header click to toggle minimize
    var composeHeader = document.querySelector('.compose-header');
    if (composeHeader && draftModal) {
      composeHeader.addEventListener('click', function(e) {
        if (e.target.closest('.compose-actions')) return;
        draftModal.classList.toggle('minimized');
      });
    }

    // Generate Draft Logic
    if (generateDraftBtn && draftTone && draftResult) {
      generateDraftBtn.addEventListener('click', async function () {
        if (!window.currentMessageId) return alert('No hay correo seleccionado');
        
        generateDraftBtn.disabled = true;
        if (loadingOverlay) loadingOverlay.classList.add('active');

        try {
          var draft = await generateDraft(window.currentMessageId, draftTone.value);
          draftResult.value = draft.contenido || '';
        } catch (error) {
          alert(error.message || 'Error al generar borrador');
        } finally {
          generateDraftBtn.disabled = false;
          if (loadingOverlay) loadingOverlay.classList.remove('active');
        }
      });
    }

    // Send Draft Logic
    var sendDraftBtn = document.getElementById('sendDraftBtn');
    if (sendDraftBtn && draftResult) {
      sendDraftBtn.addEventListener('click', async function() {
        if (!window.currentMessageId) return alert('No hay correo seleccionado');
        var body = draftResult.value.trim();
        if (!body) return alert('El borrador está vacío');
        
        sendDraftBtn.disabled = true;
        var originalBtnHtml = sendDraftBtn.innerHTML;
        sendDraftBtn.innerHTML = '<i class="bi bi-hourglass"></i> Enviando...';
        
        try {
          var result = await postJson('/correo-inteligente/api/message/' + window.currentMessageId + '/send_reply', { body: body });
          if (!result.success) throw new Error(result.error || 'No se pudo enviar el correo');
          
          alert('Correo enviado exitosamente.');
          draftModal.classList.remove('show');
          window.location.reload();
        } catch (error) {
          alert(error.message || 'Error al enviar la respuesta');
        } finally {
          sendDraftBtn.disabled = false;
          sendDraftBtn.innerHTML = originalBtnHtml;
        }
      });
    }

    // Agregar al Calendario
    var addToCalBtn = document.getElementById('addToCalendarBtn');
    var calModal = document.getElementById('calendarModal');
    var closeCalModal = document.getElementById('closeCalendarModalBtn');
    var cancelCalBtn = document.getElementById('cancelCalendarBtn');
    var saveCalBtn = document.getElementById('saveCalendarEventBtn');

    function openCalendarModal() {
      if (!addToCalBtn || !calModal) return;
      var asunto = addToCalBtn.dataset.asunto || '';
      var resumen = addToCalBtn.dataset.resumen || '';
      document.getElementById('calTitulo').value = asunto;
      document.getElementById('calDescripcion').value = resumen;
      // Default: mañana a las 08:00
      var tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setHours(8, 0, 0, 0);
      var pad = function(n) { return String(n).padStart(2, '0'); };
      var fmt = function(d) {
        return d.getFullYear() + '-' + pad(d.getMonth()+1) + '-' + pad(d.getDate()) + 'T' + pad(d.getHours()) + ':' + pad(d.getMinutes());
      };
      var end = new Date(tomorrow); end.setHours(9, 0, 0, 0);
      document.getElementById('calFechaInicio').value = fmt(tomorrow);
      document.getElementById('calFechaFin').value = fmt(end);
      calModal.classList.add('show');
    }

    if (addToCalBtn) addToCalBtn.addEventListener('click', openCalendarModal);
    if (closeCalModal) closeCalModal.addEventListener('click', function() { calModal.classList.remove('show'); });
    if (cancelCalBtn) cancelCalBtn.addEventListener('click', function() { calModal.classList.remove('show'); });

    if (saveCalBtn) {
      saveCalBtn.addEventListener('click', async function() {
        var msgId = addToCalBtn ? addToCalBtn.dataset.messageId : null;
        if (!msgId) return alert('No hay correo seleccionado');
        var titulo = document.getElementById('calTitulo').value.trim();
        var fechaInicio = document.getElementById('calFechaInicio').value;
        if (!titulo) return alert('El título es obligatorio');
        if (!fechaInicio) return alert('La fecha de inicio es obligatoria');
        saveCalBtn.disabled = true;
        var orig = saveCalBtn.innerHTML;
        saveCalBtn.innerHTML = '<i class="bi bi-hourglass"></i> Guardando...';
        try {
          var result = await postJson('/correo-inteligente/api/message/' + msgId + '/add-to-calendar', {
            titulo: titulo,
            descripcion: document.getElementById('calDescripcion').value.trim(),
            fecha_inicio: fechaInicio,
            fecha_fin: document.getElementById('calFechaFin').value || null,
            categoria: document.getElementById('calCategoria').value,
            ubicacion: document.getElementById('calUbicacion').value.trim(),
          });
          if (!result.success) throw new Error(result.error || 'No se pudo crear el evento');
          calModal.classList.remove('show');
          alert('Evento "' + result.titulo + '" creado en el calendario.');
        } catch(e) {
          alert(e.message || 'Error al crear evento');
        } finally {
          saveCalBtn.disabled = false;
          saveCalBtn.innerHTML = orig;
        }
      });
    }

    document.querySelectorAll('[data-reanalyze]').forEach(function (btn) {
      btn.addEventListener('click', async function () {
        btn.disabled = true;
        try {
          await reanalyze(btn.dataset.reanalyze);
          window.location.reload();
        } catch (error) {
          alert(error.message || 'Error al reanalizar');
        } finally {
          btn.disabled = false;
        }
      });
    });

    document.querySelectorAll('[data-status][data-message-id]').forEach(function (btn) {
      btn.addEventListener('click', async function () {
        btn.disabled = true;
        try {
          await updateStatus(btn.dataset.messageId, btn.dataset.status);
          window.location.reload();
        } catch (error) {
          alert(error.message || 'Error al actualizar estado');
        } finally {
          btn.disabled = false;
        }
      });
    });
  });
})();
