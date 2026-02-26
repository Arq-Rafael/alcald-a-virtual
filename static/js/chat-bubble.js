/**
 * Chat Interno — Alcaldía Municipal de Supatá
 * Funciones premium: usuarios desde DB, no leídos por contacto, adjuntos, polling corregido.
 */

(function () {
  'use strict';

  // ── Estado ──────────────────────────────────────────────────────────────────
  let chatBubble         = null;
  let chatModal          = null;
  let isOpen             = false;
  let currentContact     = null;    // username del contacto abierto
  let currentContactName = null;    // nombre visible del contacto abierto
  let allContacts        = [];      // caché de contactos (para filtro en memoria)
  let unreadByContact    = {};      // { username: count }
  let totalUnread        = 0;
  let messageCheckInterval = null;

  // ── Inicialización ──────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    createChatBubble();
    createChatModal();
    startMessagePolling();
  });

  // ══════════════════════════════════════════════════════════════════════════
  //  BURBUJA FLOTANTE
  // ══════════════════════════════════════════════════════════════════════════
  function createChatBubble() {
    chatBubble = document.createElement('div');
    chatBubble.id = 'chatBubble';
    chatBubble.className = 'chat-bubble';
    chatBubble.innerHTML = `
      <div class="chat-bubble-icon">
        <i class="bi bi-chat-dots-fill"></i>
      </div>
      <div class="chat-bubble-badge" id="chatBadge" style="display:none;">0</div>
    `;
    chatBubble.addEventListener('click', toggleChatModal);
    document.body.appendChild(chatBubble);
  }

  // ══════════════════════════════════════════════════════════════════════════
  //  MODAL
  // ══════════════════════════════════════════════════════════════════════════
  function createChatModal() {
    chatModal = document.createElement('div');
    chatModal.id = 'chatModal';
    chatModal.className = 'chat-modal';
    chatModal.style.display = 'none';

    chatModal.innerHTML = `
      <div class="chat-modal-container">

        <!-- Header -->
        <div class="chat-modal-header">
          <div class="chat-modal-header-left">
            <button class="chat-back-btn" id="backToContactsBtn" style="display:none;" title="Volver">
              <i class="bi bi-chevron-left"></i>
            </button>
            <div class="chat-modal-avatar" id="modalAvatar">
              <i class="bi bi-chat-dots-fill"></i>
            </div>
            <div class="chat-modal-header-info">
              <h5 id="modalContactName">Chat Interno</h5>
              <p  id="modalContactStatus">Selecciona un contacto</p>
            </div>
          </div>
          <div class="chat-modal-header-actions">
            <button class="chat-modal-btn" id="minimizeChat" title="Minimizar">
              <i class="bi bi-dash-lg"></i>
            </button>
            <button class="chat-modal-btn" id="closeChat" title="Cerrar">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>
        </div>

        <!-- Cuerpo -->
        <div class="chat-modal-body" id="chatModalBody">

          <!-- Panel de contactos -->
          <div class="chat-contacts-panel" id="contactsPanel">
            <div class="chat-contacts-search">
              <i class="bi bi-search"></i>
              <input type="text" id="searchContacts" placeholder="Buscar contacto o dependencia...">
            </div>
            <div class="chat-contacts-list" id="contactsList">
              <div class="chat-loading">Cargando contactos...</div>
            </div>
          </div>

          <!-- Panel de mensajes -->
          <div class="chat-messages-panel" id="messagesPanel" style="display:none;">
            <div class="chat-messages-area" id="messagesArea"></div>

            <!-- Input -->
            <div class="chat-input-area">
              <div class="chat-input-wrapper">
                <button class="chat-emoji-btn" id="emojiBtn" title="Emojis">😊</button>
                <button class="chat-attach-btn" id="attachBtn" title="Adjuntar archivo">
                  <i class="bi bi-paperclip"></i>
                </button>
                <input type="file" id="fileInput" style="display:none"
                       accept=".pdf,.png,.jpg,.jpeg,.gif,.docx,.xlsx">
                <textarea
                  id="messageInput"
                  placeholder="Escribe un mensaje..."
                  rows="1"
                  maxlength="1000"></textarea>
                <button class="chat-send-btn" id="sendBtn" disabled>
                  <i class="bi bi-send-fill"></i>
                </button>
              </div>
            </div>
          </div>

        </div><!-- /chatModalBody -->
      </div>
    `;

    document.body.appendChild(chatModal);
    createEmojiPicker();

    // Event listeners
    document.getElementById('minimizeChat')      .addEventListener('click', minimizeChatModal);
    document.getElementById('closeChat')         .addEventListener('click', closeChatModal);
    document.getElementById('backToContactsBtn') .addEventListener('click', backToContacts);
    document.getElementById('searchContacts')    .addEventListener('input',  filterContacts);
    document.getElementById('messageInput')      .addEventListener('input',  handleInputChange);
    document.getElementById('messageInput')      .addEventListener('keydown', handleKeyPress);
    document.getElementById('sendBtn')           .addEventListener('click', sendMessage);
    document.getElementById('emojiBtn')          .addEventListener('click', toggleEmojiPicker);
    document.getElementById('attachBtn')         .addEventListener('click', () => document.getElementById('fileInput').click());
    document.getElementById('fileInput')         .addEventListener('change', handleFileUpload);

    loadContacts();
  }

  // ══════════════════════════════════════════════════════════════════════════
  //  VISIBILIDAD DEL MODAL
  // ══════════════════════════════════════════════════════════════════════════
  function toggleChatModal() {
    isOpen ? closeChatModal() : openChatModal();
  }

  function openChatModal() {
    chatModal.style.display = 'flex';
    chatBubble.classList.add('chat-bubble-hidden');
    isOpen = true;
  }

  function minimizeChatModal() {
    chatModal.style.display = 'none';
    chatBubble.classList.remove('chat-bubble-hidden');
    isOpen = false;
  }

  function closeChatModal() {
    chatModal.style.display = 'none';
    chatBubble.classList.remove('chat-bubble-hidden');
    isOpen = false;
    currentContact = null;
    currentContactName = null;
    document.getElementById('contactsPanel').style.display = 'flex';
    document.getElementById('messagesPanel').style.display = 'none';
    document.getElementById('backToContactsBtn').style.display = 'none';
    document.getElementById('modalContactName').textContent = 'Chat Interno';
    document.getElementById('modalContactStatus').textContent = 'Selecciona un contacto';
    document.getElementById('modalAvatar').innerHTML = '<i class="bi bi-chat-dots-fill"></i>';
  }

  // ══════════════════════════════════════════════════════════════════════════
  //  CONTACTOS
  // ══════════════════════════════════════════════════════════════════════════
  async function loadContacts() {
    try {
      const [usersRes, unreadRes] = await Promise.all([
        fetch('/api/chat/users'),
        fetch('/api/chat/unread-count'),
      ]);

      const users = await usersRes.json();
      const unreadData = await unreadRes.json();

      unreadByContact = unreadData.by_contact || {};
      totalUnread     = unreadData.total       || 0;
      allContacts     = Array.isArray(users) ? users : [];

      renderContactsList(allContacts);
      updateBadge(totalUnread);
    } catch (err) {
      console.error('Error loading contacts:', err);
      document.getElementById('contactsList').innerHTML =
        '<div class="chat-error">Error al cargar contactos</div>';
    }
  }

  function renderContactsList(users) {
    const list = document.getElementById('contactsList');
    list.innerHTML = '';

    if (!users || users.length === 0) {
      list.innerHTML = `
        <div class="chat-empty">
          <span class="chat-empty-icon">👥</span>
          No hay otros usuarios registrados en el sistema.
        </div>`;
      return;
    }

    // Ordenar: primero los que tienen no leídos
    const sorted = [...users].sort((a, b) => {
      const ua = unreadByContact[a.usuario] || 0;
      const ub = unreadByContact[b.usuario] || 0;
      return ub - ua;
    });

    sorted.forEach(user => {
      const unread      = unreadByContact[user.usuario] || 0;
      const displayName = user.nombre || user.usuario;
      const initials    = getInitials(displayName);
      const subtitle    = user.secretaria || user.rol || 'Funcionario';

      // Mostrar foto real si existe, si no iniciales
      const avatarHtml = user.foto
        ? `<img src="/${user.foto}?t={{ range(1000,9999)|random if false else '' }}" class="chat-contact-avatar-img" alt="${escapeHtml(initials)}" onerror="this.outerHTML='<div class=\\'chat-contact-avatar\\'>${escapeHtml(initials)}</div>'">`
        : `<div class="chat-contact-avatar">${escapeHtml(initials)}</div>`;

      const item = document.createElement('div');
      item.className = 'chat-contact-item';
      item.dataset.username = user.usuario;
      item.dataset.foto     = user.foto || '';
      item.dataset.nombre   = displayName;
      item.innerHTML = `
        ${avatarHtml}
        <div class="chat-contact-info">
          <div class="chat-contact-name">${escapeHtml(displayName)}</div>
          <div class="chat-contact-role">${escapeHtml(subtitle)}</div>
        </div>
        ${unread > 0
          ? `<span class="chat-contact-unread-badge">${unread > 99 ? '99+' : unread}</span>`
          : `<i class="bi bi-chevron-right"></i>`
        }
      `;
      item.addEventListener('click', () => openChat(user.usuario, displayName, user.foto || ''));
      list.appendChild(item);
    });
  }

  function filterContacts(e) {
    const term = e.target.value.toLowerCase().trim();
    document.querySelectorAll('.chat-contact-item').forEach(item => {
      const name = item.querySelector('.chat-contact-name')?.textContent.toLowerCase() || '';
      const role = item.querySelector('.chat-contact-role')?.textContent.toLowerCase() || '';
      item.style.display = (!term || name.includes(term) || role.includes(term)) ? 'flex' : 'none';
    });
  }

  function backToContacts() {
    document.getElementById('messagesPanel').style.display = 'none';
    document.getElementById('contactsPanel').style.display = 'flex';
    document.getElementById('backToContactsBtn').style.display = 'none';
    document.getElementById('modalContactName').textContent = 'Chat Interno';
    document.getElementById('modalContactStatus').textContent = 'Selecciona un contacto';
    document.getElementById('modalAvatar').innerHTML = '<i class="bi bi-chat-dots-fill"></i>';
    currentContact     = null;
    currentContactName = null;
  }

  // ══════════════════════════════════════════════════════════════════════════
  //  ABRIR CONVERSACIÓN
  // ══════════════════════════════════════════════════════════════════════════
  async function openChat(contactUsername, contactDisplayName, contactFoto) {
    currentContact     = contactUsername;
    currentContactName = contactDisplayName || contactUsername;

    const initials    = getInitials(currentContactName);
    const avatarEl    = document.getElementById('modalAvatar');
    document.getElementById('modalContactName').textContent   = currentContactName;
    document.getElementById('modalContactStatus').textContent = 'Funcionario';

    if (contactFoto && avatarEl) {
      avatarEl.innerHTML = '';
      avatarEl.style.overflow = 'hidden';
      avatarEl.style.padding  = '0';
      const img = document.createElement('img');
      img.src = '/' + contactFoto;
      img.style.cssText = 'width:100%;height:100%;object-fit:cover;';
      img.onerror = () => { avatarEl.innerHTML = ''; avatarEl.textContent = initials; avatarEl.style.overflow = ''; };
      avatarEl.appendChild(img);
    } else if (avatarEl) {
      avatarEl.textContent = initials;
      avatarEl.style.overflow = '';
    }
    document.getElementById('backToContactsBtn').style.display = 'flex';
    document.getElementById('contactsPanel').style.display    = 'none';
    document.getElementById('messagesPanel').style.display    = 'flex';

    await loadMessages(contactUsername);
    await markAsRead(contactUsername);
  }

  async function markAsRead(contactUsername) {
    try {
      await fetch('/api/chat/mark-read', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contact: contactUsername }),
      });
      // Actualizar estado local
      delete unreadByContact[contactUsername];
      totalUnread = Object.values(unreadByContact).reduce((a, b) => a + b, 0);
      updateBadge(totalUnread);

      // Quitar badge del ítem de contacto
      const item = document.querySelector(`[data-username="${contactUsername}"]`);
      if (item) {
        const badge = item.querySelector('.chat-contact-unread-badge');
        if (badge) {
          const icon = document.createElement('i');
          icon.className = 'bi bi-chevron-right';
          badge.replaceWith(icon);
        }
      }
    } catch (e) {
      // silencioso
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  //  MENSAJES
  // ══════════════════════════════════════════════════════════════════════════
  async function loadMessages(contactUsername) {
    try {
      const res = await fetch(`/api/chat/messages?user=${encodeURIComponent(contactUsername)}`);
      const data = await res.json();
      const messages = data.messages || [];

      const area = document.getElementById('messagesArea');
      area.innerHTML = '';

      if (messages.length === 0) {
        area.innerHTML = `
          <div class="chat-empty">
            <span class="chat-empty-icon">💬</span>
            No hay mensajes aún. ¡Inicia la conversación!
          </div>`;
        return;
      }

      messages.forEach(msg => {
        area.insertAdjacentHTML('beforeend', renderMessageHtml(msg, contactUsername));
      });

      area.scrollTop = area.scrollHeight;
    } catch (err) {
      console.error('Error loading messages:', err);
    }
  }

  function renderMessageHtml(msg, contactUsername) {
    const isSent   = msg.from !== contactUsername;
    const cssClass = isSent ? 'chat-message-sent' : 'chat-message-received';
    const timeStr  = formatTime(msg.timestamp);

    let bubbleContent;
    const fileMatch = typeof msg.message === 'string' &&
      msg.message.match(/^\[FILE:([^|]+)\|([^|]+)\|([^\]]+)\]$/);

    if (fileMatch) {
      const [, safeName, originalName, ext] = fileMatch;
      const fileUrl  = `/static/chat_uploads/${safeName}`;
      const isImage  = ['png', 'jpg', 'jpeg', 'gif'].includes(ext.toLowerCase());

      if (isImage) {
        bubbleContent = `
          <div class="chat-message-text">
            <img src="${fileUrl}" alt="${escapeHtml(originalName)}"
                 class="chat-img-preview"
                 onclick="window.open('${fileUrl}', '_blank')">
          </div>
          <div class="chat-message-time">${timeStr}</div>`;
      } else {
        bubbleContent = `
          <div class="chat-message-text">
            <a href="${fileUrl}" download="${escapeHtml(originalName)}" class="chat-file-link">
              <i class="bi bi-file-earmark-arrow-down"></i>
              ${escapeHtml(originalName)}
            </a>
          </div>
          <div class="chat-message-time">${timeStr}</div>`;
      }
    } else {
      bubbleContent = `
        <div class="chat-message-text">${escapeHtml(msg.message || '')}</div>
        <div class="chat-message-time">${timeStr}</div>`;
    }

    return `
      <div class="chat-message ${cssClass}">
        <div class="chat-message-bubble">${bubbleContent}</div>
      </div>`;
  }

  // ══════════════════════════════════════════════════════════════════════════
  //  INPUT — TEXTO
  // ══════════════════════════════════════════════════════════════════════════
  function handleInputChange(e) {
    const input = e.target;
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 100) + 'px';
    document.getElementById('sendBtn').disabled = input.value.trim() === '';
  }

  function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  async function sendMessage() {
    const input   = document.getElementById('messageInput');
    const message = input.value.trim();
    if (!message || !currentContact) return;

    try {
      const res = await fetch('/api/chat/send', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ to: currentContact, message }),
      });

      if (res.ok) {
        input.value = '';
        input.style.height = 'auto';
        document.getElementById('sendBtn').disabled = true;
        await loadMessages(currentContact);
      }
    } catch (err) {
      console.error('Error sending message:', err);
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  //  INPUT — ARCHIVO
  // ══════════════════════════════════════════════════════════════════════════
  async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file || !currentContact) return;

    if (file.size > 5 * 1024 * 1024) {
      alert('El archivo no puede superar 5 MB.');
      e.target.value = '';
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('to', currentContact);

    try {
      const res = await fetch('/api/chat/upload', { method: 'POST', body: formData });
      e.target.value = '';
      if (res.ok) {
        await loadMessages(currentContact);
      } else {
        const err = await res.json().catch(() => ({}));
        alert('Error: ' + (err.error || 'No se pudo subir el archivo'));
      }
    } catch (err) {
      console.error('Upload error:', err);
      alert('Error al subir el archivo');
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  //  EMOJI PICKER
  // ══════════════════════════════════════════════════════════════════════════
  function createEmojiPicker() {
    const picker = document.createElement('div');
    picker.id = 'emojiPicker';
    picker.className = 'emoji-picker';
    picker.style.display = 'none';

    const emojis = [
      '😀','😃','😄','😁','😆','😅','😂','🤣',
      '😊','😇','😋','😎','😍','😘','😗','😙',
      '😉','🤔','🤨','🤗','🤭','🥱','🥳','😏',
      '😒','😞','😔','😟','😕','🙁','☹️','😣',
      '😖','😫','😩','😢','😭','😤','😠','😡',
      '👍','👎','👏','🙏','❤️','💔','👌','✌️',
      '👊','✊','🤝','👋','👀','💡','🎉','✅',
    ];

    emojis.forEach(emoji => {
      const btn = document.createElement('button');
      btn.className = 'emoji-btn';
      btn.textContent = emoji;
      btn.onclick = () => insertEmoji(emoji);
      picker.appendChild(btn);
    });

    document.body.appendChild(picker);
  }

  function toggleEmojiPicker() {
    const picker  = document.getElementById('emojiPicker');
    const btnEl   = document.getElementById('emojiBtn');
    if (picker.style.display === 'none') {
      const rect = btnEl.getBoundingClientRect();
      picker.style.bottom = (window.innerHeight - rect.top + 8) + 'px';
      picker.style.left   = rect.left + 'px';
      picker.style.display = 'grid';
    } else {
      picker.style.display = 'none';
    }
  }

  function insertEmoji(emoji) {
    const input = document.getElementById('messageInput');
    input.value += emoji;
    input.focus();
    handleInputChange({ target: input });
    document.getElementById('emojiPicker').style.display = 'none';
  }

  // Cerrar picker al hacer clic fuera
  document.addEventListener('click', e => {
    const picker = document.getElementById('emojiPicker');
    const btn    = document.getElementById('emojiBtn');
    if (picker && btn && !picker.contains(e.target) && !btn.contains(e.target)) {
      picker.style.display = 'none';
    }
  });

  // ══════════════════════════════════════════════════════════════════════════
  //  POLLING DE NO LEÍDOS
  // ══════════════════════════════════════════════════════════════════════════
  async function checkNewMessages() {
    try {
      const res  = await fetch('/api/chat/unread-count');
      const data = await res.json();

      const newUnread = data.by_contact || {};
      const newTotal  = data.total      || 0;

      // Detectar nuevos mensajes del contacto abierto
      if (currentContact && (newUnread[currentContact] || 0) > 0) {
        await loadMessages(currentContact);
        await markAsRead(currentContact);
      } else {
        unreadByContact = newUnread;
        totalUnread     = newTotal;
        updateBadge(totalUnread);

        // Actualizar badges de contactos visibles
        document.querySelectorAll('.chat-contact-item').forEach(item => {
          const uname = item.dataset.username;
          const count = unreadByContact[uname] || 0;
          let badge = item.querySelector('.chat-contact-unread-badge');
          let icon  = item.querySelector('i.bi-chevron-right');

          if (count > 0) {
            if (!badge) {
              if (icon) icon.remove();
              const span = document.createElement('span');
              span.className = 'chat-contact-unread-badge';
              item.appendChild(span);
              badge = span;
            }
            badge.textContent = count > 99 ? '99+' : count;
          } else if (badge) {
            const i = document.createElement('i');
            i.className = 'bi bi-chevron-right';
            badge.replaceWith(i);
          }
        });
      }
    } catch (err) {
      console.error('Error polling messages:', err);
    }
  }

  function updateBadge(count) {
    const badge = document.getElementById('chatBadge');
    if (!badge) return;
    if (count > 0) {
      badge.textContent = count > 99 ? '99+' : count;
      badge.style.display = 'flex';
      chatBubble.classList.add('chat-bubble-pulse');
    } else {
      badge.style.display = 'none';
      chatBubble.classList.remove('chat-bubble-pulse');
    }
  }

  function startMessagePolling() {
    checkNewMessages();
    messageCheckInterval = setInterval(checkNewMessages, 15000);
  }

  // ══════════════════════════════════════════════════════════════════════════
  //  UTILIDADES
  // ══════════════════════════════════════════════════════════════════════════
  function getInitials(name) {
    if (!name) return '?';
    const words = name.trim().split(/\s+/);
    if (words.length === 1) return words[0].substring(0, 2).toUpperCase();
    return (words[0][0] + words[words.length - 1][0]).toUpperCase();
  }

  function formatTime(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp.replace(' ', 'T'));
    if (isNaN(date)) return timestamp.substring(11, 16) || '';
    const h = date.getHours().toString().padStart(2, '0');
    const m = date.getMinutes().toString().padStart(2, '0');
    return `${h}:${m}`;
  }

  function escapeHtml(text) {
    if (typeof text !== 'string') return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

})();
