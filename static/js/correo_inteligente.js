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
