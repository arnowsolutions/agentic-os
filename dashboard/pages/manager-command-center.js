/* Montefiore Urology — Manager Command Center (Tier 2: Jessie/Winnie/Kelly) */
async function renderManagerCommandCenter() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="pages-manager-cc">
      <style>
        .pages-manager-cc .mc-header {
          display:flex; justify-content:space-between; align-items:flex-start;
          margin-bottom:24px; flex-wrap:wrap; gap:16px;
        }
        .pages-manager-cc .mc-header-left h1 {
          font-size:1.6rem; font-weight:700; margin:0 0 4px;
        }
        .pages-manager-cc .mc-header-left p {
          margin:0; color:var(--text-muted); font-size:13px;
        }
        .pages-manager-cc .mc-command-grid {
          display:grid;
          grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));
          gap:12px; margin-bottom:20px;
        }
        .pages-manager-cc .mc-command-card {
          background:var(--bg-card); border:1px solid var(--border);
          border-radius:12px; padding:20px; cursor:pointer;
          transition:box-shadow .2s, transform .2s, border-color .2s;
          text-align:center;
        }
        .pages-manager-cc .mc-command-card:hover {
          box-shadow:0 4px 20px rgba(0,0,0,0.15);
          transform:translateY(-2px);
          border-color:var(--accent);
        }
        .pages-manager-cc .mc-command-card .mc-cmd-icon {
          font-size:2rem; margin-bottom:8px;
        }
        .pages-manager-cc .mc-command-card .mc-cmd-label {
          font-weight:600; font-size:14px; margin-bottom:2px;
        }
        .pages-manager-cc .mc-command-card .mc-cmd-desc {
          font-size:11px; color:var(--text-muted);
        }
        .pages-manager-cc .mc-command-card .mc-cmd-badge {
          display:inline-block; font-size:10px; padding:2px 8px;
          border-radius:10px; margin-top:6px; font-weight:500;
        }
        .pages-manager-cc .mc-result-card {
          background:var(--bg-card); border:1px solid var(--border);
          border-radius:12px; margin-bottom:16px; overflow:hidden;
        }
        .pages-manager-cc .mc-result-header {
          padding:14px 16px; font-weight:600; font-size:14px;
          border-bottom:1px solid var(--border);
          display:flex; align-items:center; gap:8px;
        }
        .pages-manager-cc .mc-result-body {
          padding:16px; font-size:13px; line-height:1.6;
        }
        .pages-manager-cc .mc-coverage-item {
          display:flex; justify-content:space-between; align-items:center;
          padding:8px 0; border-bottom:1px solid var(--border-dim);
        }
        .pages-manager-cc .mc-coverage-item:last-child { border:none; }
        .pages-manager-cc .mc-section-title {
          font-weight:600; font-size:13px; margin:16px 0 8px;
          color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px;
        }
        .pages-manager-cc .mc-flex-gap { display:flex; gap:16px; flex-wrap:wrap; }
        .pages-manager-cc .mc-stat-pill {
          display:inline-flex; align-items:center; gap:6px;
          padding:4px 12px; border-radius:20px; font-size:12px; font-weight:500;
        }
      </style>

      <div class="mc-header">
        <div class="mc-header-left">
          <h1>⚙️ Manager Command Center</h1>
          <p>Predetermined commands for scheduling, coverage, and team management</p>
        </div>
        <div class="btn-group">
          <button class="btn btn-sm btn-ghost" onclick="renderManagerCommandCenter()">🔄 Refresh</button>
        </div>
      </div>

      <!-- Command Buttons -->
      <div class="mc-command-grid">
        <div class="mc-command-card" onclick="_mc_run('coverage')">
          <div class="mc-cmd-icon">📅</div>
          <div class="mc-cmd-label">/coverage</div>
          <div class="mc-cmd-desc">Today's call + backup + gaps</div>
          <span class="mc-cmd-badge" style="background:rgba(0,122,255,0.12);color:#007aff">Real-time</span>
        </div>
        <div class="mc-command-card" onclick="_mc_run('team')">
          <div class="mc-cmd-icon">👥</div>
          <div class="mc-cmd-label">/team</div>
          <div class="mc-cmd-desc">All residents and their status</div>
          <span class="mc-cmd-badge" style="background:rgba(52,199,89,0.12);color:#34c759">15 residents</span>
        </div>
        <div class="mc-command-card" onclick="_mc_run('approvals')">
          <div class="mc-cmd-icon">✅</div>
          <div class="mc-cmd-label">/approvals</div>
          <div class="mc-cmd-desc">Pending swaps, PTO, call-outs</div>
          <span class="mc-cmd-badge" style="background:rgba(255,204,0,0.12);color:#ffcc00" id="mcPendingCount">0 pending</span>
        </div>
        <div class="mc-command-card" onclick="_mc_run('gaps')">
          <div class="mc-cmd-icon">⚠️</div>
          <div class="mc-cmd-label">/gaps</div>
          <div class="mc-cmd-desc">Uncovered shifts needing action</div>
          <span class="mc-cmd-badge" style="background:rgba(255,69,58,0.12);color:#ff453a">Needs review</span>
        </div>
        <div class="mc-command-card" onclick="_mc_run('today')">
          <div class="mc-cmd-icon">📋</div>
          <div class="mc-cmd-label">/today</div>
          <div class="mc-cmd-desc">Full daily briefing</div>
          <span class="mc-cmd-badge" style="background:rgba(175,82,222,0.12);color:#af52de">Summary</span>
        </div>
        <div class="mc-command-card" onclick="_mc_run('gme')">
          <div class="mc-cmd-icon">💰</div>
          <div class="mc-cmd-label">/gme</div>
          <div class="mc-cmd-desc">GME balances at a glance</div>
          <span class="mc-cmd-badge" style="background:rgba(52,199,89,0.12);color:#34c759">Kelly access</span>
        </div>
        <div class="mc-command-card" onclick="_mc_runSwap(true)">
          <div class="mc-cmd-icon">🔧</div>
          <div class="mc-cmd-label">Test Swap Processor</div>
          <div class="mc-cmd-desc">Dry-run swap email processor</div>
          <span class="mc-cmd-badge" style="background:rgba(0,122,255,0.12);color:#007aff">Dry-run</span>
        </div>
        <div class="mc-command-card" onclick="_mc_runSwap(false)">
          <div class="mc-cmd-icon">⚡</div>
          <div class="mc-cmd-label">Run Swap Processor</div>
          <div class="mc-cmd-desc">Live swap processing + emails</div>
          <span class="mc-cmd-badge" style="background:rgba(255,69,58,0.12);color:#ff453a">Live</span>
        </div>
      </div>

      <!-- Results Area -->
      <div id="mcResults">
        <div class="mc-result-card" style="border:1px dashed var(--border)">
          <div class="mc-result-body" style="text-align:center;padding:32px;color:var(--text-muted)">
            <div style="font-size:2rem;margin-bottom:8px">👆</div>
            <div style="font-weight:500">Tap a command above to run it</div>
            <div style="font-size:12px;margin-top:4px">Results appear here</div>
          </div>
        </div>
      </div>
    </div>
  `;
}

async function _mc_run(cmd) {
  const results = document.getElementById('mcResults');
  if (!results) return;
  results.innerHTML = '<div class="mc-result-card"><div class="mc-result-body"><div class="loading" style="padding:8px"><div class="loading-spinner" style="width:18px;height:18px"></div><span style="font-size:13px">Running /' + cmd + '...</span></div></div></div>';

  try {
    // Run the corresponding API calls
    let html = '';
    if (cmd === 'coverage') {
      html = await _mc_coverage();
    } else if (cmd === 'team') {
      html = await _mc_team();
    } else if (cmd === 'approvals') {
      html = await _mc_approvals();
    } else if (cmd === 'gaps') {
      html = await _mc_gaps();
    } else if (cmd === 'today') {
      html = await _mc_today();
    } else if (cmd === 'gme') {
      html = await _mc_gme();
    }
    results.innerHTML = html;
  } catch (err) {
    results.innerHTML = `<div class="mc-result-card"><div class="mc-result-body"><div class="empty-state"><div class="empty-state-icon">⚠️</div><div class="empty-state-title">Error</div><div class="empty-state-desc">${escapeHtml(err.message)}</div></div></div></div>`;
  }
}

async function _mc_coverage() {
  const [oncallData, scheduleData] = await Promise.all([
    api.get('/api/oncall/now').catch(() => ({})),
    api.get('/api/oncall/schedule').catch(() => ({})),
  ]);
  const oncall = oncallData.oncall || [];
  const hospitals = scheduleData.hospitals || [];
  const today = new Date();
  const todayStr = today.toISOString().slice(0,10);

  let html = `<div class="mc-result-card">
    <div class="mc-result-header">📅 Coverage — ${today.toLocaleDateString('en-US', { weekday:'long', month:'long', day:'numeric', year:'numeric' })}</div>
    <div class="mc-result-body">`;

  if (oncall.length > 0) {
    html += oncall.map(e => `
      <div class="mc-coverage-item">
        <div><strong>🏥 ${escapeHtml(e.hospital)}</strong></div>
        <div class="text-right">
          <div>Primary: <strong>${escapeHtml(e.primary_attending || '—')}</strong></div>
          <div class="text-xs text-muted">Backup: ${escapeHtml(e.backup_attending || '—')} · Peds: ${escapeHtml(e.peds_attending || '—')}</div>
        </div>
      </div>
    `).join('');
  } else {
    html += `<div class="text-muted"><em>No call data for today. Schedule runs Jul 1 – Dec 31, 2026.</em></div>`;
  }

  html += `<div class="mc-section-title">Hospitals on File</div>
    <div class="mc-flex-gap">
      ${hospitals.map(h => `
        <span class="mc-stat-pill" style="background:rgba(0,122,255,0.08);color:var(--text)">
          🏥 ${escapeHtml(h.name)} — ${h.total_dates} days (${h.start_date} → ${h.end_date})
        </span>
      `).join('')}
    </div>`;

  html += `<div class="mc-section-title">Coverage Status</div>
    <div class="mc-flex-gap">
      <span class="mc-stat-pill" style="background:rgba(52,199,89,0.12);color:#34c759">✅ ${oncall.length} assignments today</span>
      <span class="mc-stat-pill" style="background:rgba(0,122,255,0.12);color:#007aff">📅 ${hospitals.reduce((s,h) => s + h.total_dates, 0)} total schedule entries</span>
    </div>`;

  html += `</div></div>`;
  return html;
}

async function _mc_team() {
  const data = await api.get('/api/crm/contacts').catch(() => ({ contacts: [] }));
  const residents = (data.contacts || []).filter(c => c.category === 'Resident')
    .sort((a,b) => (a.lastName || '').localeCompare(b.lastName || ''));

  let html = `<div class="mc-result-card">
    <div class="mc-result-header">👥 My Team — ${residents.length} Residents</div>
    <div class="mc-result-body">
      <div class="mc-flex-gap" style="margin-bottom:12px">
        <span class="mc-stat-pill" style="background:rgba(52,199,89,0.12);color:#34c759">✅ ${residents.length} total</span>
        <span class="mc-stat-pill" style="background:rgba(0,122,255,0.12);color:#007aff">PG-1 to PG-5</span>
      </div>
      <table class="ud-gme-table" style="width:100%">
        <thead><tr>
          <th>Name</th><th>PGY</th><th>GME Used</th><th>GME Left</th><th>Status</th>
        </tr></thead>
        <tbody>
          ${residents.map(r => {
            const reims = r.reimbursements || [];
            const used = reims.reduce((s, rem) => s + (rem.amount || 0), 0);
            const remaining = 1250 - used;
            const status = remaining <= 0 ? 'Exhausted' : remaining < 300 ? 'Low' : 'Available';
            const statusColor = remaining <= 0 ? 'var(--red)' : remaining < 300 ? 'var(--yellow)' : 'var(--green)';
            return `<tr>
              <td><strong>${escapeHtml(r.firstName)} ${escapeHtml(r.lastName)}</strong></td>
              <td><span class="badge badge-info">${escapeHtml(r.pgy || '—')}</span></td>
              <td>$${used.toLocaleString()}</td>
              <td style="color:${statusColor}">$${Math.max(remaining, 0).toLocaleString()}</td>
              <td><span class="badge" style="background:${statusColor}22;color:${statusColor}">${status}</span></td>
            </tr>`;
          }).join('')}
        </tbody>
      </table>
    </div></div>`;
  return html;
}

async function _mc_approvals() {
  const data = await api.get('/api/crm/contacts').catch(() => ({ contacts: [] }));
  const contacts = data.contacts || [];
  // Look for any CRM notes that might indicate pending swaps or PTO
  const residents = contacts.filter(c => c.category === 'Resident');
  const expended = residents.filter(r => {
    const reims = r.reimbursements || [];
    return reims.some(rem => rem.status === 'pending' || rem.status === 'submitted');
  });

  let html = `<div class="mc-result-card">
    <div class="mc-result-header">✅ Pending Approvals</div>
    <div class="mc-result-body">`;

  if (expended.length > 0) {
    html += expended.map(r => {
      const pending = (r.reimbursements || []).filter(rem => rem.status === 'pending' || rem.status === 'submitted');
      return pending.map(p => `
        <div class="mc-coverage-item">
          <div><strong>${escapeHtml(r.firstName)} ${escapeHtml(r.lastName)}</strong> — ${escapeHtml(p.category || 'Reimbursement')}</div>
          <div class="text-right">
            <div>$${(p.amount || 0).toFixed(2)}</div>
            <div class="text-xs text-muted">${escapeHtml(p.date || '')} · <span class="badge badge-warning">${escapeHtml(p.status)}</span></div>
          </div>
        </div>
      `).join('');
    }).join('');
  } else {
    html += `<div class="text-muted"><em>No pending approvals at this time.</em></div>`;
    html += `<div class="mc-section-title">Upcoming PTO</div>
      <div class="text-muted text-sm">PTO tracking coming soon — will integrate with Qgenda vacation calendar.</div>`;
  }

  html += `</div></div>`;
  return html;
}

async function _mc_gaps() {
  const data = await api.get('/api/oncall/schedule').catch(() => ({}));
  const hospitals = data.hospitals || [];
  const now = new Date();
  const todayStr = now.toISOString().slice(0,10);

  let html = `<div class="mc-result-card">
    <div class="mc-result-header">⚠️ Coverage Gaps</div>
    <div class="mc-result-body">`;

  // Check if the faculty schedule has started
  if (todayStr < '2026-07-01') {
    html += `<div class="text-muted"><em>Schedule starts Jul 1, 2026. No active gaps to report.</em></div>`;
  } else {
    html += `<div class="text-muted"><em>Gap detection scans the next 7 days for uncovered shifts. Coming with live Qgenda integration.</em></div>`;
  }

  html += `<div class="mc-section-title">Hospital Schedule Ranges</div>
    <div class="mc-flex-gap">
      ${hospitals.map(h => `
        <span class="mc-stat-pill" style="background:rgba(255,69,58,0.08);color:var(--text)">
          🏥 ${escapeHtml(h.name)}: ${escapeHtml(h.start_date)} → ${escapeHtml(h.end_date)} (${h.total_dates} days)
        </span>
      `).join('')}
    </div>`;

  if (hospitals.length > 0) {
    html += `<div class="mc-section-title">Unique Attendings</div><div class="mc-flex-gap">`;
    const allDocs = new Set();
    hospitals.forEach(h => (h.unique_primary_attendings || []).forEach(d => allDocs.add(d)));
    allDocs.forEach(d => {
      html += `<span class="badge badge-info" style="font-size:11px">${escapeHtml(d.substring(0,25))}</span> `;
    });
    html += `</div>`;
  }

  html += `</div></div>`;
  return html;
}

async function _mc_today() {
  const coverageHtml = await _mc_coverage();
  const parts = coverageHtml.split('</div></div>');
  const coverageBody = parts.slice(0, -1).join('</div></div>') || coverageHtml;

  const [contactsData] = await Promise.all([
    api.get('/api/crm/contacts').catch(() => ({ contacts: [] })),
  ]);
  const contacts = contactsData.contacts || [];
  const residents = contacts.filter(c => c.category === 'Resident');
  const totalPool = residents.length * 1250;
  const totalUsed = residents.reduce((s, r) => s + (r.reimbursements || []).reduce((ss, rem) => ss + (rem.amount || 0), 0), 0);
  const totalRemaining = totalPool - totalUsed;

  let html = `<div class="mc-result-card">
    <div class="mc-result-header">📋 Daily Briefing — ${new Date().toLocaleDateString('en-US', { weekday:'long', month:'long', day:'numeric', year:'numeric' })}</div>
    <div class="mc-result-body">
      <div class="mc-flex-gap" style="margin-bottom:16px">
        <span class="mc-stat-pill" style="background:rgba(52,199,89,0.12);color:#34c759">👥 ${residents.length} residents</span>
        <span class="mc-stat-pill" style="background:rgba(0,122,255,0.12);color:#007aff">💰 $${totalUsed.toLocaleString()} / $${totalPool.toLocaleString()} GME used</span>
        <span class="mc-stat-pill" style="background:rgba(255,204,0,0.12);color:#ffcc00">📅 ${new Date().toLocaleDateString('en-US', { weekday:'long' })}</span>
      </div>
      <div class="mc-section-title">Today's Coverage</div>
    `;

  // Reuse coverage data
  const oncallData = await api.get('/api/oncall/now').catch(() => ({}));
  const oncall = oncallData.oncall || [];
  if (oncall.length > 0) {
    oncall.slice(0,5).forEach(e => {
      html += `<div class="mc-coverage-item">
        <div><strong>🏥 ${escapeHtml(e.hospital)}</strong> — ${escapeHtml(e.primary_attending || '—')}</div>
        <div class="text-xs text-muted">Backup: ${escapeHtml(e.backup_attending || '—')}</div>
      </div>`;
    });
  } else {
    html += `<div class="text-muted"><em>No call today. Schedule runs Jul–Dec 2026.</em></div>`;
  }

  html += `<div class="mc-section-title" style="margin-top:16px">Residents Needing Attention</div>`;
  const exhausted = residents.filter(r => {
    const used = (r.reimbursements || []).reduce((s, rem) => s + (rem.amount || 0), 0);
    return used >= 1200;
  });
  const zeroUsed = residents.filter(r => {
    const used = (r.reimbursements || []).reduce((s, rem) => s + (rem.amount || 0), 0);
    return used === 0;
  });

  if (exhausted.length > 0) {
    html += exhausted.map(r => `<div class="mc-coverage-item"><span>⚠️ <strong>${escapeHtml(r.firstName)} ${escapeHtml(r.lastName)}</strong> — GME exhausted</span></div>`).join('');
  }
  if (zeroUsed.length > 0) {
    html += zeroUsed.map(r => `<div class="mc-coverage-item"><span>💡 <strong>${escapeHtml(r.firstName)} ${escapeHtml(r.lastName)}</strong> — hasn't used any GME yet</span></div>`).join('');
  }
  if (exhausted.length === 0 && zeroUsed.length === 0) {
    html += `<div class="text-muted text-sm">All residents are in good standing.</div>`;
  }

  html += `</div></div>`;
  return html;
}

