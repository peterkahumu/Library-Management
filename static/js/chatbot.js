/**
 * Library Management Chatbot
 * Pre-determined response engine with keyword matching.
 * Ready to be swapped out for a live AI API.
 */

(function () {
  'use strict';

  /* ── Knowledge Base ──────────────────────────────────────── */
  const RESPONSES = [
    {
      patterns: [/\b(hi|hello|hey|good\s*(morning|afternoon|evening)|greetings)\b/i],
      replies: [
        "Hello! 👋 I'm LibraBot, your library assistant. How can I help you today?",
        "Hi there! 📚 Welcome to the Library Management System. What can I help you with?",
      ],
    },
    {
      patterns: [/\bborrow(ing)?\b|\bcheck\s*out\b|\bhow\s*(do\s*i|to)\s*(get|borrow|take)\b/i],
      replies: [
        "To borrow a book:\n1. Browse the <b>Catalogue</b> and open the book you want.\n2. Click <b>Borrow Book</b>.\n3. The librarian will process your request and update the status.\n\nEach student can borrow up to <b>5 books</b> at a time.",
      ],
    },
    {
      patterns: [/\breturn(ing)?\b|\bdue\s*date\b|\boverdue\b/i],
      replies: [
        "To return a book, bring it to the library desk. The librarian will mark it as returned in the system.\n\n⚠️ Books not returned by the due date attract a daily fine — check <b>My Books</b> for your current due dates.",
      ],
    },
    {
      patterns: [/\bfine(s)?\b|\bfee(s)?\b|\bpenalt(y|ies)\b|\bpay(ment)?\b/i],
      replies: [
        "Fines are charged for overdue books. You can view any outstanding fines in your <b>Dashboard</b> under the fines section.\n\nContact the librarian to settle a fine in person.",
      ],
    },
    {
      patterns: [/\bcatalogue\b|\bsearch\b|\bfind\s*(a\s*)?book\b|\bavailab(le|ility)\b/i],
      replies: [
        "You can browse all available books in the <b>Catalogue</b> section. Use the search bar and genre filters to narrow your results.\n\nBooks showing <span class='text-success fw-bold'>Available</span> can be borrowed right away!",
      ],
    },
    {
      patterns: [/\bgoogle\s*books\b|\bexternal\b|\bonline\s*book\b/i],
      replies: [
        "The <b>Google Books</b> section lets you search millions of books online. You can view details and previews directly within the system.",
      ],
    },
    {
      patterns: [/\bmy\s*books?\b|\bborrowed\b|\bcurrent(ly)?\s*(reading|borrow)\b/i],
      replies: [
        "Head to <b>My Books</b> in the navigation to see all books you've borrowed, their due dates, and return status.",
      ],
    },
    {
      patterns: [/\brenew\b|\bextension\b|\bmore\s*time\b/i],
      replies: [
        "Book renewals must be requested through the librarian at the desk. You can reach out before your due date to avoid fines.",
      ],
    },
    {
      patterns: [/\baccount\b|\bprofile\b|\bpassword\b|\blogin\b|\bsign\s*(in|up)\b/i],
      replies: [
        "You can manage your account from the <b>profile menu</b> (top-right on desktop, or the Menu tab on mobile). Options include changing your password and viewing your role.",
      ],
    },
    {
      patterns: [/\bhour(s)?\b|\bopen(ing)?\b|\bwhen\b.*\bopen\b|\bschedule\b|\btiming\b/i],
      replies: [
        "📅 Library hours:\n• Monday – Friday: 8:00 AM – 6:00 PM\n• Saturday: 9:00 AM – 1:00 PM\n• Sunday & Public Holidays: Closed\n\nFor holiday-specific changes, check the notice board.",
      ],
    },
    {
      patterns: [/\badmin\b|\blibrarian\b|\bstaff\b|\bcontact\b|\bhelp\b|\bsupport\b/i],
      replies: [
        "For assistance, you can visit the library desk during opening hours or ask any staff member. Admins and Librarians can manage your account directly from their dashboards.",
      ],
    },
    {
      patterns: [/\bthank(s|you)?\b|\bawesome\b|\bgreat\b|\bperfect\b|\bcheers\b/i],
      replies: [
        "You're welcome! 😊 Let me know if there's anything else I can help with.",
        "Happy to help! 📚 Feel free to ask anytime.",
      ],
    },
    {
      patterns: [/\bbye\b|\bgoodbye\b|\bsee\s*you\b|\btake\s*care\b/i],
      replies: [
        "Goodbye! 👋 Happy reading!",
        "See you! Come back anytime you need help. 📖",
      ],
    },
  ];

  const FALLBACK = [
    "I'm not sure about that one. Try asking about borrowing, returns, fines, the catalogue, or your account.",
    "Hmm, I didn't quite catch that. You can ask me about borrowing books, due dates, fines, or opening hours.",
    "That's outside my knowledge for now. 😅 Try <b>How do I borrow a book?</b> or <b>What are the library hours?</b>",
  ];

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
    bubble.innerHTML = text.replace(/\n/g, '<br>');

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
    suggestBox.innerHTML = '';
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
  function sendMessage(text) {
    text = (text || input.value).trim();
    if (!text || isTyping) return;

    if (suggestBox) suggestBox.style.display = 'none';
    addMessage(text, 'user');
    input.value = '';
    input.style.height = 'auto';
    sendBtn.disabled = true;
    isTyping = true;

    const typingEl = showTyping();

    // Simulate "thinking" delay
    const delay = 700 + Math.random() * 600;
    setTimeout(() => {
      hideTyping();
      const reply = getReply(text);
      addMessage(reply, 'bot');
      isTyping = false;
      sendBtn.disabled = false;
    }, delay);
  }

  /* ── Panel Toggle ────────────────────────────────────────── */
  function openPanel() {
    isOpen = true;
    panel.classList.add('open');
    fab.classList.add('active');
    fab.querySelector('i').className = 'fas fa-times';
    if (badge) badge.classList.remove('visible');
    input.focus();
  }

  function closePanel() {
    isOpen = false;
    panel.classList.remove('open');
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
