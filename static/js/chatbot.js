/**
 * Library Management Chatbot
 */

(function () {
  'use strict';

  /* ── Basic user suggestions. ──────────────────────────────────────── */
  const SUGGESTIONS = [
    "How do I borrow a book?",
    "Library hours",
    "Check my fines",
    "Search catalogue",
    "Return a book",
  ];

  /* ── State ───────────────────────────────────────────────── */
  let isOpen = false;
  let isTyping = false;
  let conversationHistory = []; // Keeps track of messages for API context

  /* ── DOM refs ────────────────────────────────────────────── */
  const fab = document.getElementById('chatbot-fab');
  const panel = document.getElementById('chatbot-panel');
  const closeBtn = document.getElementById('chatbot-close-btn');
  const messages = document.getElementById('chatbot-messages');
  const input = document.getElementById('chatbot-input');
  const sendBtn = document.getElementById('chatbot-send-btn');
  const badge = fab ? fab.querySelector('.chat-badge') : null;
  const suggestBox = document.getElementById('chatbot-suggestions');

  if (!fab || !panel) return; // chatbot HTML not present

  /* ── Helpers ─────────────────────────────────────────────── */
  function rand(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
  }

  function scrollToBottom() {
    messages.scrollTop = messages.scrollHeight;
  }

  function createBubble(text, sender) {
    const wrap = document.createElement('div');
    wrap.className = `chat-bubble-wrap ${sender}`;

    const icon = document.createElement('div');
    icon.className = 'chat-bubble-icon';
    icon.innerHTML = sender === 'bot'
      ? '<i class="fas fa-robot"></i>'
      : '<i class="fas fa-user"></i>';

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';

    // Convert markdown line returns to <br> to handle markdown lists
    bubble.innerHTML = text.replace(/\n((?!(<br>)))/g, '<br>');

    wrap.appendChild(icon);
    wrap.appendChild(bubble);
    return wrap;
  }

  function showTyping() {
    const wrap = document.createElement('div');
    wrap.className = 'chat-bubble-wrap bot';
    wrap.id = 'typing-indicator-wrap';

    const icon = document.createElement('div');
    icon.className = 'chat-bubble-icon';
    icon.innerHTML = '<i class="fas fa-robot"></i>';

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    bubble.innerHTML = '<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>';

    wrap.appendChild(icon);
    wrap.appendChild(bubble);
    messages.appendChild(wrap);
    scrollToBottom();
    return wrap;
  }

  function hideTyping() {
    const el = document.getElementById('typing-indicator-wrap');
    if (el) el.remove();
  }

  function addMessage(text, sender) {
    const bubble = createBubble(text, sender);
    messages.appendChild(bubble);
    scrollToBottom();
  }

  function getReply(text) {
    for (const entry of RESPONSES) {
      for (const pattern of entry.patterns) {
        if (pattern.test(text)) {
          return rand(entry.replies);
        }
      }
    }
    return rand(FALLBACK);
  }

  function buildSuggestions() {
    if (!suggestBox) return;
    // Don't rebuild if already built to save DOM ops
    if (suggestBox.children.length > 0) return;
    SUGGESTIONS.forEach(s => {
      const chip = document.createElement('button');
      chip.className = 'chat-suggestion-chip';
      chip.textContent = s;
      chip.addEventListener('click', () => {
        sendMessage(s);
        suggestBox.style.display = 'none';
      });
      suggestBox.appendChild(chip);
    });
  }

  /* ── Send Logic ──────────────────────────────────────────── */
  async function sendMessage(text) {
    text = (text || input.value).trim();
    if (!text || isTyping) return;

    if (suggestBox) suggestBox.style.display = 'none';
    addMessage(text, 'user');
    conversationHistory.push({ role: "user", content: text });

    input.value = '';
    input.style.height = 'auto';
    sendBtn.disabled = true;
    isTyping = true;

    showTyping();

    try {
      // Connect to the FastAPI AI microservice
      const response = await fetch('http://localhost:8001/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: conversationHistory })
      });

      hideTyping();

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      // Create an empty bot bubble to stream into
      const botBubbleWrap = createBubble('', 'bot');
      messages.appendChild(botBubbleWrap);
      const botBubbleContent = botBubbleWrap.querySelector('.chat-bubble');

      // Read the SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let botFullResponse = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunkStr = decoder.decode(value, { stream: true });

        // SSE messages are split by double newline
        const events = chunkStr.split('\n\n');
        for (const event of events) {
          if (!event.trim()) continue;

          if (event.startsWith('event: message') || event.startsWith('event: done') || event.startsWith('event: error')) {
            // Find the data line for this event
            const dataMatch = event.match(/data:\s+(.+)$/m);
            if (dataMatch) {
              const dataStr = dataMatch[1];
              try {
                const dataObj = JSON.parse(dataStr);
                const content = dataObj.content || '';

                if (content === '[DONE]') {
                  break; // Stream complete
                }

                // Append chunk and update UI
                botFullResponse += content;

                // Extremely basic markdown formatting for stream chunks
                // converts **bold** to <b>bold</b> and \n to <br>
                let htmlOut = botFullResponse
                  .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
                  .replace(/\n/g, '<br>');

                botBubbleContent.innerHTML = htmlOut;
                scrollToBottom();

              } catch (e) { /* ignore parse error on partial chunks if any */ }
            }
          }
        }
      }

      // Save the bot's final answer to history
      conversationHistory.push({ role: "assistant", content: botFullResponse });

    } catch (error) {
      console.error('Chat error:', error);
      hideTyping();
      addMessage("⚠️ Sorry, I'm having trouble connecting to my brain right now. Please try again later.", 'bot');
    } finally {
      isTyping = false;
      sendBtn.disabled = false;
    }
  }

  /* ── Panel Toggle ────────────────────────────────────────── */
  function openPanel() {
    isOpen = true;
    panel.classList.add('open');
    panel.setAttribute('aria-hidden', 'false'); // Fix ARIA hidden focus error
    fab.classList.add('active');
    fab.querySelector('i').className = 'fas fa-times';
    if (badge) badge.classList.remove('visible');
    input.focus();
  }

  function closePanel() {
    isOpen = false;
    panel.classList.remove('open');
    panel.setAttribute('aria-hidden', 'true'); // Hide from ARIA when closed
    fab.classList.remove('active');
    fab.querySelector('i').className = 'fas fa-comments';
  }

  /* ── Event Listeners ─────────────────────────────────────── */
  fab.addEventListener('click', () => (isOpen ? closePanel() : openPanel()));
  closeBtn.addEventListener('click', closePanel);

  sendBtn.addEventListener('click', () => sendMessage());

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Auto-resize textarea
  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 80) + 'px';
    sendBtn.disabled = input.value.trim().length === 0;
  });

  /* ── Initialise ──────────────────────────────────────────── */
  function init() {
    buildSuggestions();
    sendBtn.disabled = true;

    // Welcome message after a brief delay
    setTimeout(() => {
      addMessage("👋 Hi! I'm <b>LibraBot</b>, your library assistant. Ask me anything about borrowing books, fines, the catalogue, or library hours!", 'bot');
    }, 400);

    // Subtle badge after 3s to draw attention if panel is closed
    setTimeout(() => {
      if (!isOpen && badge) badge.classList.add('visible');
    }, 3000);
  }

  init();
})();
