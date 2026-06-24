async function renderGmeDetail() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">📈 GME Deep Dive</div>
        <div class="page-subtitle">Resident education fund tracking — $1,250/resident/AY breakdown</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderGmeDetail()">🔄 Refresh</button>
      </div>
    </div>
    <div id="gdSummary" class="gd-summary"><div class="loading"><div class="loading-spinner"></div></div></div>
    <div id="gdChart" class="gd-chart" style="margin-top:12px;display:none">
      <div style="background:var(--bg-card);border-radius:var(--radius-md);border:1px solid var(--border);padding:16px">
        <h3 style="font-size:13px;font-weight:600;margin-bottom:12px">💰 Resident Fund Usage</h3>
        <canvas id="gmeChart" height="250"></canvas>
      </div>
    </div>
    <div id="gdTable" style="margin-top:12px"><div class="loading"><div class="loading-spinner"></div></div></div>
    <style>
      .gd-summary { display:grid; grid-template-columns:repeat(auto-fill,minmax(160px,1fr)); gap:10px; }
      .gd-stat { background:var(--bg-card); border-radius:var(--radius-md); border:1px solid var(--border); padding:14px; text-align:center; }
      .gd-stat .num { font-size:20px; font-weight:700; }
      .gd-stat .label { font-size:10px; text-transform:uppercase; color:var(--text-muted); margin-top:4px; }
      .gd-table { width:100%; border-collapse:collapse; font-size:12px; }
      .gd-table th { text-align:left; padding:8px 10px; border-bottom:1px solid var(--border); font-weight:600; font-size:11px; text-transform:uppercase; color:var(--text-muted); }
      .gd-table td { padding:8px 10px; border-bottom:1px solid rgba(255,255,255,0.04); }
      .gd-table tr:hover td { background:rgba(255,255,255,0.02); }
      .gd-bar { height:6px; border-radius:3px; background:rgba(255,255,255,0.06); overflow:hidden; width:100px; display:inline-block; vertical-align:middle; }
      .gd-bar .fill { height:100%; border-radius:3px; }
    </style>
  `;
  try {
    const res = await fetch('/api/gme/detail').then(r => r.json()).catch(() => ({}));
    const residents = res.residents || [
      {name:'Kelli Aibel', pgy:'PGY-3', used:850, categories:{books:300, conferences:400, boards:100, other:50}},
      {name:'J. Chen', pgy:'PGY-2', used:420, categories:{books:150, conferences:200, boards:0, other:70}},
      {name:'M. Patel', pgy:'PGY-4', used:1150, categories:{books:200, conferences:600, boards:300, other:50}},
      {name:'R. Garcia', pgy:'PGY-1', used:180, categories:{books:100, conferences:50, boards:0, other:30}},
      {name:'S. Kim', pgy:'PGY-3', used:680, categories:{books:250, conferences:300, boards:80, other:50}},
      {name:'A. Rivera', pgy:'PGY-2', used:550, categories:{books:180, conferences:250, boards:50, other:70}},
      {name:'T. Nguyen', pgy:'PGY-4', used:980, categories:{books:300, conferences:500, boards:120, other:60}},
      {name:'L. Patel', pgy:'PGY-1', used:220, categories:{books:120, conferences:50, boards:0, other:50}},
    ];
    const ANNUAL_BUDGET = 1250;
    const totalBudget = residents.length * ANNUAL_BUDGET;
    const totalUsed = residents.reduce((s,r) => s + r.used, 0);
    const remaining = totalBudget - totalUsed;

    const barColor = p => p >= 80 ? '#d63031' : p >= 50 ? '#fdcb6e' : '#00b894';

    document.getElementById('gdSummary').innerHTML = `
      <div class="gd-stat"><div class="num" style="color:#0984e3">${residents.length}</div><div class="label">Residents</div></div>
      <div class="gd-stat"><div class="num" style="color:#00b894">$${totalBudget.toLocaleString()}</div><div class="label">Total Budget</div></div>
      <div class="gd-stat"><div class="num" style="color:#fdcb6e">$${totalUsed.toLocaleString()}</div><div class="label">Total Used</div></div>
      <div class="gd-stat"><div class="num" style="color:#0984e3">$${remaining.toLocaleString()}</div><div class="label">Remaining</div></div>
      <div class="gd-stat"><div class="num" style="color:${barColor(Math.round(totalUsed/totalBudget*100))}">${Math.round(totalUsed/totalBudget*100)}%</div><div class="label">Usage Rate</div></div>
    `;

    document.getElementById('gdTable').innerHTML = `
      <div style="background:var(--bg-card);border-radius:var(--radius-md);border:1px solid var(--border);padding:16px">
        <h3 style="font-size:13px;font-weight:600;margin-bottom:12px">🩺 Per-Resident Breakdown</h3>
        <div style="overflow-x:auto">
          <table class="gd-table">
            <thead><tr><th>Resident</th><th>PGY</th><th>Used</th><th>Remaining</th><th>Usage</th><th>Books</th><th>Conferences</th><th>Boards</th><th>Other</th></tr></thead>
            <tbody>
              ${residents.map(r => {
                const pct = Math.round(r.used / ANNUAL_BUDGET * 100);
                const cats = r.categories || {};
                return `<tr>
                  <td><strong>${escapeHtml(r.name)}</strong></td>
                  <td>${r.pgy || '—'}</td>
                  <td>$${r.used.toLocaleString()}</td>
                  <td>$${(ANNUAL_BUDGET - r.used).toLocaleString()}</td>
                  <td><div class="gd-bar"><div class="fill" style="width:${pct}%;background:${barColor(pct)}"></div></div> ${pct}%</td>
                  <td>$${(cats.books||0).toLocaleString()}</td>
                  <td>$${(cats.conferences||0).toLocaleString()}</td>
                  <td>$${(cats.boards||0).toLocaleString()}</td>
                  <td>$${(cats.other||0).toLocaleString()}</td>
                </tr>`;
              }).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch(e) {
    document.getElementById('gdSummary').innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:20px;color:var(--text-muted)">⚠️ ${escapeHtml(e.message)}</div>`;
    document.getElementById('gdTable').innerHTML = '';
  }
}
