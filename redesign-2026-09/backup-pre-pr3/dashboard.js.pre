/* ═══════════════════════════════════════════════════════════════════════
   Dashboard — Clean Overview
   Key metrics, agent status, recent activity. No emoji.
   ═══════════════════════════════════════════════════════════════════ */

async function renderDashboard() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">Dashboard</h1>
        <p class="page-subtitle">System overview and real-time agent monitoring</p>
      </div>
      <div class="btn-group">
        <button class="btn btn-primary btn-sm" onclick="runQuickSkill()">Run Skill</button>
        <button class="btn btn-sm" onclick="navigate('backups')">Backup</button>
        <button class="btn btn-ghost btn-sm" onclick="renderDashboard()">Refresh</button>
      </div>
    </div>
    <div id="dashStats" class="grid grid-4 mb-4"></div>
    <div class="grid grid-3 mb-4">
      <div class="card" style="grid-column:span 2">
        <div class="card-header"><span class="card-title">Agent Status</span></div>
        <div id="agentList"><div class="skeleton" style="height:80px"></div></div>
      </div>
      <div class="card">
        <div class="card-header"><span class="card-title">Recent Activity</span></div>
        <div id="recentActivity"><div class="skeleton" style="height:80px"></div></div>
      </div>
    </div>
    <div id="dashQuickActions" class="mb-4"></div>
  `;

  try {
    const [status, skills, audit] = await Promise.all([
      api.getStatus(),
      api.getSkills(),
      api.getAudit(10)
    ]);

    const agents = status.agents || [];
    const skillsCount = status.skills_count || 0;
    const entries = (audit.entries || []).slice(0, 10);
    const online = agents.filter(a => a.status === 'online').length;

    // ── Stat cards ──
    document.getElementById('dashStats').innerHTML = `
      <div class="stat-card">
        <div class="stat-icon" style="color:var(--accent)">&#9679;</div>
        <div class="stat-value">${skillsCount}</div>
        <div class="stat-label">Skills</div>
        <div class="stat-change" style="color:var(--accent-light)">installed &amp; ready</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="color:${online === agents.length ? 'var(--green)' : online > 0 ? 'var(--yellow)' : 'var(--red)'}">&#9679;</div>
        <div class="stat-value">${online}<span style="font-size:0.55em;color:var(--text-muted)">/${agents.length}</span></div>
        <div class="stat-label">Agents Online</div>
        <div class="stat-change" style="color:${online === agents.length ? 'var(--green)' : 'var(--red)'}">${online === agents.length ? 'All operational' : agents.length - online + ' offline'}</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="color:var(--blue)">&#9679;</div>
        <div class="stat-value">${entries.length}</div>
        <div class="stat-label">Recent Events</div>
        <div class="stat-change" style="color:var(--text-muted)">last 10 activities</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="color:var(--purple)">&#9679;</div>
        <div class="stat-value">${(skills || []).filter(s => s.scores && s.scores.length > 0).length}</div>
        <div class="stat-label">Tracked Skills</div>
        <div class="stat-change" style="color:var(--text-muted)">with eval scores</div>
      </div>
    `;

    // ── Agent status ──
    document.getElementById('agentList').innerHTML = `
      <div style="display:flex;flex-wrap:wrap;gap:10px;padding:4px 0">
        ${agents.map(a => {
          const isOnline = a.status === 'online';
          const dotColor = isOnline ? 'var(--green)' : 'var(--red)';
          return `<div class="agent-health-card" style="flex:1;min-width:180px;padding:12px 14px">
            <div class="agent-health-avatar" style="background:${isOnline ? 'var(--green-dim)' : 'var(--red-dim)'};color:${dotColor};font-size:0.75rem;width:36px;height:36px;border-radius:8px">${a.name[0].toUpperCase()}</div>
            <div class="agent-health-info">
              <div class="agent-health-name">${a.name}</div>
              <div class="agent-health-status" style="color:${dotColor}">${a.status}</div>
            </div>
          </div>`;
        }).join('')}
      </div>
    `;

    // ── Recent activity ──
    document.getElementById('recentActivity').innerHTML = entries.length === 0
      ? '<div class="empty-state" style="padding:16px"><div class="empty-state-icon" style="font-size:20px">—</div><div class="empty-state-title" style="font-size:0.8rem">No activity yet</div></div>'
      : `<div style="display:flex;flex-direction:column;gap:2px;max-height:320px;overflow-y:auto">${entries.slice(0, 6).map(e => {
          const isSkill = e.action === 'skill_run';
          return `<div class="event-item" style="border:none;border-radius:6px;padding:7px 10px">
            <div class="event-dot" style="background:${isSkill ? 'var(--accent)' : 'var(--blue)'};min-width:6px;width:6px;height:6px;margin-top:5px"></div>
            <div class="event-content">
              <div class="event-title" style="font-size:0.78rem">${e.action}${e.skill ? ': ' + e.skill : ''}</div>
              <div class="event-meta" style="font-size:0.68rem">${e.agent ? e.agent : ''} ${e.run_id ? '#' + e.run_id : ''}</div>
            </div>
            <div class="event-time" style="font-size:0.68rem">${timeAgo(e.timestamp)}</div>
          </div>`;
        }).join('')}</div>`;

    // ── Quick actions ──
    document.getElementById('dashQuickActions').innerHTML = `
      <div class="card">
        <div class="card-header"><span class="card-title">Quick Actions</span></div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;padding:4px 0">
          <button class="btn btn-sm" onclick="navigate('chat')">AI Chat</button>
          <button class="btn btn-sm" onclick="navigate('skills')">Skills Hub</button>
          <button class="btn btn-sm" onclick="navigate('scheduler')">Scheduler</button>
          <button class="btn btn-sm" onclick="navigate('calendar')">Calendar</button>
          <button class="btn btn-sm" onclick="navigate('kanban')">Kanban</button>
          <button class="btn btn-sm" onclick="navigate('cost')">Cost</button>
          <button class="btn btn-sm" onclick="navigate('audit')">Audit Log</button>
          <button class="btn btn-sm" onclick="navigate('backups')">Backups</button>
        </div>
      </div>
    `;

  } catch (err) {
    document.getElementById('dashStats').innerHTML = `<div class="card" style="grid-column:1/-1"><div class="empty-state"><div class="empty-state-icon">—</div><div class="empty-state-title">Connection Error</div><div class="empty-state-desc">${escapeHtml(err.message)}</div><button class="btn btn-primary mt-3" onclick="navigate('dashboard')">Retry</button></div></div>`;
  }
}

// ── Quick Run Skill ──
async function runQuickSkill() {
  showModal('Run Skill', `
    <div class="form-group">
      <label class="form-label">Skill</label>
      <select id="qrSkill" class="form-input">
        <option value="">Select a skill...</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">Input (optional)</label>
      <textarea id="qrInput" class="form-textarea" rows="3" placeholder="Enter input for the skill..."></textarea>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">Cancel</button>
    <button class="btn btn-primary" onclick="executeQuickRun()">Run</button>
  `);
  try {
    const skills = await api.getSkills();
    const select = document.getElementById('qrSkill');
    skills.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.name;
      opt.textContent = s.name.replace(/-/g, ' ');
      select.appendChild(opt);
    });
  } catch {}
}

async function executeQuickRun() {
  const name = document.getElementById('qrSkill').value;
  const input = document.getElementById('qrInput').value;
  if (!name) { showToast('Please select a skill', 'warning'); return; }
  try {
    const r = await api.runSkill(name, input);
    closeModal();
    showToast(`"${name}" dispatched to ${r.agent} #${r.run_id}`, 'success');
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
}
