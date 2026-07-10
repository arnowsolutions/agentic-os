const OMNIROUTE_BASE = 'https://omniroute.srv1738752.hstgr.cloud';
const OMNIROUTE_KEY = 'omni-0901b5a1277093ee297bdcf3742c00ce92cf6461540e445d';

// --- Chat State ---
let omnirouteMessages = [];
let omnirouteConversationId = 'chat_' + Date.now();

// --- Render ---
async function renderOmniroute() {
  const content = document.getElementById('pageContent');

  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">💬 OmniRoute Chat</div>
        <div class="page-subtitle">237 providers · auto-fallback · image upload · free routing</div>
      </div>
      <div class="page-header-right">
        <button class="btn btn-ghost btn-sm" onclick="clearOmnirouteChat()" title="New conversation">
          🆕 New Chat
        </button>
        <button class="btn btn-ghost btn-sm" onclick="checkOmnirouteHealth()" title="Check connection">
          🔄 Status
        </button>
        <a href="${OMNIROUTE_BASE}" target="_blank" class="btn btn-secondary btn-sm" rel="noopener">
          🎛️ Dashboard ↗
        </a>
      </div>
    </div>

    <!-- Status bar -->
    <div id="omnirouteStatusBar" style="display:flex;align-items:center;gap:12px;padding:8px 14px;background:var(--bg-card);border:1px solid var(--border);border-radius:8px;margin-bottom:12px;font-size:13px">
      <span id="omnirouteStatusDot" class="status-dot status-dot-checking"></span>
      <span id="omnirouteStatusText">Checking OmniRoute...</span>
      <span style="flex:1"></span>
      <span style="color:var(--text-muted)">Model:</span>
      <select id="omnirouteModelSelect" class="form-select" style="width:auto;padding:4px 8px;font-size:12px" onchange="updateOmnirouteModelBadge()">
        <optgroup label="Auto Routing">
          <option value="auto/cheap">💰 auto/cheap</option>
          <option value="auto/best-free">🆓 auto/best-free</option>
          <option value="auto/coding:free">💻 auto/coding:free</option>
          <option value="auto/best-coding">🏆 auto/best-coding</option>
          <option value="auto/best-fast">⚡ auto/best-fast</option>
          <option value="auto/best-reasoning">🧠 auto/best-reasoning</option>
          <option value="auto/coding" selected>🔧 auto/coding</option>
          <option value="auto/chat">💬 auto/chat</option>
        </optgroup>
        <optgroup label="Direct Models">
          <option value="groq/llama-3.3-70b-versatile">Groq Llama 3.3 70B</option>
          <option value="groq/meta-llama/llama-4-scout-17b-16e-instruct">Groq Llama 4 Scout 17B</option>
          <option value="groq/qwen/qwen3.6-27b">Groq Qwen 3.6 27B</option>
          <option value="groq/llama-3.1-8b-instant">Groq Llama 3.1 8B</option>
          <option value="glm/glm-5.2">GLM 5.2</option>
          <option value="kmc/kimi-k2.6">Kimi K2.6</option>
        </optgroup>
      </select>
      <span id="omnirouteCostBadge" style="font-size:11px;color:var(--green)">$0.00</span>
    </div>

    <!-- Chat Area -->
    <div style="display:flex;flex-direction:column;height:calc(100vh - 220px);min-height:500px">
      <!-- Messages -->
      <div id="omnirouteMessages" style="flex:1;overflow-y:auto;padding:12px 0;display:flex;flex-direction:column;gap:12px;min-height:0">
        <div style="text-align:center;color:var(--text-muted);padding:40px 20px">
          <div style="font-size:48px;margin-bottom:12px">🚀</div>
          <div style="font-size:18px;font-weight:600;margin-bottom:6px">OmniRoute Chat</div>
          <div style="font-size:13px">Ask anything, paste images, or drag &amp; drop files.<br>Routes through 237 providers automatically.</div>
        </div>
      </div>

      <!-- Image Preview Area -->
      <div id="omnirouteImagePreview" style="display:none;padding:8px 12px;border-top:1px solid var(--border);background:var(--bg-card)"></div>

      <!-- Input Area -->
      <div style="border-top:1px solid var(--border);padding:12px 0 0 0;background:var(--bg-main)">
        <div style="display:flex;gap:8px;align-items:flex-end">
          <!-- Image Upload Button -->
          <label class="btn btn-ghost btn-sm" style="cursor:pointer;padding:10px 12px;flex-shrink:0" title="Upload image">
            🖼️
            <input type="file" accept="image/*" style="display:none" id="omnirouteFileInput" onchange="handleOmnirouteFile(event)" multiple>
          </label>
          <!-- Text Input -->
          <textarea id="omnirouteInput"
            class="form-textarea"
            rows="1"
            placeholder="Type a message... (Shift+Enter for new line)"
            style="flex:1;resize:none;max-height:150px;min-height:44px;font-size:14px"
            onkeydown="handleOmnirouteKeydown(event)"
            oninput="autoResizeOmnirouteInput()"
          ></textarea>
          <!-- Send Button -->
          <button class="btn btn-primary" id="omnirouteSendBtn" onclick="sendOmnirouteMessage()" style="padding:10px 20px;flex-shrink:0">
            ▶ Send
          </button>
        </div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:6px;display:flex;gap:16px">
          <span>🖼️ Click 🖼️ to upload images</span>
          <span>📋 Paste image from clipboard: Ctrl+V in text box</span>
          <span id="omniroutePendingImages" style="display:none;color:var(--yellow)"></span>
        </div>
      </div>
    </div>

    <style>
      .omniroute-msg {
        display: flex;
        gap: 10px;
        padding: 0 14px;
        animation: omnirouteFadeIn 0.2s ease;
      }
      .omniroute-msg.user {
        flex-direction: row-reverse;
      }
      .omniroute-msg-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        flex-shrink: 0;
      }
      .omniroute-msg.assistant .omniroute-msg-avatar {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      }
      .omniroute-msg.user .omniroute-msg-avatar {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
      }
      .omniroute-msg-bubble {
        max-width: 75%;
        padding: 10px 14px;
        border-radius: 16px;
        font-size: 14px;
        line-height: 1.55;
        word-wrap: break-word;
      }
      .omniroute-msg.user .omniroute-msg-bubble {
        background: var(--accent);
        color: #fff;
        border-bottom-right-radius: 4px;
      }
      .omniroute-msg.assistant .omniroute-msg-bubble {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-bottom-left-radius: 4px;
      }
      .omniroute-msg-bubble pre {
        background: rgba(0,0,0,0.3);
        border-radius: 8px;
        padding: 10px;
        overflow-x: auto;
        font-size: 13px;
        margin: 8px 0;
      }
      .omniroute-msg-bubble code {
        font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
        font-size: 13px;
        background: rgba(0,0,0,0.2);
        padding: 2px 5px;
        border-radius: 4px;
      }
      .omniroute-msg-bubble pre code {
        background: none;
        padding: 0;
      }
      .omniroute-msg-meta {
        font-size: 11px;
        color: var(--text-muted);
        margin-top: 4px;
        padding: 0 14px;
      }
      .omniroute-msg.user + .omniroute-msg-meta {
        text-align: right;
      }
      .omniroute-img-preview {
        position: relative;
        display: inline-block;
        margin: 4px;
      }
      .omniroute-img-preview img {
        max-width: 200px;
        max-height: 150px;
        border-radius: 8px;
        border: 1px solid var(--border);
        object-fit: cover;
      }
      .omniroute-img-preview .remove-btn {
        position: absolute;
        top: -6px;
        right: -6px;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background: var(--red);
        color: #fff;
        border: none;
        cursor: pointer;
        font-size: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .omniroute-msg-bubble img {
        max-width: 100%;
        max-height: 300px;
        border-radius: 8px;
        margin: 6px 0;
      }
      .omniroute-typing {
        display: flex;
        gap: 4px;
        padding: 10px 14px;
      }
      .omniroute-typing span {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--text-muted);
        animation: omnirouteBounce 1.4s infinite ease-in-out;
      }
      .omniroute-typing span:nth-child(2) { animation-delay: 0.2s; }
      .omniroute-typing span:nth-child(3) { animation-delay: 0.4s; }
      @keyframes omnirouteBounce {
        0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
        40% { transform: scale(1); opacity: 1; }
      }
      @keyframes omnirouteFadeIn {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
      }
      #omnirouteInput:focus {
        outline: none;
        border-color: var(--accent);
        box-shadow: 0 0 0 2px rgba(99,102,241,0.15);
      }
      .omniroute-cursor {
        animation: omnirouteBlink 1s step-end infinite;
        color: var(--accent);
      }
      @keyframes omnirouteBlink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0; }
      }
    </style>
  `;

  // Attach paste handler to input
  setTimeout(() => {
    const input = document.getElementById('omnirouteInput');
    if (input) {
      input.addEventListener('paste', handleOmniroutePaste);
    }
  }, 100);

  setTimeout(checkOmnirouteHealth, 300);
  loadOmnirouteChat();
}

// --- Chat Persistence ---
function saveOmnirouteChat() {
  try {
    localStorage.setItem('omniroute_messages', JSON.stringify(omnirouteMessages.slice(-100)));
  } catch(e) {}
}

function loadOmnirouteChat() {
  try {
    const saved = localStorage.getItem('omniroute_messages');
    if (saved) {
      omnirouteMessages = JSON.parse(saved);
      renderOmnirouteMessages();
    }
  } catch(e) {}
}

function clearOmnirouteChat() {
  omnirouteMessages = [];
  omnirouteConversationId = 'chat_' + Date.now();
  localStorage.removeItem('omniroute_messages');
  omniroutePendingImages = [];
  renderOmnirouteMessages();
  updateImagePreview();
  showToast('New conversation started', 'info');
}

// --- Image Handling ---
let omniroutePendingImages = [];

function handleOmnirouteFile(event) {
  const files = event.target.files;
  for (const file of files) {
    if (!file.type.startsWith('image/')) continue;
    const reader = new FileReader();
    reader.onload = function(e) {
      omniroutePendingImages.push({
        dataUrl: e.target.result,
        name: file.name,
        type: file.type
      });
      updateImagePreview();
    };
    reader.readAsDataURL(file);
  }
  event.target.value = '';
}

function updateImagePreview() {
  const preview = document.getElementById('omnirouteImagePreview');
  const badge = document.getElementById('omniroutePendingImages');
  if (!preview) return;

  if (omniroutePendingImages.length === 0) {
    preview.style.display = 'none';
    preview.innerHTML = '';
    if (badge) badge.style.display = 'none';
    return;
  }

  preview.style.display = 'block';
  preview.innerHTML = omniroutePendingImages.map((img, i) => `
    <div class="omniroute-img-preview">
      <img src="${img.dataUrl}" alt="${escapeHtml(img.name)}">
      <button class="remove-btn" onclick="removeOmnirouteImage(${i})" title="Remove">✕</button>
    </div>
  `).join('');
  if (badge) {
    badge.style.display = 'inline';
    badge.textContent = `${omniroutePendingImages.length} image(s) pending`;
  }
}

function removeOmnirouteImage(index) {
  omniroutePendingImages.splice(index, 1);
  updateImagePreview();
}

// --- Paste from Clipboard ---
async function handleOmniroutePaste(event) {
  const items = event.clipboardData?.items;
  if (!items) return;

  for (const item of items) {
    if (item.type.startsWith('image/')) {
      event.preventDefault();
      const blob = item.getAsFile();
      const reader = new FileReader();
      reader.onload = function(e) {
        omniroutePendingImages.push({
          dataUrl: e.target.result,
          name: 'clipboard-image.' + (item.type.split('/')[1] || 'png'),
          type: item.type
        });
        updateImagePreview();
      };
      reader.readAsDataURL(blob);
      return;
    }
  }
}

// --- Input ---
function handleOmnirouteKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendOmnirouteMessage();
  }
}

function autoResizeOmnirouteInput() {
  const input = document.getElementById('omnirouteInput');
  if (!input) return;
  input.style.height = 'auto';
  input.style.height = Math.min(input.scrollHeight, 150) + 'px';
}

// --- Send Message (SSE streaming) ---
async function sendOmnirouteMessage() {
  const input = document.getElementById('omnirouteInput');
  const text = input.value.trim();
  const hasImages = omniroutePendingImages.length > 0;

  if (!text && !hasImages) return;

  // Build user message
  const userMsg = {
    role: 'user',
    content: text || '(image attached)',
    images: omniroutePendingImages.length > 0 ? omniroutePendingImages.map(i => i.dataUrl) : [],
    timestamp: Date.now()
  };

  // Add to messages
  omnirouteMessages.push(userMsg);
  saveOmnirouteChat();

  // Clear input
  input.value = '';
  input.style.height = 'auto';
  const imagesSent = [...omniroutePendingImages];
  omniroutePendingImages = [];
  updateImagePreview();

  // Render
  renderOmnirouteMessages();
  scrollOmnirouteToBottom();

  // Create streaming placeholder
  const assistantMsg = {
    role: 'assistant',
    content: '',
    model: '',
    tokens: 0,
    timestamp: Date.now(),
    _streaming: true
  };
  omnirouteMessages.push(assistantMsg);
  const streamIndex = omnirouteMessages.length - 1;
  renderOmnirouteMessages();
  scrollOmnirouteToBottom();

  // Build API payload
  const model = document.getElementById('omnirouteModelSelect')?.value || 'auto/coding';
  const messages = buildOmniroutePayload(text || 'Analyze this image', imagesSent);

  // Disable send button
  const sendBtn = document.getElementById('omnirouteSendBtn');
  if (sendBtn) { sendBtn.disabled = true; sendBtn.textContent = '⏳'; }

  try {
    const resp = await fetch(OMNIROUTE_BASE + '/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + OMNIROUTE_KEY
      },
      body: JSON.stringify({
        model: model,
        messages: messages,
        max_tokens: 4096
      }),
      signal: AbortSignal.timeout(120000)
    });

    if (!resp.ok) {
      const errText = await resp.text().catch(() => 'Unknown');
      throw new Error('HTTP ' + resp.status + ': ' + errText.slice(0, 300));
    }

    // Parse SSE stream
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullContent = '';
    let resolvedModel = model;
    let totalTokens = 0;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // keep incomplete line in buffer

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const data = line.slice(6).trim();
        if (data === '[DONE]') continue;

        try {
          const chunk = JSON.parse(data);
          const delta = chunk.choices?.[0]?.delta;

          if (delta?.content) {
            fullContent += delta.content;
            omnirouteMessages[streamIndex].content = fullContent;
            omnirouteMessages[streamIndex].model = chunk.model || resolvedModel;
            updateStreamingMessage(streamIndex);
          }

          if (chunk.usage) {
            totalTokens = chunk.usage.total_tokens;
            resolvedModel = chunk.model || resolvedModel;
          }
        } catch (e) {
          // skip malformed JSON lines
        }
      }
    }

    // Finalize
    omnirouteMessages[streamIndex].content = fullContent || '(empty response)';
    omnirouteMessages[streamIndex].model = resolvedModel;
    omnirouteMessages[streamIndex].tokens = totalTokens;
    omnirouteMessages[streamIndex].timestamp = Date.now();
    delete omnirouteMessages[streamIndex]._streaming;
    saveOmnirouteChat();
    renderOmnirouteMessages();
    scrollOmnirouteToBottom();
    updateCostBadge({ total_tokens: totalTokens });

  } catch (err) {
    if (err.name === 'AbortError') {
      omnirouteMessages[streamIndex].content = omnirouteMessages[streamIndex].content || '⏰ Request timed out';
    } else {
      omnirouteMessages[streamIndex].content = '❌ **Error:** ' + err.message;
    }
    omnirouteMessages[streamIndex].isError = true;
    delete omnirouteMessages[streamIndex]._streaming;
    saveOmnirouteChat();
    renderOmnirouteMessages();
    scrollOmnirouteToBottom();
  } finally {
    if (sendBtn) { sendBtn.disabled = false; sendBtn.textContent = '▶ Send'; }
  }
}

// Efficiently update a single streaming message without full re-render
function updateStreamingMessage(index) {
  const container = document.getElementById('omnirouteMessages');
  if (!container) return;

  const msg = omnirouteMessages[index];
  const msgEl = container.querySelector(`[data-msg-index="${index}"]`);
  if (!msgEl) {
    // Fall back to full render if element not found
    renderOmnirouteMessages();
    scrollOmnirouteToBottom();
    return;
  }

  const bubble = msgEl.querySelector('.omniroute-msg-bubble');
  if (bubble) {
    bubble.innerHTML = formatOmnirouteContent(msg.content);
  }
  scrollOmnirouteToBottom();
}

function buildOmniroutePayload(text, images) {
  // Build conversation context (last 10 messages) + new message
  const context = omnirouteMessages.slice(-20).filter(m => m.role !== 'system' && !m.isError);

  // Convert to API format
  const apiMessages = [];

  for (const msg of context) {
    if (msg.images && msg.images.length > 0) {
      // Multimodal message
      const contentParts = [];
      if (msg.content && msg.content !== '(image attached)') {
        contentParts.push({ type: 'text', text: msg.content });
      } else {
        contentParts.push({ type: 'text', text: 'Analyze this image:' });
      }
      for (const imgDataUrl of msg.images) {
        contentParts.push({
          type: 'image_url',
          image_url: { url: imgDataUrl }
        });
      }
      apiMessages.push({ role: 'user', content: contentParts });
    } else {
      apiMessages.push({ role: msg.role, content: msg.content });
    }
  }

  return apiMessages;
}

// --- Rendering ---
function renderOmnirouteMessages() {
  const container = document.getElementById('omnirouteMessages');
  if (!container) return;

  if (omnirouteMessages.length === 0) {
    container.innerHTML = `
      <div style="text-align:center;color:var(--text-muted);padding:40px 20px">
        <div style="font-size:48px;margin-bottom:12px">🚀</div>
        <div style="font-size:18px;font-weight:600;margin-bottom:6px">OmniRoute Chat</div>
        <div style="font-size:13px">Ask anything, paste images, or drag &amp; drop files.<br>Routes through 237 providers automatically.</div>
      </div>`;
    return;
  }

  container.innerHTML = omnirouteMessages.map((msg, i) => {
    const isUser = msg.role === 'user';
    const avatar = isUser ? '👤' : '🤖';
    const time = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';

    let bubbleContent = '';

    // Images
    if (msg.images && msg.images.length > 0) {
      bubbleContent += msg.images.map(img =>
        `<img src="${img}" alt="attached image" loading="lazy">`
      ).join('');
    }

    // Streaming indicator
    if (msg._streaming && !msg.content) {
      bubbleContent += '<span class="omniroute-cursor">▊</span>';
    } else if (msg.content && msg.content !== '(image attached)') {
      bubbleContent += formatOmnirouteContent(msg.content);
      if (msg._streaming) {
        bubbleContent += '<span class="omniroute-cursor">▊</span>';
      }
    }

    // Error styling
    const bubbleStyle = msg.isError ? 'style="background:#3b0a0a;border-color:var(--red);color:#fca5a5"' : '';

    let html = `<div class="omniroute-msg ${msg.role}" data-msg-index="${i}">`;
    html += `<div class="omniroute-msg-avatar">${avatar}</div>`;
    html += `<div class="omniroute-msg-bubble" ${bubbleStyle}>${bubbleContent}</div>`;
    html += `</div>`;

    // Meta info (model, tokens, time)
    if (!isUser && !msg.isError && !msg._streaming) {
      html += `<div class="omniroute-msg-meta" style="padding:0 56px">`;
      if (msg.model) html += `<span style="color:var(--accent);font-weight:500">${escapeHtml(msg.model)}</span>`;
      if (msg.tokens) html += ` · <span style="color:var(--text-muted)">${msg.tokens} tokens</span>`;
      if (time) html += ` · <span style="color:var(--text-muted)">${time}</span>`;
      html += `</div>`;
    } else if (msg._streaming) {
      html += `<div class="omniroute-msg-meta" style="padding:0 56px"><span style="color:var(--yellow);font-size:12px">streaming...</span></div>`;
    } else if (isUser && time) {
      html += `<div class="omniroute-msg-meta" style="text-align:right"><span style="color:var(--text-muted)">${time}</span></div>`;
    } else if (msg.isError && time) {
      html += `<div class="omniroute-msg-meta" style="padding:0 56px"><span style="color:var(--text-muted)">${time}</span></div>`;
    }

    return html;
  }).join('');
}

function formatOmnirouteContent(text) {
  if (!text) return '';
  // Basic markdown: code blocks, inline code, bold, links
  let html = escapeHtml(text);

  // Code blocks (``` ... ```)
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    return `<pre><code class="language-${lang}">${code.trim()}</code></pre>`;
  });

  // Inline code (`...`)
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Bold (**text**)
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // Italic (*text*)
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  // URLs
  html = html.replace(/(https?:\/\/\S+)/g, '<a href="$1" target="_blank" rel="noopener" style="color:var(--accent)">$1</a>');

  return html;
}

function showOmnirouteTyping() {
  const container = document.getElementById('omnirouteMessages');
  if (!container) return;
  const typingDiv = document.createElement('div');
  typingDiv.id = 'omnirouteTyping';
  typingDiv.className = 'omniroute-msg assistant';
  typingDiv.innerHTML = `
    <div class="omniroute-msg-avatar" style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%)">🤖</div>
    <div class="omniroute-msg-bubble" style="background:var(--bg-card);border:1px solid var(--border)">
      <div class="omniroute-typing">
        <span></span><span></span><span></span>
      </div>
    </div>`;
  container.appendChild(typingDiv);
  scrollOmnirouteToBottom();
}

function removeOmnirouteTyping() {
  const el = document.getElementById('omnirouteTyping');
  if (el) el.remove();
}

function scrollOmnirouteToBottom() {
  setTimeout(() => {
    const container = document.getElementById('omnirouteMessages');
    if (container) container.scrollTop = container.scrollHeight;
  }, 50);
}

function updateCostBadge(usage) {
  const badge = document.getElementById('omnirouteCostBadge');
  if (!badge) return;
  if (usage?.total_tokens) {
    badge.textContent = `${usage.total_tokens} tok`;
    badge.style.color = 'var(--text-muted)';
  }
}

function updateOmnirouteModelBadge() {
  // Placeholder for future use
}

// --- Health Check ---
async function checkOmnirouteHealth() {
  const dot = document.getElementById('omnirouteStatusDot');
  const text = document.getElementById('omnirouteStatusText');

  if (dot) dot.className = 'status-dot status-dot-checking';
  if (text) text.textContent = 'Checking...';

  try {
    const resp = await fetch(OMNIROUTE_BASE + '/v1/models', {
      method: 'GET',
      headers: { 'Authorization': 'Bearer ' + OMNIROUTE_KEY },
      signal: AbortSignal.timeout(5000)
    });
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const data = await resp.json();
    const models = data.data || [];

    if (dot) dot.className = 'status-dot status-dot-online';
    if (text) text.innerHTML = '🟢 <strong>Online</strong> — ' + models.length + ' models available';

    // Also update the old cards if they exist
    const count = document.getElementById('omnirouteModelCount');
    if (count) count.textContent = models.length;

  } catch (err) {
    if (dot) dot.className = 'status-dot status-dot-offline';
    if (text) text.textContent = '🔴 Offline — ' + err.message;
    const count = document.getElementById('omnirouteModelCount');
    if (count) count.textContent = '\u2014';
  }
}
