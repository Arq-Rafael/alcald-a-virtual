/**
 * Chat Bubble - iMessage Style
 * Burbuja flotante para Chat Interno Municipal
 */

(function() {
  'use strict';

  let chatBubble = null;
  let chatModal = null;
  let unreadCount = 0;
  let isOpen = false;
  let currentContact = null;
  let messageCheckInterval = null;

  // Inicializar cuando el DOM esté listo
  document.addEventListener('DOMContentLoaded', function() {
    createChatBubble();
    createChatModal();
    startMessagePolling();
  });

  function createChatBubble() {
    chatBubble = document.createElement('div');
    chatBubble.id = 'chatBubble';
    chatBubble.className = 'chat-bubble';
    chatBubble.innerHTML = `
      <div class="chat-bubble-icon">
        <i class="bi bi-chat-dots-fill"></i>
      </div>
      <div class="chat-bubble-badge" id="chatBadge" style="display: none;">0</div>
    `;
    
    chatBubble.addEventListener('click', toggleChatModal);
    document.body.appendChild(chatBubble);
  }

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
            <button class="chat-back-btn" id="backToContactsBtn" style="display: none;" title="Volver">
              <i class="bi bi-chevron-left"></i>
            </button>
            <div class="chat-modal-avatar" id="modalAvatar">
              <i class="bi bi-chat-dots-fill"></i>
            </div>
            <div class="chat-modal-header-info">
              <h5 id="modalContactName">Chat Interno</h5>
              <p id="modalContactStatus">Selecciona un contacto</p>
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

        <!-- Content Area -->
        <div class="chat-modal-body" id="chatModalBody">
          <!-- Contacts List -->
          <div class="chat-contacts-panel" id="contactsPanel">
            <div class="chat-contacts-search">
              <i class="bi bi-search"></i>
              <input type="text" id="searchContacts" placeholder="Buscar contactos...">
            </div>
            <div class="chat-contacts-list" id="contactsList">
              <div class="chat-loading">Cargando contactos...</div>
            </div>
          </div>

          <!-- Messages Area -->
          <div class="chat-messages-panel" id="messagesPanel" style="display: none;">
            <div class="chat-messages-area" id="messagesArea">
              <!-- Messages will be loaded here -->
            </div>
            
            <!-- Input Area -->
            <div class="chat-input-area">
              <div class="chat-input-wrapper">
                <button class="chat-emoji-btn" id="emojiBtn">😊</button>
                <textarea 
                  id="messageInput" 
                  placeholder="Escribe un mensaje..." 
                  rows="1"
                  maxlength="500"></textarea>
                <button class="chat-send-btn" id="sendBtn" disabled>
                  <i class="bi bi-send-fill"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(chatModal);
    
    // Crear emoji picker
    createEmojiPicker();
    
    // Event listeners
    document.getElementById('minimizeChat').addEventListener('click', minimizeChatModal);
    document.getElementById('closeChat').addEventListener('click', closeChatModal);
    document.getElementById('backToContactsBtn').addEventListener('click', backToContacts);
    document.getElementById('searchContacts').addEventListener('input', filterContacts);
    document.getElementById('messageInput').addEventListener('input', handleInputChange);
    document.getElementById('sendBtn').addEventListener('click', sendMessage);
    document.getElementById('messageInput').addEventListener('keydown', handleKeyPress);
    document.getElementById('emojiBtn').addEventListener('click', toggleEmojiPicker);
    
    // Load contacts
    loadContacts();
  }

  function toggleChatModal() {
    if (isOpen) {
      closeChatModal();
    } else {
      openChatModal();
    }
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
    document.getElementById('contactsPanel').style.display = 'block';
    document.getElementById('messagesPanel').style.display = 'none';
  }

  async function loadContacts() {
    try {
      const response = await fetch('/api/chat/users');
      const users = await response.json();
      
      const contactsList = document.getElementById('contactsList');
      contactsList.innerHTML = '';
      
      users.forEach(user => {
        const contactItem = document.createElement('div');
        contactItem.className = 'chat-contact-item';
        contactItem.innerHTML = `
          <div class="chat-contact-avatar">
            ${user.usuario.charAt(0).toUpperCase()}
          </div>
          <div class="chat-contact-info">
            <div class="chat-contact-name">${user.usuario}</div>
            <div class="chat-contact-role">${user.rol}</div>
          </div>
          <i class="bi bi-chevron-right"></i>
        `;
        
        contactItem.addEventListener('click', () => openChat(user.usuario));
        contactsList.appendChild(contactItem);
      });
    } catch (error) {
      console.error('Error loading contacts:', error);
      document.getElementById('contactsList').innerHTML = 
        '<div class="chat-error">Error al cargar contactos</div>';
    }
  }

  function filterContacts(e) {
    const searchTerm = e.target.value.toLowerCase();
    const contacts = document.querySelectorAll('.chat-contact-item');
    
    contacts.forEach(contact => {
      const name = contact.querySelector('.chat-contact-name').textContent.toLowerCase();
      contact.style.display = name.includes(searchTerm) ? 'flex' : 'none';
    });
  }

  function backToContacts() {
    // Hide messages panel and show contacts
    document.getElementById('messagesPanel').style.display = 'none';
    document.getElementById('contactsPanel').style.display = 'flex';
    
    // Hide back button
    document.getElementById('backToContactsBtn').style.display = 'none';
    
    // Reset header
    document.getElementById('modalContactName').textContent = 'Chat Interno';
    document.getElementById('modalContactStatus').textContent = 'Selecciona un contacto';
    document.getElementById('modalAvatar').innerHTML = '<i class="bi bi-chat-dots-fill"></i>';
    
    currentContact = null;
  }

  async function openChat(contactUsername) {
    currentContact = contactUsername;
    
    // Update header
    document.getElementById('modalContactName').textContent = contactUsername;
    document.getElementById('modalContactStatus').textContent = 'En línea';
    document.getElementById('modalAvatar').textContent = contactUsername.charAt(0).toUpperCase();
    
    // Show back button
    document.getElementById('backToContactsBtn').style.display = 'flex';
    
    // Show messages panel
    document.getElementById('contactsPanel').style.display = 'none';
    document.getElementById('messagesPanel').style.display = 'flex';
    
    // Load messages
    await loadMessages(contactUsername);
  }

  async function loadMessages(contactUsername) {
    try {
      const response = await fetch(`/api/chat/messages?user=${contactUsername}`);
      const data = await response.json();
      
      // El API devuelve {messages: [...]}
      const messages = data.messages || [];
      
      console.log('Mensajes cargados:', messages.length, messages);
      
      const messagesArea = document.getElementById('messagesArea');
      messagesArea.innerHTML = '';
      
      if (messages.length === 0) {
        messagesArea.innerHTML = '<div style="text-align: center; color: #6b7280; padding: 2rem;">No hay mensajes aún. ¡Inicia la conversación!</div>';
        return;
      }
      
      messages.forEach(msg => {
        const messageDiv = document.createElement('div');
        // Usar 'from' en lugar de 'sender'
        messageDiv.className = `chat-message ${msg.from === contactUsername ? 'chat-message-received' : 'chat-message-sent'}`;
        messageDiv.innerHTML = `
          <div class="chat-message-bubble">
            <div class="chat-message-text">${escapeHtml(msg.message)}</div>
            <div class="chat-message-time">${formatTime(msg.timestamp)}</div>
          </div>
        `;
        messagesArea.appendChild(messageDiv);
        console.log('Mensaje añadido:', msg.message);
      });
      
      // Scroll to bottom
      messagesArea.scrollTop = messagesArea.scrollHeight;
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  }

  function handleInputChange(e) {
    const input = e.target;
    const sendBtn = document.getElementById('sendBtn');
    
    // Auto-resize textarea
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 100) + 'px';
    
    // Enable/disable send button
    sendBtn.disabled = input.value.trim() === '';
  }

  function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  function createEmojiPicker() {
    const emojiPicker = document.createElement('div');
    emojiPicker.id = 'emojiPicker';
    emojiPicker.className = 'emoji-picker';
    emojiPicker.style.display = 'none';
    
    const emojis = [
      '😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣',
      '😊', '😇', '😋', '😎', '😍', '😘', '😗', '😙',
      '😉', '🤔', '🤨', '🤗', '🤭', '🥱', '🥳', '😏',
      '😒', '😞', '😔', '😟', '😕', '🙁', '☹️', '😣',
      '😖', '😫', '😩', '😢', '😭', '😤', '😠', '😡',
      '👍', '👎', '👏', '🙏', '❤️', '💔', '👌', '✌️',
      '👊', '✊', '🤝', '👋', '🤚', '👀', '💩', '🎉'
    ];
    
    emojis.forEach(emoji => {
      const btn = document.createElement('button');
      btn.className = 'emoji-btn';
      btn.textContent = emoji;
      btn.onclick = () => insertEmoji(emoji);
      emojiPicker.appendChild(btn);
    });
    
    document.body.appendChild(emojiPicker);
  }

  function toggleEmojiPicker() {
    const picker = document.getElementById('emojiPicker');
    const emojiBtn = document.getElementById('emojiBtn');
    
    if (picker.style.display === 'none') {
      // Posicionar el picker cerca del botón
      const rect = emojiBtn.getBoundingClientRect();
      picker.style.bottom = (window.innerHeight - rect.top + 10) + 'px';
      picker.style.left = rect.left + 'px';
      picker.style.display = 'grid';
    } else {
      picker.style.display = 'none';
    }
  }

  function insertEmoji(emoji) {
    const input = document.getElementById('messageInput');
    input.value += emoji;
    input.focus();
    
    // Trigger input change to enable send button
    handleInputChange({ target: input });
    
    // Cerrar picker
    document.getElementById('emojiPicker').style.display = 'none';
  }

  // Cerrar picker al hacer click fuera
  document.addEventListener('click', (e) => {
    const picker = document.getElementById('emojiPicker');
    const emojiBtn = document.getElementById('emojiBtn');
    
    if (picker && emojiBtn && 
        !picker.contains(e.target) && 
        !emojiBtn.contains(e.target)) {
      picker.style.display = 'none';
    }
  });

  async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message || !currentContact) return;
    
    try {
      const response = await fetch('/api/chat/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to: currentContact,
          message: message
        })
      });
      
      if (response.ok) {
        input.value = '';
        input.style.height = 'auto';
        document.getElementById('sendBtn').disabled = true;
        
        // Reload messages
        await loadMessages(currentContact);
      }
    } catch (error) {
      console.error('Error sending message:', error);
    }
  }

  async function checkNewMessages() {
    try {
      const response = await fetch('/api/chat/last');
      const data = await response.json();
      
      if (data.count > 0) {
        unreadCount = data.count;
        updateBadge(unreadCount);
      }
    } catch (error) {
      console.error('Error checking messages:', error);
    }
  }

  function updateBadge(count) {
    const badge = document.getElementById('chatBadge');
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
    // Check for new messages every 10 seconds
    messageCheckInterval = setInterval(checkNewMessages, 10000);
    checkNewMessages(); // Check immediately
  }

  function formatTime(timestamp) {
    const date = new Date(timestamp);
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
})();
