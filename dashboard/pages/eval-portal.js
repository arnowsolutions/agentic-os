async function renderEvalPortal(target) {
  const content = target || document.getElementById('suitePane') || document.getElementById('pageContent');
  
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">Eval Portal</div>
        <div class="page-subtitle">CMS evaluation forms — track completion, send reminders</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderEvalPortal()">↻ Refresh</button>
        <button class="btn btn-primary" onclick="sendEvalReminders()">Send Reminders</button>
      </div>
    </div>
    <div class="eval-summary" id="evalSummary">
      <div class="loading"><div class="loading-spinner"></div><span>Loading evaluation data...</span></div>
    </div>
    <div class="eval-tables" id="evalTables" style="margin-top:16px;display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <div class="eval-section">
        <h3 style="font-size:14px;font-weight:600;margin-bottom:8px">Faculty Evaluations</h3>
        <div id="evalFaculty"><div class="loading"><div class="loading-spinner"></div></div></div>
      </div>
      <div class="eval-section">
        <h3 style="font-size:14px;font-weight:600;margin-bottom:8px">Resident Evaluations</h3>
        <div id="evalResidents"><div class="loading"><div class="loading-spinner"></div></div></div>
      </div>
    </div>
    <style>
      .eval-section {
        background: var(--bg-card); border-radius: var(--radius-md); border: 1px solid var(--border);
        padding: 16px;
      }
      .eval-summary {
        background: var(--bg-card); border-radius: var(--radius-md); border: 1px solid var(--border);
        padding: 20px;
      }
      .eval-stat-row { display: flex; gap: 16px; flex-wrap: wrap; }
      .eval-stat {
        flex: 1; min-width: 120px; text-align: center; padding: 12px;
        background: var(--hover-bg); border-radius: var(--radius-sm);
      }
      .eval-stat .num { font-size: 28px; font-weight: 700; }
      .eval-stat .label { font-size: 11px; text-transform: uppercase; color: var(--text-muted); margin-top: 2px; }
      .eval-stat .num.green { color: #00b894; }
      .eval-stat .num.yellow { color: #fdcb6e; }
      .eval-stat .num.red { color: #d63031; }
      .eval-stat .num.blue { color: #0984e3; }
      .eval-table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 8px; }
      .eval-table th { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--border); font-weight: 600; font-size: 11px; text-transform: uppercase; color: var(--text-muted); }
      .eval-table td { padding: 6px 8px; border-bottom: 1px solid var(--border); }
      .eval-table tr:hover td { background: var(--hover-bg); }
      .eval-badge { padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 600; }
      .eval-badge.done { background: rgba(0,184,148,0.15); color: #00b894; }
      .eval-badge.pending { background: rgba(253,203,110,0.15); color: #fdcb6e; }
      .eval-badge.overdue { background: rgba(214,48,49,0.15); color: #d63031; }
    </style>
  `;

  try {
    // Try to fetch from portal API, fall back to demo data
    let faculty = [];
    let residents = [];
    
    try {
      const res = await fetch('/api/eval/forms');
      const data = await res.json();
      stampPage(data);
      faculty = data.faculty || [];
      residents = data.residents || [];
    } catch {
      faculty = [];
      residents = [];
    }
    if (!faculty.length && !residents.length) {
      document.getElementById('evalSummary').innerHTML =
        '<div class="empty-state"><div class="empty-state-icon">!</div><div class="empty-state-title">No eval forms loaded</div><div class="empty-state-desc">The eval forms file has no entries. Run the eval sync, then refresh.</div></div>';
    }

    const all = [...faculty, ...residents];
    const done = all.filter(f => f.status === 'done').length;
    const pending = all.filter(f => f.status === 'pending').length;
    const overdue = all.filter(f => f.status === 'overdue').length;

    document.getElementById('evalSummary').innerHTML = `
      <div class="eval-stat-row">
        <div class="eval-stat">
          <div class="num blue">${all.length}</div>
          <div class="label">Total Forms</div>
        </div>
        <div class="eval-stat">
          <div class="num green">${done}</div>
          <div class="label">Completed</div>
        </div>
        <div class="eval-stat">
          <div class="num yellow">${pending}</div>
          <div class="label">Pending</div>
        </div>
        <div class="eval-stat">
          <div class="num red">${overdue}</div>
          <div class="label">Overdue</div>
        </div>
        <div class="eval-stat">
          <div class="num ${all.length ? (done/all.length >= 0.8 ? 'green' : done/all.length >= 0.5 ? 'yellow' : 'red') : ''}">
            ${all.length ? Math.round(done/all.length * 100) : 0}%
          </div>
          <div class="label">Completion Rate</div>
        </div>
      </div>
    `;

    const renderTable = (data) => `
      <table class="eval-table">
        <thead><tr><th>Name</th><th>Form</th><th>Status</th><th>Date</th></tr></thead>
        <tbody>
          ${data.map(f => `
            <tr>
              <td><strong>${escapeHtml(f.name)}</strong></td>
              <td style="color:var(--text-muted)">${escapeHtml(f.form)}</td>
              <td><span class="eval-badge ${f.status}">${f.status}</span></td>
              <td style="font-size:11px;color:var(--text-muted)">${f.date}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;

    document.getElementById('evalFaculty').innerHTML = faculty.length ? renderTable(faculty) : '<div style="padding:12px;text-align:center;color:var(--text-muted);font-size:13px">No faculty evaluations found</div>';
    document.getElementById('evalResidents').innerHTML = residents.length ? renderTable(residents) : '<div style="padding:12px;text-align:center;color:var(--text-muted);font-size:13px">No resident evaluations found</div>';
  } catch (err) {
    document.getElementById('evalSummary').innerHTML = `
      <div style="text-align:center;padding:20px">
        <div style="font-size:24px;margin-bottom:8px">!</div>
        <div style="color:var(--text-muted)">Could not load evaluation data</div>
      </div>
    `;
  }
}

async function sendEvalReminders() {
  try {
    showToast('Sending evaluation reminders...', 'info');
    const res = await fetch('/api/eval/send-reminders', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast(`Reminders sent to ${data.count || 0} evaluators`, 'success');
    } else {
      showToast('Failed to send reminders', 'error');
    }
  } catch (err) {
    showToast('Error: ' + err.message, 'error');
  }
}
