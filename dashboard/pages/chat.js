var _hermesIframeInstance = null;
// Canonical Hermes WebUI origin — the "Open in new tab" target (named tab: reused).
var HERMES_WEBUI_URL = 'https://hermes-webui-gsga.srv1738752.hstgr.cloud/';

async function renderChat() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">AI Chat</h1>
        <p class="page-subtitle">Talk to opencode and Hermes</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="clearChat()">Clear</button>
        <button class="btn" onclick="refreshChat()">Refresh</button>
      </div>
    </div>
    <div class="chat-layout">
      <div class="chat-sidebar">
        <div class="chat-agents-label">Agents</div>
        <div class="chat-agent active" data-agent="opencode" onclick="selectAgent('opencode')">
          <div class="agent-dot online"></div>
          <div>
            <div class="chat-agent-name">opencode</div>
            <div class="chat-agent-desc">Code & DevOps</div>
          </div>
        </div>
        <div class="chat-agent" data-agent="hermes" onclick="selectAgent('hermes')">
          <div class="agent-dot online"></div>
          <div>
            <div class="chat-agent-name">Hermes</div>
            <div class="chat-agent-desc">Memory & Scheduling</div>
          </div>
        </div>
        <div style="margin-top:auto;padding:12px;font-size:11px;color:var(--text-muted);border-top:1px solid var(--border)">
          <div id="chatAgentStatus">opencode • ready</div>
        </div>
      </div>
      <div class="chat-main" id="chatMain">
        <div id="chatMessages" class="chat-messages">
          <div class="chat-welcome">
            <div class="chat-welcome-icon">+</div>
            <div class="chat-welcome-title">Agentic OS Chat</div>
            <div class="chat-welcome-desc">Select an agent on the left and start a conversation.<br>Each agent has different capabilities.</div>
            <div style="display:flex;gap:8px;margin-top:16px;flex-wrap:wrap;justify-content:center">
              <button class="btn btn-sm" onclick="sendQuickPrompt('opencode','Check the system status and running processes')">System Check</button>
              <button class="btn btn-sm" onclick="sendQuickPrompt('hermes','What did I work on recently?')">Recall Memory</button>
            </div>
          </div>
        </div>
        <div class="chat-input-area">
          <div class="chat-context-row" id="chatContextRow" style="margin-bottom:4px;font-size:11px;color:var(--text-muted);display:none;align-items:center;gap:6px">
            <span>Context:</span>
            <select id="chatPageContext" style="background:var(--bg-input);color:var(--text);border:1px solid var(--border);border-radius:6px;font-size:11px;padding:2px 6px" onchange="chatContextChanged()">
              <option value="">none</option>
            </select>
            <span id="chatPageContextNote" style="color:var(--text-muted)"></span>
          </div>
          <div class="chat-agent-indicator" id="chatAgentIndicator">opencode</div>
          <textarea id="chatInput" class="chat-input" rows="1" placeholder="Type a message..." onkeydown="handleChatKey(event)"></textarea>
          <button class="btn btn-primary btn-icon" onclick="sendChatMessage()" id="chatSendBtn" title="Send">&rarr;</button>
        </div>
      </div>
      <div class="chat-iframe-container" id="hermesIframeContainer" style="display:none">
        <div class="chat-embed-bar">
          <span class="chat-embed-label">Hermes WebUI</span>
          <span class="chat-embed-note">live in this pane — same sign-in as the dashboard</span>
          <div class="btn-group" style="margin-left:auto">
            <button class="btn btn-sm" onclick="reloadHermesIframe()">↻ Reload</button>
            <button class="btn btn-sm btn-primary" onclick="openHermesWebUITab()">↗ Open in new tab</button>
          </div>
        </div>
        <div class="chat-embed-frame" id="hermesIframeWrap">
          <div class="chat-iframe-loading" id="hermesIframeLoading">
            <div class="loading-spinner"></div>
            <span>Loading Hermes WebUI...</span>
          </div>
        </div>
      </div>
    </div>
  `;

  window._currentAgent = 'opencode';
  window._chatHistory = [];
  _hermesIframeInstance = null; // rebuild the embed fresh on each page visit
  document.getElementById('chatInput').focus();
  initChatContext();  // AI-generalist: page-aware chat (non-blocking)

  // Update agent status indicators
  try {
    const status = await api.getStatus();
    (status.agents || []).forEach(a => {
      const el = document.querySelector(`.chat-agent[data-agent="${a.name}"]`);
      if (el) {
        const dot = el.querySelector('.agent-dot');
        dot.className = `agent-dot ${a.status}`;
      }
    });
    updateAgentStatusText();
  } catch {}

  // Load chat history
  await refreshChat();
}

// ─── Page-aware chat context (AI-generalist layer, 2026-09 Stage 5b) ──
var CHAT_CTX = { pages: {}, auto: '' };

async function initChatContext() {
  const row = document.getElementById('chatContextRow');
  const sel = document.getElementById('chatPageContext');
  if (!row || !sel) return;
  try {
    const r = await api.fetchSafe('/api/skill-manifest', {}, 8000);
    const pages = (r.data && r.data.pages) || {};
    CHAT_CTX.pages = pages;
    const keys = Object.keys(pages).sort();
    if (!keys.length) return;
    sel.innerHTML = '<option value="">none</option>' + keys.map(k =>
      `<option value="${k}">${escapeHtml(pages[k].title || k)}</option>`).join('');
    // Default to the page the user was on before opening chat.
    const auto = window._lastDataPage && pages[window._lastDataPage] ? window._lastDataPage : '';
    sel.value = auto;
    CHAT_CTX.auto = auto;
    row.style.display = 'flex';
    chatContextChanged();
  } catch (e) { /* manifest endpoint unavailable — chat works without context */ }
}

function chatContextChanged() {
  const sel = document.getElementById('chatPageContext');
  const note = document.getElementById('chatPageContextNote');
  if (!sel || !note) return;
  const p = CHAT_CTX.pages[sel.value];
  note.textContent = p ? `${(p.endpoints || []).length} live endpoints attached` : '';
}

function currentChatContext() {
  const sel = document.getElementById('chatPageContext');
  return sel ? sel.value : '';
}

function selectAgent(agent) {
  window._currentAgent = agent;
  document.querySelectorAll('.chat-agent').forEach(el => el.classList.remove('active'));
  document.querySelector(`.chat-agent[data-agent="${agent}"]`).classList.add('active');
  document.getElementById('chatAgentIndicator').textContent = agent;
  updateAgentStatusText();

  const chatMain = document.getElementById('chatMain');
  const iframeContainer = document.getElementById('hermesIframeContainer');

  if (agent === 'hermes') {
    // Hide chat main, show the Hermes WebUI embed. The iframe loads the real
    // WebUI through the same-origin /hermes-webui/ proxy (the proxied app
    // mounts itself under that path), so it renders in place right here.
    chatMain.style.display = 'none';
    iframeContainer.style.display = 'flex';

    if (!_hermesIframeInstance) {
      _hermesIframeInstance = document.createElement('iframe');
      _hermesIframeInstance.src = '/hermes-webui/';
      _hermesIframeInstance.className = 'chat-iframe';
      _hermesIframeInstance.title = 'Hermes WebUI';
      _hermesIframeInstance.allow = 'clipboard-read; clipboard-write';

      // Hide the loading overlay once the WebUI document has loaded
      _hermesIframeInstance.addEventListener('load', () => {
        const loading = document.getElementById('hermesIframeLoading');
        if (loading) loading.style.display = 'none';
      });

      document.getElementById('hermesIframeWrap').appendChild(_hermesIframeInstance);
    }
  } else {
    // Show chat main, hide iframe
    chatMain.style.display = 'flex';
    iframeContainer.style.display = 'none';
    document.getElementById('chatInput').focus();
  }
}

/** Open the canonical Hermes WebUI in a named tab (first click opens it,
 *  later clicks reuse that tab instead of spawning duplicates). */
function openHermesWebUITab() {
  window.open(HERMES_WEBUI_URL, 'hermes-webui');
}

/** Reload the embedded WebUI pane, keeping the loading overlay visible. */
function reloadHermesIframe() {
  if (!_hermesIframeInstance) return;
  const loading = document.getElementById('hermesIframeLoading');
  if (loading) loading.style.display = 'flex';
  try {
    _hermesIframeInstance.contentWindow.location.reload();
  } catch (e) {
    _hermesIframeInstance.src = '/hermes-webui/';
  }
}

function updateAgentStatusText() {
  const el = document.getElementById('chatAgentStatus');
  if (el && window._currentAgent) {
    const agentEl = document.querySelector(`.chat-agent[data-agent="${window._currentAgent}"]`);
    const dot = agentEl ? agentEl.querySelector('.agent-dot') : null;
    let statusText = 'unknown';
    if (dot) {
      if (dot.classList.contains('online')) {
        statusText = 'online';
      } else if (dot.classList.contains('warning')) {
        statusText = 'warning';
      } else if (dot.classList.contains('offline')) {
        statusText = 'offline';
      }
    }
    el.textContent = `${window._currentAgent} • ${statusText}`;
  }
}

function handleChatKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendChatMessage();
  }
  autoResizeTextarea(e.target);
}

function autoResizeTextarea(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 150) + 'px';
}

async function sendChatMessage() {
  const input = document.getElementById('chatInput');
  const message = input.value.trim();
  if (!message) return;

  const agent = window._currentAgent || 'opencode';
  input.value = '';
  input.style.height = 'auto';

  // If Hermes is selected, the WebUI embed owns its own input box —
  // focus it so the user keeps typing there directly.
  if (agent === 'hermes') {
    if (_hermesIframeInstance) {
      try { _hermesIframeInstance.contentWindow.focus(); } catch (e) { /* ignore */ }
    }
    return;
  }

  // Add user message to chat
  addChatMessage('user', message, agent);

  // Show typing indicator
  const typingId = showTypingIndicator(agent);

  try {
    // Client-side timeout: 200s (slightly more than Hermes' 180s backend timeout)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 200000);
    const r = await api.chat(agent, message, controller, currentChatContext());
    clearTimeout(timeoutId);
    removeTypingIndicator(typingId);
    addChatMessage('assistant', r.response.content, agent);

    // Store in local history
    window._chatHistory.push({ role: 'user', content: message, agent });
    window._chatHistory.push({ role: 'assistant', content: r.response.content, agent });
  } catch (err) {
    removeTypingIndicator(typingId);
    const msg = err.name === 'AbortError' ? 'Request timed out after 200s' : err.message;
    addChatMessage('assistant', `! Error: ${msg}`, agent);
  }
}

function addChatMessage(role, content, agent) {
  const container = document.getElementById('chatMessages');
  const welcome = container.querySelector('.chat-welcome');
  if (welcome) welcome.style.display = 'none';

  const msg = document.createElement('div');
  msg.className = `chat-message ${role}`;
  msg.innerHTML = `
    <div class="chat-message-avatar">${role === 'user' ? '▸' : '◆'}</div>
    <div class="chat-message-body">
      <div class="chat-message-header">
        <span class="chat-message-agent">${role === 'user' ? 'You' : agent}</span>
        <span class="chat-message-time">just now</span>
      </div>
      <div class="chat-message-content">${escapeHtml(content)}</div>
    </div>
  `;
  container.appendChild(msg);
  container.scrollTop = container.scrollHeight;
}

function showTypingIndicator(agent) {
  const container = document.getElementById('chatMessages');
  const id = 'typing-' + Date.now();
  const div = document.createElement('div');
  div.className = 'chat-message assistant';
  div.id = id;
  div.innerHTML = `
    <div class="chat-message-avatar">◆</div>
    <div class="chat-message-body">
      <div class="chat-message-header">
        <span class="chat-message-agent">${agent}</span>
      </div>
      <div class="typing-indicator"><span></span><span></span><span></span></div>
    </div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

