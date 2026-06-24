let _aiBuilderHistory = [];

async function renderAiBuilder() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">🤖 AI Builder</h1>
        <p class="page-subtitle">Google Antigravity — Build add-ons & websites with Gemini</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="clearAiBuilder()">🗑 Clear</button>
        <button class="btn" onclick="exportAICode()">📦 Export</button>
      </div>
    </div>
    <div class="builder-layout">
      <div class="builder-sidebar">
        <div class="builder-config-section">
          <div class="builder-config-label">Model</div>
          <select id="builderModel" class="builder-select" onchange="saveBuilderConfig()">
            <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
            <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
            <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
            <option value="gemini-2.0-flash-lite">Gemini 2.0 Flash Lite</option>
          </select>
        </div>
        <div class="builder-config-section">
          <div class="builder-config-label">Mode</div>
          <select id="builderMode" class="builder-select" onchange="onBuilderModeChange()">
            <option value="chat">💬 Chat</option>
            <option value="code">💻 Build Code</option>
            <option value="website">🌐 Build Website</option>
            <option value="addon">🔌 Build Add-on</option>
          </select>
        </div>
        <div class="builder-config-section">
          <div class="builder-config-label">System Prompt</div>
          <textarea id="builderSystemPrompt" class="builder-textarea" rows="4" placeholder="Custom instructions for Gemini..." onchange="saveBuilderConfig()">You are an expert web developer. Generate clean, working code with HTML, CSS, and JavaScript. Always provide full, runnable code.</textarea>
        </div>
        <div class="builder-config-section" style="margin-top:auto">
          <div class="builder-quick-actions-label">Quick Actions</div>
          <button class="btn btn-sm" onclick="builderQuickAction('Create a responsive dashboard with charts and data tables')" style="display:block;width:100%;margin-bottom:6px;text-align:left">📊 Dashboard</button>
          <button class="btn btn-sm" onclick="builderQuickAction('Build a contact form with email validation and submission')" style="display:block;width:100%;margin-bottom:6px;text-align:left">📝 Contact Form</button>
          <button class="btn btn-sm" onclick="builderQuickAction('Create a CRUD app with local storage for task management')" style="display:block;width:100%;margin-bottom:6px;text-align:left">✅ Task Manager</button>
          <button class="btn btn-sm" onclick="builderQuickAction('Build a real-time chat widget for a website using WebSocket')" style="display:block;width:100%;margin-bottom:6px;text-align:left">💬 Chat Widget</button>
          <button class="btn btn-sm" onclick="builderQuickAction('Create an API endpoint that integrates with Google Calendar')" style="display:block;width:100%;text-align:left">📅 Google Calendar</button>
        </div>
      </div>
      <div class="builder-main">
        <div class="builder-chat" id="builderMessages">
          <div class="builder-welcome">
            <div class="builder-welcome-icon">🤖</div>
            <div class="builder-welcome-title">AI Builder</div>
            <div class="builder-welcome-desc">
              Powered by <strong>Google Gemini</strong> — describe what you want to build<br>
              and I'll generate the code right here.
            </div>
            <div style="display:flex;gap:8px;margin-top:16px;flex-wrap:wrap;justify-content:center">
              <button class="btn btn-primary btn-sm" onclick="builderQuickAction('Build a modern landing page for a tech startup')">🚀 Landing Page</button>
              <button class="btn btn-sm" onclick="builderQuickAction('Create a Hermes Agent skill template for scheduling tasks')">⚡ Hermes Skill</button>
              <button class="btn btn-sm" onclick="builderQuickAction('Build a REST API in Python with FastAPI')">🔧 API Scaffold</button>
            </div>
          </div>
        </div>
        <div class="builder-input-area">
          <div class="builder-mode-badge" id="builderModeBadge">💬 Chat</div>
          <textarea id="builderInput" class="builder-input" rows="1" placeholder="Describe what you want to build..." onkeydown="handleBuilderKey(event)"></textarea>
          <button class="btn btn-primary btn-icon" onclick="sendBuilderMessage()" id="builderSendBtn" title="Send">➤</button>
        </div>
      </div>
      <div class="builder-preview" id="builderPreview" style="display:none">
        <div class="builder-preview-header">
          <span class="builder-preview-title">📄 Generated Output</span>
          <div class="btn-group">
            <button class="btn btn-sm" onclick="copyBuilderCode()">📋 Copy</button>
            <button class="btn btn-sm" onclick="runBuilderCode()">▶ Run</button>
            <button class="btn btn-sm" onclick="toggleBuilderPreview()">✕ Close</button>
          </div>
        </div>
        <pre id="builderCodeDisplay" class="builder-code-display"><code>// Generated code will appear here</code></pre>
        <div class="builder-preview-frame" id="builderPreviewFrame" style="display:none">
          <iframe id="builderPreviewIframe" class="builder-preview-iframe" sandbox="allow-scripts allow-same-origin"></iframe>
        </div>
      </div>
    </div>
  `;

  window._aiBuilderHistory = [];

  // Load saved config
  try {
    const savedModel = localStorage.getItem('builder-model');
    if (savedModel) document.getElementById('builderModel').value = savedModel;
    const savedMode = localStorage.getItem('builder-mode');
    if (savedMode) {
      document.getElementById('builderMode').value = savedMode;
      document.getElementById('builderModeBadge').textContent = document.querySelector(`#builderMode option[value="${savedMode}"]`)?.textContent || '💬 Chat';
    }
    const savedPrompt = localStorage.getItem('builder-prompt');
    if (savedPrompt) document.getElementById('builderSystemPrompt').value = savedPrompt;
  } catch {}

  document.getElementById('builderInput').focus();
}

