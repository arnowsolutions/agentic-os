async function renderTelegram() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">💬 Telegram Sessions</h1>
        <p class="page-subtitle">Messaging conversations from Hermes state.db</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="renderTelegram()">🔄 Refresh</button>
      </div>
    </div>

    <div id="telegramStats" class="grid grid-4 mb-4"></div>
    <div id="telegramList" class="mt-3"></div>
  `;

  try {
    const data = await api.getTelegramSessions();
    const sessions = data.sessions || [];
    const total = data.total || 0;
    const active = sessions.filter(s => !s.ended).length;
    const totalMsgs = sessions.reduce((sum, s) => sum + (s.messages || 0), 0);
    const sources = [...new Set(sessions.map(s => s.source))];

    document.getElementById('telegramStats').innerHTML = `
      <div class="card stat-card">
        <div class="stat-icon blue">💬</div>
        <div class="stat-value">${total}</div>
        <div class="stat-label">Total Sessions</div>
        <div class="stat-change up">${active} active</div>
      </div>
      <div class="card stat-card">
        <div class="stat-icon green">✉</div>
        <div class="stat-value">${totalMsgs}</div>
        <div class="stat-label">Total Messages</div>
      </div>
      <div class="card stat-card">
        <div class="stat-icon purple">📱</div>
        <div class="stat-value">${sources.length}</div>
        <div class="stat-label">Platforms</div>
        <div class="stat-change up">${sources.join(', ')}</div>
      </div>
      <div class="card stat-card">
        <div class="stat-icon yellow">🔄</div>
        <div class="stat-value">${sessions.filter(s => s.source === 'telegram').length}</div>
        <div class="stat-label">Telegram</div>
      </div>
    `;

    if (data.error) {
      document.getElementById('telegramList').innerHTML = `
        <div class="card"><div class="empty-state"><div class="empty-state-icon">⚠</div>
        <div class="empty-state-title">Error Loading Sessions</div>
        <div class="empty-state-desc">${escapeHtml(data.error)}</div></div></div>`;
      return;
    }

    if (sessions.length === 0) {
      document.getElementById('telegramList').innerHTML = `
        <div class="card"><div class="empty-state"><div class="empty-state-icon">📭</div>
        <div class="empty-state-title">No messaging sessions found</div>
        <div class="empty-state-desc">Chat on Telegram and they'll appear here</div></div></div>`;
      return;
    }

    document.getElementById('telegramList').innerHTML = `
      <div class="card">
        <div class="card-header"><span class="card-title">📋 Session History</span></div>
        <div style="overflow-x:auto">
          <table class="data-table" style="width:100%;border-collapse:collapse;font-size:13px">
            <thead>
              <tr style="border-bottom:1px solid var(--border);color:var(--text-muted);font-size:11px;text-transform:uppercase;letter-spacing:0.5px">
                <th style="padding:8px 12px;text-align:left">Platform</th>
                <th style="padding:8px 12px;text-align:left">Title</th>
                <th style="padding:8px 12px;text-align:center">Messages</th>
                <th style="padding:8px 12px;text-align:center">Model</th>
                <th style="padding:8px 12px;text-align:right">Tokens</th>
                <th style="padding:8px 12px;text-align:right">Started</th>
                <th style="padding:8px 12px;text-align:right">Status</th>
              </tr>
            </thead>
            <tbody>
              ${sessions.map(s => {
                const platformEmoji = { telegram: '✈️', discord: '💬', slack: '🔌', email: '📧' }[s.source] || '💬';
                const started = s.started ? new Date(s.started * 1000).toLocaleDateString() : '—';
                const status = s.ended ? '<span style="color:var(--text-muted)">⬤ Ended</span>' : '<span style="color:var(--green)">⬤ Active</span>';
                const totalTokens = (s.input_tokens || 0) + (s.output_tokens || 0);
                return `<tr style="border-bottom:1px solid var(--border)">
                  <td style="padding:8px 12px">${platformEmoji} ${s.source}</td>
                  <td style="padding:8px 12px;font-weight:500">${escapeHtml(s.title)}</td>
                  <td style="padding:8px 12px;text-align:center">${s.messages}</td>
                  <td style="padding:8px 12px;text-align:center;font-size:11px">${s.model ? escapeHtml(s.model.split('/').pop()) : '—'}</td>
                  <td style="padding:8px 12px;text-align:right;font-size:11px;color:var(--text-muted)">
                    ${totalTokens > 999 ? (totalTokens / 1000).toFixed(1) + 'k' : totalTokens}
                  </td>
                  <td style="padding:8px 12px;text-align:right;font-size:11px;color:var(--text-muted)">${started}</td>
                  <td style="padding:8px 12px;text-align:right">${status}</td>
                </tr>`;
              }).join('')}
            </tbody>
          </table>
        </div>
      </div>
      <div style="margin-top:8px;font-size:11px;color:var(--text-muted);text-align:center">
        Data from Hermes state.db · Auto-refresh to see new sessions
      </div>
    `;
  } catch (err) {
    document.getElementById('telegramList').innerHTML = `
      <div class="card"><div class="empty-state"><div class="empty-state-icon">⚠</div>
      <div class="empty-state-title">Connection Error</div>
      <div class="empty-state-desc">${escapeHtml(err.message)}</div></div></div>`;
  }
}