async function _mc_gme() {
  const [summary, residents] = await Promise.all([
    api.getGmeSummary().catch(() => ({})),
    api.getGmeResidents().catch(() => ({ residents: [] })),
  ]);
  const gmeResidents = residents.residents || [];
  const totalPool = summary.total_pool || (gmeResidents.length * 1250);
  const totalUsed = summary.total_used || 0;
  const totalRemaining = summary.total_remaining || 0;
  const usedPct = totalPool > 0 ? Math.round((totalUsed / totalPool) * 100) : 0;

  let html = `<div class="mc-result-card">
    <div class="mc-result-header">💰 GME Status</div>
    <div class="mc-result-body">
      <div class="mc-flex-gap" style="margin-bottom:16px">
        <span class="mc-stat-pill" style="background:rgba(52,199,89,0.12);color:#34c759">$${totalUsed.toLocaleString()} used</span>
        <span class="mc-stat-pill" style="background:rgba(0,122,255,0.12);color:#007aff">$${totalRemaining.toLocaleString()} remaining</span>
        <span class="mc-stat-pill" style="background:rgba(255,204,0,0.12);color:#ffcc00">${usedPct}% of pool</span>
        <span class="mc-stat-pill" style="background:rgba(175,82,222,0.12);color:#af52de">${gmeResidents.length} residents</span>
      </div>
      <table class="ud-gme-table" style="width:100%">
        <thead><tr>
          <th>Resident</th><th>PGY</th><th>Used</th><th>Left</th><th>Remaining %</th>
        </tr></thead>
        <tbody>
          ${gmeResidents.sort((a,b) => b.total_used - a.total_used).map(r => {
            const remaining = 1250 - r.total_used;
            const pct = Math.min(Math.round((r.total_used / 1250) * 100), 100);
            const color = pct >= 90 ? 'var(--red)' : pct >= 70 ? 'var(--yellow)' : 'var(--green)';
            return `<tr>
              <td><strong>${escapeHtml(r.firstName)} ${escapeHtml(r.lastName)}</strong></td>
              <td><span class="badge badge-info">${escapeHtml(r.pgy || '—')}</span></td>
              <td>$${r.total_used.toLocaleString()}</td>
              <td style="color:${color}">$${Math.max(remaining,0).toLocaleString()}</td>
              <td><div class="ud-bar-bg" style="max-width:80px"><div class="ud-bar-fill" style="width:${pct}%;background:${color}"></div></div></td>
            </tr>`;
          }).join('')}
        </tbody>
      </table>
    </div></div>`;
  return html;
}

