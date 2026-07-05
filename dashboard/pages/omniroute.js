const OMNIROUTE_BASE = 'https://omniroute.srv1738752.hstgr.cloud';

async function renderOmniroute() {
  const content = document.getElementById('pageContent');

  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">OmniRoute — AI Gateway</div>
        <div class="page-subtitle">237 providers · auto-fallback · token compression · zero-cost LLM routing</div>
      </div>
      <div class="page-header-right">
        <button class="btn btn-secondary" onclick="checkOmnirouteHealth()" style="margin-right:8px">
          🔄 Check Status
        </button>
        <a href="${OMNIROUTE_BASE}" target="_blank" class="btn btn-primary" rel="noopener">
          🚀 Open Dashboard ↗
        </a>
      </div>
    </div>

    <!-- Status cards -->
    <div class="grid grid-3" style="margin-bottom:20px">
      <div class="card" id="omnirouteStatusCard">
        <div class="card-header">
          <div class="card-title">Server Status</div>
        </div>
        <div class="omniroute-status-body">
          <span id="omnirouteStatusDot" class="status-dot status-dot-checking"></span>
          <span id="omnirouteStatusText">Checking...</span>
        </div>
        <div class="text-muted text-sm" id="omnirouteUptime" style="margin-top:8px">—</div>
      </div>
      <div class="card">
        <div class="card-header">
          <div class="card-title">Models Available</div>
        </div>
        <div class="omniroute-stat-number" id="omnirouteModelCount">—</div>
        <div class="text-muted text-sm">routing combos + providers</div>
      </div>
      <div class="card">
        <div class="card-header">
          <div class="card-title">Free Tokens /mo</div>
        </div>
        <div class="omniroute-stat-number" style="color:var(--green)">1.6B</div>
        <div class="text-muted text-sm">across 90+ free-tier providers</div>
      </div>
    </div>

    <!-- Main grid: chat + config -->
    <div class="grid grid-2" style="margin-bottom:20px">
      <!-- Quick Chat -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">💬 Quick Test</div>
        </div>
        <div class="form-group">
          <label class="form-label">Model Combo</label>
          <select class="form-select" id="omnirouteModelSelect">
            <option value="auto/cheap">💰 auto/cheap</option>
            <option value="auto/best-free">🆓 auto/best-free</option>
            <option value="auto/coding:free">💻 auto/coding:free</option>
            <option value="auto/best-coding">🏆 auto/best-coding</option>
            <option value="auto/best-fast">⚡ auto/best-fast</option>
            <option value="auto/best-reasoning">🧠 auto/best-reasoning</option>
            <option value="auto/coding">🔧 auto/coding</option>
            <option value="auto/chat">💬 auto/chat</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Your message</label>
          <textarea class="form-textarea" id="omniroutePrompt" rows="2" placeholder="Ask anything..."></textarea>
        </div>
        <button class="btn btn-primary" onclick="testOmniroute()">
          🚀 Send
        </button>
        <div id="omnirouteResponse" class="omniroute-response-box" style="display:none;margin-top:12px"></div>
      </div>

      <!-- Quick links -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">🔗 Quick Links</div>
        </div>
        <div style="display:flex;flex-direction:column;gap:8px">
          <a href="${OMNIROUTE_BASE}" target="_blank" class="btn btn-secondary" style="text-align:left" rel="noopener">
            🎛️ Open Dashboard
          </a>
          <a href="${OMNIROUTE_BASE}/v1/models" target="_blank" class="btn btn-secondary" style="text-align:left" rel="noopener">
            📋 View Model List (JSON)
          </a>
          <a href="${OMNIROUTE_BASE}/v1/health" target="_blank" class="btn btn-secondary" style="text-align:left" rel="noopener">
            ❤️ Health Check
          </a>
          <a href="https://github.com/diegosouzapw/OmniRoute" target="_blank" class="btn btn-secondary" style="text-align:left" rel="noopener">
            📖 GitHub Repo
          </a>
          <div class="text-muted text-sm" style="margin-top:8px;padding:8px;background:var(--bg-card);border-radius:8px">
            <strong>📡 URL:</strong> ${OMNIROUTE_BASE}<br>
            <strong>🔐 Claude Code:</strong> <code>ANTHROPIC_BASE_URL=${OMNIROUTE_BASE}</code><br>
            <strong>🆓 Save:</strong> $0 inference via free-tier routing
          </div>
        </div>
      </div>
    </div>

    <!-- Full Dashboard Iframe -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">OmniRoute Dashboard</div>
        <div class="card-subtitle text-muted">Full management interface — providers, combos, usage, settings</div>
      </div>
      <div style="position:relative;width:100%;min-height:600px;border-radius:8px;overflow:hidden">
        <div id="omnirouteIframeFallback" style="display:none;padding:40px;text-align:center;background:var(--bg-card);border-radius:8px">
          <div style="font-size:48px;margin-bottom:16px">🔌</div>
          <h3>Dashboard Unavailable</h3>
          <p class="text-muted">The OmniRoute server may be restarting. Try again in a moment.</p>
          <button class="btn btn-primary mt-3" onclick="checkOmnirouteHealth()">Check Again</button>
        </div>
        <iframe id="omnirouteIframe"
          src="${OMNIROUTE_BASE}"
          style="width:100%;height:600px;border:none;border-radius:8px;background:#0b0f1a"
          loading="lazy"
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
          onload="handleOmnirouteIframeLoad()"
          onerror="handleOmnirouteIframeError()">
        </iframe>
      </div>
    </div>

    <style>
      .omniroute-status-body {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 0;
      }
      .status-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
      }
      .status-dot-checking { background: var(--yellow); animation: pulse 1.5s infinite; }
      .status-dot-online { background: var(--green); }
      .status-dot-offline { background: var(--red); }
      .omniroute-stat-number {
        font-size: 28px;
        font-weight: 700;
        color: var(--text);
      }
      .omniroute-response-box {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 12px;
        font-size: 14px;
        white-space: pre-wrap;
        max-height: 200px;
        overflow-y: auto;
      }
      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
      }
    </style>
  `;

  setTimeout(checkOmnirouteHealth, 500);
}

async function checkOmnirouteHealth() {
  const dot = document.getElementById('omnirouteStatusDot');
  const text = document.getElementById('omnirouteStatusText');
  const uptime = document.getElementById('omnirouteUptime');
  const count = document.getElementById('omnirouteModelCount');

  if (dot) dot.className = 'status-dot status-dot-checking';
  if (text) text.textContent = 'Checking...';

  try {
    const resp = await fetch(OMNIROUTE_BASE + '/v1/models', {
      method: 'GET',
      mode: 'cors',
      signal: AbortSignal.timeout(5000)
    });
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const data = await resp.json();
    const models = data.data || [];

    if (dot) dot.className = 'status-dot status-dot-online';
    if (text) text.textContent = '🟢 Online — ' + models.length + ' models';
    if (uptime) uptime.textContent = 'Live at ' + OMNIROUTE_BASE;
    if (count) count.textContent = models.length;
  } catch (err) {
    if (dot) dot.className = 'status-dot status-dot-offline';
    if (text) text.textContent = '🔴 Not responding';
    if (uptime) uptime.textContent = 'Error: ' + err.message;
    if (count) count.textContent = '\u2014';
  }
}

async function testOmniroute() {
  const model = document.getElementById('omnirouteModelSelect').value;
  const prompt = document.getElementById('omniroutePrompt').value;
  const responseEl = document.getElementById('omnirouteResponse');

  if (!prompt) { showToast('Enter a prompt first', 'warning'); return; }

  responseEl.style.display = 'block';
  responseEl.textContent = '⏳ Routing through ' + model + '...';
  responseEl.style.color = 'var(--text-muted)';

  try {
    const resp = await fetch(OMNIROUTE_BASE + '/v1/chat/completions', {
      method: 'POST',
      mode: 'cors',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: model,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 500,
        stream: false
      }),
      signal: AbortSignal.timeout(30000)
    });
    if (!resp.ok) {
      const errText = await resp.text().catch(() => 'Unknown error');
      throw new Error('HTTP ' + resp.status + ': ' + errText.slice(0, 200));
    }
    const data = await resp.json();
    const choice = data.choices ? data.choices[0] : null;
    const content = (choice && choice.message) ? choice.message.content : '(empty response)';
    const usedModel = data.model || model;

    responseEl.style.color = 'var(--text)';
    responseEl.innerHTML =
      '<div class="text-muted text-sm" style="margin-bottom:8px">' +
      '✅ via <strong>' + escapeHtml(usedModel) + '</strong>' +
      (data.usage ? ' \u00b7 ' + data.usage.total_tokens + ' tokens' : '') +
      '</div><div>' + escapeHtml(content) + '</div>';
  } catch (err) {
    responseEl.style.color = 'var(--red)';
    responseEl.textContent = '\u274c Error: ' + err.message;
  }
}

function handleOmnirouteIframeLoad() {
  const fallback = document.getElementById('omnirouteIframeFallback');
  if (fallback) fallback.style.display = 'none';
}
function handleOmnirouteIframeError() {
  const iframe = document.getElementById('omnirouteIframe');
  const fallback = document.getElementById('omnirouteIframeFallback');
  if (iframe) iframe.style.display = 'none';
  if (fallback) fallback.style.display = 'block';
}