function onBuilderModeChange() {
  const mode = document.getElementById('builderMode').value;
  const badge = document.getElementById('builderModeBadge');
  const labels = { chat: '💬 Chat', code: '💻 Build Code', website: '🌐 Build Website', addon: '🔌 Build Add-on' };
  badge.textContent = labels[mode] || '💬 Chat';
  saveBuilderConfig();
}

function saveBuilderConfig() {
  try {
    localStorage.setItem('builder-model', document.getElementById('builderModel').value);
    localStorage.setItem('builder-mode', document.getElementById('builderMode').value);
    localStorage.setItem('builder-prompt', document.getElementById('builderSystemPrompt').value);
  } catch {}
}

function handleBuilderKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendBuilderMessage();
  }
  autoResizeTextarea(e.target);
}

async function sendBuilderMessage() {
  const input = document.getElementById('builderInput');
  const message = input.value.trim();
  if (!message) return;

  const mode = document.getElementById('builderMode').value;
  const model = document.getElementById('builderModel').value;
  const system = document.getElementById('builderSystemPrompt').value;

  input.value = '';
  input.style.height = 'auto';

  // Build the actual prompt based on mode
  let fullPrompt = message;
  if (mode === 'code') {
    fullPrompt = `Generate clean production-ready code for: ${message}\n\nInclude full implementation with HTML, CSS, and JavaScript if applicable. Add comments explaining key parts.`;
  } else if (mode === 'website') {
    fullPrompt = `Build a complete, polished website for: ${message}\n\nGenerate a single HTML file with embedded CSS and JS. Include responsive design, modern styling, and all necessary functionality. Make it production-ready.`;
  } else if (mode === 'addon') {
    fullPrompt = `Design and implement a complete add-on/plugin for: ${message}\n\nInclude manifest/configuration, main logic, UI components, and integration instructions.`;
  }

  // Add user message
  addBuilderMessage('user', message, mode);

  // Show typing indicator
  const typingId = showBuilderTyping();

  try {
    const r = await api.post('/api/gemini/chat', {
      message: fullPrompt,
      model: model,
      system: system + (mode !== 'chat' ? '\nAlways output complete, working code. Never use placeholders like "..." or "// your code here".' : ''),
    });

    removeBuilderTyping(typingId);
    const response = r.response || '⚠ No response from Gemini';
    addBuilderMessage('assistant', response, mode);

    // If there's code in the response, show it in the preview
    const codeMatch = response.match(/```(\w*)\n([\s\S]*?)```/);
    if (codeMatch) {
      const codeLang = codeMatch[1] || 'text';
      const codeContent = codeMatch[2];
      showBuilderCode(codeContent, codeLang);
    }

    window._aiBuilderHistory.push({ role: 'user', content: message, mode });
    window._aiBuilderHistory.push({ role: 'assistant', content: response, mode });
  } catch (err) {
    removeBuilderTyping(typingId);
    addBuilderMessage('assistant', `⚠ Error: ${err.message}`, mode);
  }
}