async function refreshChat() {
  try {
    const data = await api.getChatHistory();
    const messages = data.messages || [];
    window._chatHistory = messages;
    renderChatHistory(messages);
  } catch {}
}

function renderChatHistory(messages) {
  const container = document.getElementById('chatMessages');
  if (!container) return;
  const welcome = container.querySelector('.chat-welcome');
  if (welcome) welcome.style.display = 'none';

  // Remove all existing messages (keep welcome)
  container.querySelectorAll('.chat-message').forEach(el => el.remove());

  if (messages.length === 0) {
    if (welcome) welcome.style.display = '';
    return;
  }

  messages.forEach(msg => {
    const div = document.createElement('div');
    div.className = `chat-message ${msg.role}`;
    div.innerHTML = `
      <div class="chat-message-avatar">${msg.role === 'user' ? '▸' : '◆'}</div>
      <div class="chat-message-body">
        <div class="chat-message-header">
          <span class="chat-message-agent">${msg.role === 'user' ? 'You' : msg.agent}</span>
          <span class="chat-message-time">${timeAgo(msg.timestamp)}</span>
        </div>
        <div class="chat-message-content">${escapeHtml(msg.content)}</div>
      </div>
    `;
    container.appendChild(div);
  });
  container.scrollTop = container.scrollHeight;
}

function clearChat() {
  document.querySelectorAll('#chatMessages .chat-message').forEach(el => el.remove());
  const welcome = document.querySelector('.chat-welcome');
  if (welcome) welcome.style.display = '';
  window._chatHistory = [];
}

function sendQuickPrompt(agent, message) {
  selectAgent(agent);
  document.getElementById('chatInput').value = message;
  sendChatMessage();
}
