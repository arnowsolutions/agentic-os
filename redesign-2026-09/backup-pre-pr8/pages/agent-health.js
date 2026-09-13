let agentHealthInterval = null;

async function renderAgentHealth() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">Agent Health</div>
        <div class="page-subtitle">Real-time monitoring of all 3 agents</div>
      </div>
      <div class="btn-group">
        <label class="switch" title="Auto-refresh every 5s">
          <input type="checkbox" id="healthAutoRefresh" checked onchange="toggleHealthAutoRefresh()">
          <span class="switch-slider"></span>
        </label>
        <span class="text-sm text-muted">Auto</span>
        <button class="btn btn-primary" onclick="refreshAgentHealth()">🔄 Refresh Now</button>
      </div>
    </div>
    <div id="agentHealthCards" class="grid grid-3" style="margin-bottom:20px">
      <div class="skeleton" style="height:180px"></div>
      <div class="skeleton" style="height:180px"></div>
      <div class="skeleton" style="height:180px"></div>
    </div>
    <div class="section-title">Health Overview</div>
    <div class="card" id="healthOverviewCard">
      <div class="loading"><div class="loading-spinner"></div><span>Loading health data...</span></div>
    </div>
  `;
  await refreshAgentHealth();
  if (document.getElementById('healthAutoRefresh')?.checked) {
    startHealthAutoRefresh();
  }
}

function startHealthAutoRefresh() {
  stopHealthAutoRefresh();
  agentHealthInterval = setInterval(refreshAgentHealth, 5000);
}

function stopHealthAutoRefresh() {
  if (agentHealthInterval) {
    clearInterval(agentHealthInterval);
    agentHealthInterval = null;
  }
}

function toggleHealthAutoRefresh() {
  if (document.getElementById('healthAutoRefresh')?.checked) {
    startHealthAutoRefresh();
  } else {
    stopHealthAutoRefresh();
  }
}

async function refreshAgentHealth() {
  try {
    const data = await api.getAgentHealth();
    const agents = data.agents || [];
    const cards = document.getElementById('agentHealthCards');
    if (!cards) return;
    const agentIcons = { opencode: '🔧', hermes: '⚡', gemini: '🧠' };
    const agentColors = { opencode: 'purple', hermes: 'green', gemini: 'blue' };
    const healthLabels = {
      not_configured: { label: 'Not Configured', color: 'var(--text-muted)', badge: 'badge-secondary' },
      offline: { label: 'Offline', color: 'var(--red)', badge: 'badge-danger' },
      no_usage_yet: { label: 'No Usage Yet', color: 'var(--yellow)', badge: 'badge-warning' },
      healthy: { label: 'Healthy', color: 'var(--green)', badge: 'badge-success' }
    };
    
    cards.innerHTML = agents.map(a => {
      // Format last seen
      let lastSeenDisplay = 'Never';
      if (a.last_seen) {
        try {
          const date = new Date(a.last_seen);
          lastSeenDisplay = date.toLocaleString();
        } catch {
          lastSeenDisplay = a.last_seen;
        }
      }
      
      // Get health display config
      const health = healthLabels[a.health_label] || healthLabels.no_usage_yet;
      const isOnline = a.availability === 'online';
      
      return `
      <div class="agent-health-card">
        <div class="agent-health-avatar" style="background:var(--${agentColors[a.name] || 'accent'}-dim);color:var(--${agentColors[a.name] || 'accent'})">
          ${agentIcons[a.name] || '🤖'}
        </div>
        <div class="agent-health-info">
          <div class="agent-health-name" style="text-transform:capitalize">${a.name}</div>
          <div class="agent-health-status">
            <span class="agent-dot ${isOnline ? 'online' : 'offline'}"></span>
            <span style="color:${health.color}">${health.label}</span>
          </div>
          <div class="agent-health-stats">
            <div class="agent-health-stat">
              <div class="agent-health-stat-value" style="color:var(--text-secondary);font-size:13px">
                ${a.total_runs !== undefined ? a.total_runs : '-'}
              </div>
              <div class="agent-health-stat-label">Runs</div>
            </div>
            <div class="agent-health-stat">
              <div class="agent-health-stat-value" style="color:${isOnline ? 'var(--green)' : 'var(--red)'};font-size:13px">
                ${isOnline ? 'online' : 'offline'}
              </div>
              <div class="agent-health-stat-label">Status</div>
            </div>
            <div class="agent-health-stat">
              <div class="agent-health-stat-value text-sm" style="font-size:10px;color:var(--text-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:80px" title="${lastSeenDisplay}">
                ${a.last_seen ? lastSeenDisplay : 'Never'}
              </div>
              <div class="agent-health-stat-label">Last Activity</div>
            </div>
          </div>
          ${a.health_reason ? `<div style="font-size:10px;color:var(--text-muted);margin-top:6px">${a.health_reason}</div>` : ''}
        </div>
      </div>
    `}).join('');
    
    // Update overview with real aggregation
    const overview = document.getElementById('healthOverviewCard');
    if (overview) {
      const counts = {
        not_configured: agents.filter(a => a.health_label === 'not_configured').length,
        offline: agents.filter(a => a.health_label === 'offline').length,
        no_usage_yet: agents.filter(a => a.health_label === 'no_usage_yet').length,
        healthy: agents.filter(a => a.health_label === 'healthy').length,
      };
      const total = agents.length;
      
      overview.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:space-between">
          <div>
            <div style="font-size:14px;font-weight:600">System Status</div>
            <div style="font-size:12px;color:var(--text-secondary);margin-top:4px">
              <span class="badge badge-success">${counts.healthy} healthy</span>
              <span class="badge badge-warning">${counts.no_usage_yet} no usage</span>
              <span class="badge badge-danger">${counts.offline} offline</span>
              ${counts.not_configured > 0 ? `<span class="badge badge-secondary">${counts.not_configured} not configured</span>` : ''}
            </div>
            <div style="font-size:11px;color:var(--text-muted);margin-top:4px">
              Last updated: ${new Date(data.updated).toLocaleTimeString()}
            </div>
          </div>
          <div class="status-indicator ${counts.healthy === total ? 'online' : counts.healthy > 0 ? 'warning' : 'offline'}">
            <span class="agent-dot ${counts.healthy === total ? 'online' : counts.healthy > 0 ? 'warning' : 'offline'}"></span>
            ${counts.healthy === total ? 'All Healthy' : counts.healthy > 0 ? 'Partial' : 'Issues'}
          </div>
        </div>
      `;
    }
  } catch (err) {
    const cards = document.getElementById('agentHealthCards');
    if (cards) cards.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><div class="empty-state-icon">⚠</div><div class="empty-state-title">Failed to load health data</div><div class="empty-state-desc">${escapeHtml(err.message)}</div></div>`;
  }
}
