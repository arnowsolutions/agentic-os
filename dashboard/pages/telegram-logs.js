async function renderTelegramLogs() {
  const content = document.getElementById('pageContent');
  
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">✈️ Telegram Logs</div>
        <div class="page-subtitle">Recent messages, gateway activity, and delivery history</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderTelegramLogs()">🔄 Refresh</button>
        <button class="btn btn-primary" onclick="fetchTelegramLogs()">📥 Load Logs</button>
      </div>
    </div>
    <div class="tl-grid">
      <div class="tl-section" id="tlRecentSection">
        <div class="tl-section-header"><span>📨 Recent Telegram Activity</span></div>
        <div id="tlRecent" class="tl-loading"><div class="loading-spinner"></div></div>
      </div>
      <div class="tl-section" id="tlGatewaySection">
        <div class="tl-section-header"><span>🔌 Gateway Connection</span></div>
        <div id="tlGateway" class="tl-loading"><div class="loading-spinner"></div></div>
      </div>
    </div>
    <div class="tl-section" style="margin-top:12px" id="tlLogSection">
      <div class="tl-section-header">
        <span>📋 Gateway Log (last 50 lines)</span>
        <button class="btn btn-ghost btn-xs" onclick="fetchTelegramLogs()">🔄 Refresh</button>
      </div>
      <div id="tlLogContent" class="tl-loading"><div class="loading-spinner"></div></div>
    </div>
    <style>
      .tl-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:16px; }
      @media (max-width:800px) { .tl-grid { grid-template-columns:1fr; } }
      .tl-section { background:var(--bg-card); border-radius:var(--radius-md); border:1px solid var(--border); overflow:hidden; }
      .tl-section-header { padding:10px 14px; border-bottom:1px solid var(--border); font-size:13px; font-weight:600; display:flex; justify-content:space-between; align-items:center; }
      .tl-loading { padding:20px; text-align:center; color:var(--text-muted); font-size:13px; display:flex; flex-direction:column; align-items:center; gap:8px; }
      .tl-log-line { padding:3px 14px; font-family:monospace; font-size:10.5px; line-height:1.5; border-bottom:1px solid rgba(255,255,255,0.03); white-space:pre-wrap; word-break:break-all; }
      .tl-log-line:hover { background:rgba(255,255,255,0.03); }
      .tl-log-line .time { color:#636e72; margin-right:8px; }
      .tl-log-line .info { color:#74b9ff; }
      .tl-log-line .warn { color:#fdcb6e; }
      .tl-log-line .error { color:#d63031; }
      .tl-message { padding:8px 14px; border-bottom:1px solid rgba(255,255,255,0.04); font-size:12px; display:flex; gap:8px; align-items:start; }
      .tl-message:hover { background:rgba(255,255,255,0.02); }
      .tl-message .avatar { width:28px; height:28px; border-radius:50%; background:var(--gradient); display:grid; place-items:center; font-size:11px; font-weight:700; color:#fff; flex-shrink:0; }
      .tl-message .body { flex:1; min-width:0; }
      .tl-message .sender { font-weight:600; font-size:12px; }
      .tl-message .text { color:var(--text-muted); font-size:11px; margin-top:1px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
      .tl-message .time { font-size:10px; color:#636e72; flex-shrink:0; }
      .tl-status { display:flex; align-items:center; gap:8px; padding:14px; font-size:13px; }
      .tl-status .dot { width:10px; height:10px; border-radius:50%; }
      .tl-status .dot.green { background:#00b894; }
      .tl-status .dot.red { background:#d63031; }
      .tl-status .dot.yellow { background:#fdcb6e; }
      .btn-xs { padding:4px 8px; font-size:11px; }
    </style>
  `;

  // Auto-load logs on render
  fetchTelegramLogs();
}

async function fetchTelegramLogs() {
  const recentEl = document.getElementById('tlRecent');
  const gatewayEl = document.getElementById('tlGateway');
  const logEl = document.getElementById('tlLogContent');

  try {
    const [gatewayRes, logRes] = await Promise.all([
      fetch('/api/telegram/status').then(r => r.json()).catch(() => ({})),
      fetch('/api/telegram/logs').then(r => r.json()).catch(() => ({lines: []})),
    ]);

    // Gateway status
    const connected = gatewayRes.connected;
    gatewayEl.innerHTML = `
      <div class="tl-status">
        <span class="dot ${connected ? 'green' : 'red'}"></span>
        <span style="font-weight:600">${connected ? '✅ Connected' : '❌ Disconnected'}</span>
        <span style="color:var(--text-muted);font-size:11px">${gatewayRes.detail || ''}</span>
      </div>
      ${gatewayRes.platforms ? `
        <div style="padding:0 14px 12px;font-size:11px;color:var(--text-muted)">
          ${Object.entries(gatewayRes.platforms).map(([name, info]) => `
            <div style="display:flex;justify-content:space-between;padding:4px 0">
              <span>${name}</span>
              <span class="dot" style="width:8px;height:8px;display:inline-block;border-radius:50%;margin-right:4px;background:${info.connected ? '#00b894' : '#d63031'}"></span>
            </div>
          `).join('')}
        </div>` : ''}
    `;

    // Recent messages
    const messages = gatewayRes.recent_messages || [];
    if (messages.length > 0) {
      recentEl.innerHTML = messages.map(m => `
        <div class="tl-message">
          <div class="avatar">${(m.sender || '?')[0].toUpperCase()}</div>
          <div class="body">
            <div class="sender">${escapeHtml(m.sender || 'Unknown')}</div>
            <div class="text">${escapeHtml(m.text || m.message || '(no content)')}</div>
          </div>
          <span class="time">${m.time || m.date || ''}</span>
        </div>
      `).join('');
    } else {
      recentEl.innerHTML = '<div class="tl-loading">📭 No recent messages — gateway may be idle</div>';
    }

    // Logs
    const lines = logRes.lines || [];
    if (lines.length > 0) {
      logEl.innerHTML = lines.map(line => {
        const cls = line.toLowerCase().includes('error') ? 'error' 
          : line.toLowerCase().includes('warn') ? 'warn' 
          : 'info';
        const time = line.substring(0, 19);
        const rest = line.substring(19);
        return `<div class="tl-log-line"><span class="time">${escapeHtml(time)}</span><span class="${cls}">${escapeHtml(rest)}</span></div>`;
      }).join('');
    } else {
      logEl.innerHTML = '<div class="tl-loading">📭 No log data available</div>';
    }
  } catch (err) {
    recentEl.innerHTML = `<div class="tl-loading">⚠️ Error: ${escapeHtml(err.message)}</div>`;
    gatewayEl.innerHTML = `<div class="tl-loading">⚠️ Error loading status</div>`;
    logEl.innerHTML = `<div class="tl-loading">⚠️ Error loading logs</div>`;
  }
}
