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

  function renderMarkdownSafeHTML(text) {
    // Split text by markdown bold patterns and newlines while preserving formatting info
    const parts = [];
    let lastIndex = 0;

    // Process **bold** patterns
    const boldRegex = /\*\*(.*?)\*\*/g;
    let match;
    const boldMatches = [];
    while ((match = boldRegex.exec(text)) !== null) {
      boldMatches.push({ start: match.index, end: match.index + match[0].length, content: match[1] });
    }

    // Build fragment: text with safe bold markup and line breaks
    const frag = document.createDocumentFragment();
    let currentIdx = 0;
    const lines = text.split('\n');

    lines.forEach((line, lineIdx) => {
      // Process bold patterns in this line
      let lineStart = 0;
      let inBold = false;
      let boldIdx = 0;

      // Simple bold replacement: find ** pairs in this line only
      const lineBoldRegex = /\*\*(.*?)\*\*/g;
      let lineMatch;
      let lastLineIdx = 0;
      const fragments = [];

      while ((lineMatch = lineBoldRegex.exec(line)) !== null) {
        // Add text before bold
        if (lineMatch.index > lastLineIdx) {
          fragments.push({ type: 'text', content: line.substring(lastLineIdx, lineMatch.index) });
        }
        // Add bold text
        fragments.push({ type: 'bold', content: lineMatch[1] });
        lastLineIdx = lineMatch.index + lineMatch[0].length;
      }
      // Add remaining text
      if (lastLineIdx < line.length) {
        fragments.push({ type: 'text', content: line.substring(lastLineIdx) });
      }

      // Create DOM nodes for this line
      fragments.forEach(frag_item => {
        if (frag_item.type === 'text') {
          frag.appendChild(document.createTextNode(frag_item.content));
        } else if (frag_item.type === 'bold') {
          const bold = document.createElement('b');
          bold.textContent = frag_item.content;
          frag.appendChild(bold);
        }
      });

      // Add line break between lines (but not after last line)
      if (lineIdx < lines.length - 1) {
        frag.appendChild(document.createElement('br'));
      }
    });

    return frag;
  }

  function createBubble(text, sender) {
    const wrap = document.createElement('div');
    wrap.className = `chat-bubble-wrap ${sender}`;

    const icon = document.createElement('div');
    icon.className = 'chat-bubble-icon';
    // Hardcoded content is safe
    icon.innerHTML = sender === 'bot'
      ? '<i class="fas fa-robot"></i>'
      : '<i class="fas fa-user"></i>';

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';

    // Safely render text with markdown formatting using DOM methods (prevents XSS)
    bubble.appendChild(renderMarkdownSafeHTML(text));

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
      // Get AI service URL from data-attribute (configurable per deployment)
      const aiServiceUrl = panel.dataset.aiServiceUrl;

      // Connect to the FastAPI AI microservice
      const response = await fetch(aiServiceUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: conversationHistory })
      });

      console.log("AI service url at: ", aiServiceUrl)
      if (!response.ok) {
        hideTyping();
        throw new Error(`Server returned ${response.status}`);
      }

      // Create an empty bot bubble to stream into
      const botBubbleWrap = createBubble('', 'bot');
      const botBubbleContent = botBubbleWrap.querySelector('.chat-bubble');
      let hasStartedStreaming = false;

      // Read the SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let botFullResponse = '';
      let streamBuffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          if (!hasStartedStreaming) {
            hideTyping();
            messages.appendChild(botBubbleWrap);
          }
          break;
        }

        // Normalize CRLF to LF so indexOf('\n\n') correctly detects SSE event boundaries
        streamBuffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n');

        // SSE messages are split by double newline
        let boundaryIndex;
        while ((boundaryIndex = streamBuffer.indexOf('\n\n')) >= 0) {
          const event = streamBuffer.substring(0, boundaryIndex);
          streamBuffer = streamBuffer.substring(boundaryIndex + 2);
          if (!event.trim()) continue;

          if (event.startsWith('event: message') || event.startsWith('event: done') || event.startsWith('event: error')) {
            // Find the data line for this event
            const dataMatch = event.match(/data:\s+(.*)$/m);
            if (dataMatch) {
              const dataStr = dataMatch[1];
              try {
                const dataObj = JSON.parse(dataStr);

                // Handle done event
                if (event.startsWith('event: done')) {
                  if (!hasStartedStreaming) {
                    hideTyping();
                    messages.appendChild(botBubbleWrap);
                  }
                  break; // Stream complete
                }

                // Handle error event
                if (event.startsWith('event: error')) {
                  if (!hasStartedStreaming) {
                    hideTyping();
                  }
                  const errorMsg = dataObj.error || 'An error occurred while processing your request.';
                  console.error('AI Service error:', errorMsg);
                  if (!hasStartedStreaming) {
                    messages.appendChild(botBubbleWrap);
                  }
                  break;
                }

                // Handle message event
                const content = dataObj.content || '';

                if (!hasStartedStreaming) {
                  hideTyping();
                  messages.appendChild(botBubbleWrap);
                  hasStartedStreaming = true;
                }

                // Append chunk and update UI
                botFullResponse += content;

                // Safely update bubble with formatted content (prevents XSS)
                botBubbleContent.innerHTML = ''; // Clear previous content
                botBubbleContent.appendChild(renderMarkdownSafeHTML(botFullResponse));
                scrollToBottom();

              } catch (e) {
                console.warn('Failed to parse SSE data chunk:', dataStr, e);
              }
            }
          }
        }
      }

      // Save the bot's final answer to history
      conversationHistory.push({ role: "assistant", content: botFullResponse });

    } catch (error) {
      console.error('Chat error:', error);
      hideTyping();
      addMessage("Sorry, I'm unable to reach the AI service. Please try again in a moment.", 'bot');
    } finally {
      isTyping = false;
      // Recompute button state: disabled if input is empty, enabled if input has text
      sendBtn.disabled = input.value.trim().length === 0;
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
