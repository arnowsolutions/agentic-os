async function renderEvalDashboard() {
  const content = document.getElementById('pageContent');

  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">📊 Eval Dashboard</div>
        <div class="page-subtitle">Evaluation completion tracking — auto-triggered from OR schedule</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderEvalDashboard()">🔄 Refresh</button>
      </div>
    </div>
    <div id="edContent"><div class="loading"><div class="loading-spinner"></div><span>Loading eval data...</span></div></div>
    <style id="edStyles"></style>
  `;

  try {
    const res = await fetch('/api/eval/dashboard');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderEvalContent(data);
  } catch (err) {
    document.getElementById('edContent').innerHTML = `
      <div class="card" style="text-align:center;padding:40px">
        <div style="font-size:32px;margin-bottom:12px">⚠️</div>
        <div style="color:var(--text-muted)">Could not load eval data: ${escapeHtml(err.message)}</div>
      </div>
    `;
  }
}

function renderEvalContent(data) {
  const { summary, resident_stats, faculty_stats, procedure_stats, recent_activity } = data;
  const container = document.getElementById('edContent');

  // ─── Styles ───
  document.getElementById('edStyles').textContent = `
    .ed-grid { display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin-bottom:16px; }
    .ed-stat { background:var(--bg-card);border-radius:var(--radius-md);border:1px solid var(--border);padding:16px;text-align:center; }
    .ed-stat .num { font-size:32px;font-weight:700; }
    .ed-stat .num.green { color:#00b894; }
    .ed-stat .num.yellow { color:#fdcb6e; }
    .ed-stat .num.red { color:#d63031; }
    .ed-stat .num.blue { color:#0984e3; }
    .ed-stat .label { font-size:11px;text-transform:uppercase;color:var(--text-muted);margin-top:4px;letter-spacing:0.5px; }
    .ed-section { background:var(--bg-card);border-radius:var(--radius-md);border:1px solid var(--border);padding:16px;margin-bottom:12px; }
    .ed-section h3 { font-size:14px;font-weight:600;margin:0 0 12px 0;display:flex;align-items:center;gap:6px; }
    .ed-table { width:100%;border-collapse:collapse;font-size:12px; }
    .ed-table th { text-align:left;padding:8px 10px;border-bottom:1px solid var(--border);font-weight:600;font-size:11px;text-transform:uppercase;color:var(--text-muted); }
    .ed-table td { padding:8px 10px;border-bottom:1px solid rgba(255,255,255,0.04); }
    .ed-table tr:hover td { background:rgba(255,255,255,0.03); }
    .ed-badge { display:inline-block;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:600; }
    .ed-badge.green { background:rgba(0,184,148,0.15);color:#00b894; }
    .ed-badge.yellow { background:rgba(253,203,110,0.15);color:#fdcb6e; }
    .ed-badge.red { background:rgba(214,48,49,0.15);color:#d63031; }
    .ed-bar { height:6px;border-radius:3px;background:rgba(255,255,255,0.06);overflow:hidden;min-width:80px; }
    .ed-bar-fill { height:100%;border-radius:3px;transition:width 0.6s ease; }
    .ed-proc-grid { display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:8px; }
    .ed-proc-card { padding:12px;background:rgba(255,255,255,0.02);border-radius:var(--radius-sm);border:1px solid rgba(255,255,255,0.04); }
    .ed-proc-card .proc-name { font-size:12px;font-weight:600;margin-bottom:6px;color:var(--text); }
    .ed-proc-card .proc-row { display:flex;justify-content:space-between;align-items:center;font-size:11px;color:var(--text-muted); }
    .ed-activity { max-height:400px;overflow-y:auto; }
    .ed-activity-item { padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.04);font-size:12px;line-height:1.5; }
    .ed-activity-item:last-child { border:none; }
    .ed-tabs { display:flex;gap:4px;margin-bottom:12px; }
    .ed-tab { padding:6px 16px;border-radius:var(--radius-sm);font-size:12px;font-weight:500;cursor:pointer;background:rgba(255,255,255,0.04);border:1px solid transparent; }
    .ed-tab:hover { background:rgba(255,255,255,0.08); }
    .ed-tab.active { background:rgba(106,176,243,0.15);border-color:rgba(106,176,243,0.3);color:#6ab0f3; }
    .ed-tab-content { display:none; }
    .ed-tab-content.active { display:block; }
  `;

  const rateNum = summary.completion_rate || 0;
  const rateClass = rateNum >= 80 ? 'green' : rateNum >= 50 ? 'yellow' : 'red';

  // ─── Summary stats ───
  const statsHtml = `
    <div class="ed-grid">
      <div class="ed-stat"><div class="num blue">${summary.total}</div><div class="label">Total Evals</div></div>
      <div class="ed-stat"><div class="num green">${summary.completed}</div><div class="label">Completed</div></div>
      <div class="ed-stat"><div class="num ${summary.pending > 0 ? 'yellow' : 'green'}">${summary.pending}</div><div class="label">Pending</div></div>
      <div class="ed-stat"><div class="num ${rateClass}">${rateNum}%</div><div class="label">Completion Rate</div></div>
      <div class="ed-stat"><div class="num blue">${summary.residents_total}</div><div class="label">Residents</div></div>
      <div class="ed-stat"><div class="num blue">${summary.faculty_total}</div><div class="label">Faculty</div></div>
    </div>
  `;

  // ─── Tabs ───
  const tabsHtml = `
    <div class="ed-tabs">
      <div class="ed-tab active" onclick="switchEdTab('residents')">👨‍⚕️ Residents</div>
      <div class="ed-tab" onclick="switchEdTab('faculty')">👩‍⚕️ Faculty</div>
      <div class="ed-tab" onclick="switchEdTab('procedures')">🔬 Procedures</div>
      <div class="ed-tab" onclick="switchEdTab('activity')">🕐 Recent</div>
    </div>
    <div class="ed-tab-content active" id="edTabResidents">${renderResidentTable(resident_stats)}</div>
    <div class="ed-tab-content" id="edTabFaculty">${renderFacultyTable(faculty_stats)}</div>
    <div class="ed-tab-content" id="edTabProcedures">${renderProcedureGrid(procedure_stats)}</div>
    <div class="ed-tab-content" id="edTabActivity">${renderActivityFeed(recent_activity)}</div>
  `;

  // ─── Footer ───
  const footerHtml = `
    <div class="ed-section">
      <h3>ℹ️ About This Dashboard</h3>
      <div style="font-size:12px;color:var(--text-muted);line-height:1.6">
        <p style="margin:0 0 4px 0">Data sourced from the <strong>eval spreadsheet</strong> (all 20 FAC/RES sheets) and the <strong>eval_tracking</strong> PostgreSQL table.</p>
        <p style="margin:0;font-size:11px">Auto-triggered evals from the OR schedule write identity rows to the spreadsheet — the same as if someone used the eval portal. When a Google Form is submitted, the Apps Script fills in the evaluation data. Dashboard reflects both manual and auto-triggered flows.</p>
      </div>
    </div>
  `;

  container.innerHTML = statsHtml + tabsHtml + footerHtml;
}

function renderResidentTable(stats) {
  const sorted = [...stats].sort((a, b) => a.completion_rate - b.completion_rate);
  const rows = sorted.map(r => {
    const pct = r.completion_rate || 0;
    const barColor = pct >= 80 ? '#00b894' : pct >= 50 ? '#fdcb6e' : '#d63031';
    const badge = pct >= 80 ? 'green' : pct >= 50 ? 'yellow' : 'red';
    return `<tr>
      <td><strong>${escapeHtml(r.name)}</strong><br><span style="font-size:10px;color:var(--text-muted)">${r.pgy || '?'}</span></td>
      <td style="color:var(--text-muted)">${r.total}</td>
      <td style="color:#00b894">${r.completed}</td>
      <td style="color:#fdcb6e">${r.pending}</td>
      <td><div class="ed-bar"><div class="ed-bar-fill" style="width:${pct}%;background:${barColor}"></div></div></td>
      <td><span class="ed-badge ${badge}">${pct}%</span></td>
    </tr>`;
  }).join('');

  return `
    <div class="ed-section">
      <h3>👨‍⚕️ Resident Completion <span style="font-weight:400;font-size:11px;color:var(--text-muted)">(sorted by rate ↑)</span></h3>
      <table class="ed-table">
        <thead><tr><th>Resident</th><th>Total</th><th>Done</th><th>Pending</th><th>Bar</th><th>Rate</th></tr></thead>
        <tbody>${rows || '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:16px">No data</td></tr>'}</tbody>
      </table>
    </div>
  `;
}

function renderFacultyTable(stats) {
  const rows = stats.map(f => {
    const pct = f.completion_rate || 0;
    const barColor = pct >= 80 ? '#00b894' : pct >= 50 ? '#fdcb6e' : '#d63031';
    return `<tr>
      <td><strong>${escapeHtml(f.name)}</strong></td>
      <td style="color:var(--text-muted)">${f.total}</td>
      <td style="color:#00b894">${f.completed}</td>
      <td style="color:#fdcb6e">${f.pending}</td>
      <td><div class="ed-bar"><div class="ed-bar-fill" style="width:${pct}%;background:${barColor}"></div></div></td>
    </tr>`;
  }).join('');

  return `
    <div class="ed-section">
      <h3>👩‍⚕️ Faculty Completion</h3>
      <table class="ed-table">
        <thead><tr><th>Faculty</th><th>Total</th><th>Done</th><th>Pending</th><th>Rate</th></tr></thead>
        <tbody>${rows || '<tr><td colspan="5" style="text-align:center;color:var(--text-muted);padding:16px">No data</td></tr>'}</tbody>
      </table>
    </div>
  `;
}

function renderProcedureGrid(stats) {
  const cards = stats.map(p => {
    const pct = p.completion_rate || 0;
    const barColor = pct >= 80 ? '#00b894' : pct >= 50 ? '#fdcb6e' : '#d63031';
    const shortName = p.procedure.split(' - ')[1] || p.procedure;
    return `<div class="ed-proc-card">
      <div class="proc-name">${shortName}</div>
      <div class="proc-row"><span>Total</span><span>${p.total}</span></div>
      <div class="proc-row"><span style="color:#00b894">Completed</span><span>${p.completed}</span></div>
      <div class="proc-row"><span style="color:#fdcb6e">Pending</span><span>${p.pending}</span></div>
      <div style="margin-top:8px"><div class="ed-bar"><div class="ed-bar-fill" style="width:${pct}%;background:${barColor}"></div></div></div>
      <div style="text-align:right;font-size:10px;color:var(--text-muted);margin-top:4px">${pct}%</div>
    </div>`;
  }).join('');

  return `
    <div class="ed-section">
      <h3>🔬 Procedure Breakdown</h3>
      <div class="ed-proc-grid">${cards || '<div style="color:var(--text-muted)">No data</div>'}</div>
    </div>
  `;
}

function renderActivityFeed(activity) {
  if (!activity || activity.length === 0) {
    return `<div class="ed-section"><h3>🕐 Recent Activity</h3><div style="text-align:center;padding:16px;color:var(--text-muted);font-size:13px">No completed evaluations yet</div></div>`;
  }
  const items = activity.map(e => {
    const ts = e.timestamp ? e.timestamp.slice(0, 10) : '?';
    const procShort = e.procedure ? e.procedure.split(' - ').pop() : '?';
    const who = e.role === 'Resident' ? e.resident_name : e.faculty_name;
    const by = e.role === 'Resident' ? e.faculty_name : e.resident_name;
    return `<div class="ed-activity-item">
      <span style="color:var(--text-muted);font-size:11px">${ts}</span>
      <span style="margin:0 6px;color:#555">|</span>
      <strong>${escapeHtml(who)}</strong> (${e.role})
      <span style="margin:0 6px;color:#555">→</span>
      <span style="color:#6ab0f3">${escapeHtml(procShort)}</span>
      <span style="color:var(--text-muted);font-size:11px"> — eval by ${escapeHtml(by)}</span>
    </div>`;
  }).join('');

  return `
    <div class="ed-section">
      <h3>🕐 Recent Completed Evaluations</h3>
      <div class="ed-activity">${items}</div>
    </div>
  `;
}

// ─── Tab switching ───
function switchEdTab(tab) {
  document.querySelectorAll('.ed-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.ed-tab-content').forEach(t => t.classList.remove('active'));
  const tabIndex = { residents: 0, faculty: 1, procedures: 2, activity: 3 }[tab];
  document.querySelectorAll('.ed-tab')[tabIndex]?.classList.add('active');
  document.getElementById(`edTab${tab.charAt(0).toUpperCase() + tab.slice(1)}`)?.classList.add('active');
}

// ─── Utility ───
function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