function addBuilderMessage(role, content, mode) {
  const container = document.getElementById('builderMessages');
  const welcome = container.querySelector('.builder-welcome');
  if (welcome) welcome.style.display = 'none';

  const msg = document.createElement('div');
  msg.className = `builder-message ${role}`;

  // Render code blocks nicely
  let htmlContent = escapeHtml(content)
    .replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
      return `<div class="builder-code-block"><div class="builder-code-block-header">${lang || 'code'}</div><pre><code>${escapeHtml(code.trim())}</code></pre></div>`;
    })
    .replace(/\n/g, '<br>');

  const icon = role === 'user' ? '👤' : '🤖';
  const label = role === 'user' ? 'You' : `Gemini ${mode !== 'chat' ? '(' + mode + ')' : ''}`;

  msg.innerHTML = `
    <div class="builder-message-avatar">${icon}</div>
    <div class="builder-message-body">
      <div class="builder-message-header">
        <span class="builder-message-agent">${label}</span>
        <span class="builder-message-time">just now</span>
      </div>
      <div class="builder-message-content">${htmlContent}</div>
    </div>
  `;
  container.appendChild(msg);
  container.scrollTop = container.scrollHeight;
}

function showBuilderTyping() {
  const container = document.getElementById('builderMessages');
  const id = 'btyping-' + Date.now();
  const div = document.createElement('div');
  div.className = 'builder-message assistant';
  div.id = id;
  div.innerHTML = `
    <div class="builder-message-avatar">🤖</div>
    <div class="builder-message-body">
      <div class="builder-message-header">
        <span class="builder-message-agent">Gemini</span>
      </div>
      <div class="typing-indicator"><span></span><span></span><span></span></div>
    </div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeBuilderTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function showBuilderCode(code, language) {
  const preview = document.getElementById('builderPreview');
  const display = document.getElementById('builderCodeDisplay');
  const frame = document.getElementById('builderPreviewFrame');

  preview.style.display = 'flex';
  display.innerHTML = `<code class="language-${language}">${escapeHtml(code)}</code>`;
  display.style.display = 'block';
  frame.style.display = 'none';

  // If it's HTML, offer to render it
  if (language === 'html' || code.trim().startsWith('<!') || code.trim().startsWith('<html')) {
    frame.style.display = 'block';
    const iframe = document.getElementById('builderPreviewIframe');
    iframe.srcdoc = code;
  }
}

function toggleBuilderPreview() {
  const preview = document.getElementById('builderPreview');
  preview.style.display = preview.style.display === 'none' ? 'flex' : 'none';
}

function copyBuilderCode() {
  const code = document.getElementById('builderCodeDisplay').textContent;
  navigator.clipboard.writeText(code).then(() => showToast('Code copied!', 'success')).catch(() => {});
}

function runBuilderCode() {
  const code = document.getElementById('builderCodeDisplay').textContent;
  try {
    // Try to eval JS code - mainly for scripts
    new Function(code)();
    showToast('Code executed successfully!', 'success');
  } catch (e) {
    showToast(`Execution error: ${e.message}`, 'error');
  }
}

function clearAiBuilder() {
  document.querySelectorAll('#builderMessages .builder-message').forEach(el => el.remove());
  const welcome = document.querySelector('.builder-welcome');
  if (welcome) welcome.style.display = '';
  window._aiBuilderHistory = [];
  document.getElementById('builderPreview').style.display = 'none';
}

async function exportAICode() {
  // Collect all code blocks from the conversation
  const blocks = document.querySelectorAll('.builder-code-block pre code');
  if (blocks.length === 0) {
    showToast('No code blocks to export', 'warning');
    return;
  }

  let exportContent = '# AI Builder Export\n\n';
  blocks.forEach((block, i) => {
    exportContent += `## Block ${i + 1}\n\`\`\`\n${block.textContent}\n\`\`\`\n\n`;
  });

  try {
    await navigator.clipboard.writeText(exportContent);
    showToast(`Exported ${blocks.length} code blocks to clipboard!`, 'success');
  } catch {
    showToast('Could not copy to clipboard', 'error');
  }
}

function builderQuickAction(prompt) {
  const input = document.getElementById('builderInput');
  input.value = prompt;
  autoResizeTextarea(input);
  input.focus();
}