async function _mc_runSwap(dryRun) {
  const results = document.getElementById('mcResults');
  if (!results) return;
  results.innerHTML = `<div class="mc-result-card"><div class="mc-result-body"><div class="loading" style="padding:8px"><div class="loading-spinner" style="width:18px;height:18px"></div><span style="font-size:13px">Running swap processor (${dryRun ? 'dry-run' : 'live'})...</span></div></div></div>`;
  try {
    const res = await fetch(`/api/swap/process?dry_run=${dryRun}`, { method: 'POST' });
    const data = await res.json();
    const ok = res.ok && data.success;
    const stdout = escapeHtml(data.stdout || '').replace(/\n/g, '<br>');
    const stderr = escapeHtml(data.stderr || '').replace(/\n/g, '<br>');
    results.innerHTML = `
      <div class="mc-result-card" style="border-color:${ok ? 'var(--green)' : 'var(--red)'}">
        <div class="mc-result-header">${ok ? '✅' : '❌'} Swap Processor — ${dryRun ? 'Dry Run' : 'Live'}</div>
        <div class="mc-result-body">
          <div class="mc-flex-gap" style="margin-bottom:12px">
            <span class="mc-stat-pill" style="background:${ok ? 'rgba(52,199,89,0.12)' : 'rgba(255,69,58,0.12)'};color:${ok ? '#34c759' : '#ff453a'}">${ok ? 'Success' : 'Failed'}</span>
          </div>
          <div class="mc-section-title">stdout</div>
          <div class="hlt-raw" style="max-height:240px;margin-bottom:12px">${stdout || '<em>No output</em>'}</div>
          ${stderr ? `<div class="mc-section-title">stderr</div><div class="hlt-raw" style="max-height:160px;color:var(--red)">${stderr}</div>` : ''}
        </div>
      </div>`;
  } catch (err) {
    results.innerHTML = `<div class="mc-result-card"><div class="mc-result-body"><div class="empty-state"><div class="empty-state-icon">⚠️</div><div class="empty-state-title">Request failed</div><div class="empty-state-desc">${escapeHtml(err.message)}</div></div></div></div>`;
  }
}
