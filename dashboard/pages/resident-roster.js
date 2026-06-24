async function renderResidentRoster() {
  const content = document.getElementById('pageContent');
  
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">🩺 Resident Roster</div>
        <div class="page-subtitle">All urology residents — contact info, PGY level, rotation status</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderResidentRoster()">🔄 Refresh</button>
        <button class="btn btn-primary" onclick="exportRosterCSV()">📥 Export CSV</button>
      </div>
    </div>
    <div class="rr-controls">
      <input type="text" id="rrSearch" class="rr-search" placeholder="Search by name, PGY level, email..." oninput="filterRoster()">
      <select id="rrFilter" class="rr-filter" onchange="filterRoster()">
        <option value="all">All PGY Levels</option>
        <option value="PGY-1">PGY-1</option>
        <option value="PGY-2">PGY-2</option>
        <option value="PGY-3">PGY-3</option>
        <option value="PGY-4">PGY-4</option>
        <option value="PGY-5">PGY-5</option>
        <option value="Faculty">Faculty</option>
      </select>
    </div>
    <div id="rrStats" class="rr-stats"></div>
    <div id="rrTable" class="rr-table-wrap">
      <div class="loading"><div class="loading-spinner"></div><span>Loading roster...</span></div>
    </div>
    <style>
      .rr-controls { display: flex; gap: 8px; margin: 12px 0; }
      .rr-search { flex: 1; padding: 8px 12px; border: 1px solid var(--border); border-radius: 6px; background: #1a1a2e; color: #eee; font-size: 13px; }
      .rr-filter { padding: 8px 12px; border: 1px solid var(--border); border-radius: 6px; background: #1a1a2e; color: #eee; font-size: 13px; cursor: pointer; }
      .rr-table-wrap { background: var(--bg-card); border-radius: var(--radius-md); border: 1px solid var(--border); overflow: hidden; }
      .rr-table { width: 100%; border-collapse: collapse; font-size: 13px; }
      .rr-table th { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); font-weight: 600; font-size: 11px; text-transform: uppercase; color: var(--text-muted); background: rgba(255,255,255,0.02); }
      .rr-table td { padding: 8px 12px; border-bottom: 1px solid var(--border); }
      .rr-table tr:hover td { background: rgba(255,255,255,0.03); }
      .rr-pgy { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
      .rr-pgy.pgy1 { background: rgba(0,184,148,0.15); color: #00b894; }
      .rr-pgy.pgy2 { background: rgba(9,132,227,0.15); color: #0984e3; }
      .rr-pgy.pgy3 { background: rgba(253,203,110,0.15); color: #fdcb6e; }
      .rr-pgy.pgy4 { background: rgba(214,48,49,0.15); color: #d63031; }
      .rr-pgy.pgy5 { background: rgba(108,92,231,0.15); color: #6c5ce7; }
      .rr-pgy.faculty { background: rgba(162,155,254,0.15); color: #a29bfe; }
      .rr-stats { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
      .rr-stat { padding: 6px 14px; border-radius: 8px; background: var(--bg-card); border: 1px solid var(--border); font-size: 12px; }
      .rr-stat strong { font-size: 16px; }
    </style>
  `;

  await loadRoster();
}

const ROSTER_DATA = [
  { name: 'Kelli Aibel', pgy: 'PGY-3', email: 'kaibel@montefiore.org', phone: '(917) 555-0101', program: 'Urology', status: 'Active', evalStatus: 'Pending' },
  { name: 'J. Chen', pgy: 'PGY-2', email: 'jchen@montefiore.org', phone: '(917) 555-0102', program: 'Urology', status: 'Active', evalStatus: 'Complete' },
  { name: 'M. Patel', pgy: 'PGY-4', email: 'mpatel@montefiore.org', phone: '(917) 555-0103', program: 'Urology', status: 'Active', evalStatus: 'Pending' },
  { name: 'R. Garcia', pgy: 'PGY-1', email: 'rgarcia@montefiore.org', phone: '(917) 555-0104', program: 'Urology', status: 'Active', evalStatus: 'Complete' },
  { name: 'S. Kim', pgy: 'PGY-3', email: 'skim@montefiore.org', phone: '(917) 555-0105', program: 'Urology', status: 'Active', evalStatus: 'Overdue' },
  { name: 'A. Thompson', pgy: 'PGY-5', email: 'athompson@montefiore.org', phone: '(917) 555-0106', program: 'Urology', status: 'Active', evalStatus: 'Complete' },
  { name: 'L. Martinez', pgy: 'PGY-2', email: 'lmartinez@montefiore.org', phone: '(917) 555-0107', program: 'Urology', status: 'Active', evalStatus: 'Pending' },
  { name: 'D. Wilson', pgy: 'PGY-4', email: 'dwilson@montefiore.org', phone: '(917) 555-0108', program: 'Urology', status: 'Active', evalStatus: 'Complete' },
  { name: 'Dr. A. Smith', pgy: 'Faculty', email: 'asmith@montefiore.org', phone: '(718) 555-0201', program: 'Faculty', status: 'Active', evalStatus: '-' },
  { name: 'Dr. B. Johnson', pgy: 'Faculty', email: 'bjohnson@montefiore.org', phone: '(718) 555-0202', program: 'Faculty', status: 'Active', evalStatus: '-' },
];

async function loadRoster() {
  let residents = [...ROSTER_DATA];

  // Try loading from API if available
  try {
    const res = await fetch('/api/crm/contacts?category=resident');
    const data = await res.json();
    if (data.contacts && data.contacts.length > 0) {
      residents = data.contacts.map(c => ({
        name: c.name || c.first_name + ' ' + c.last_name,
        pgy: c.role || c.pgy || 'PGY-?',
        email: c.email || '-',
        phone: c.phone || '-',
        program: 'Urology',
        status: c.status || 'Active',
        evalStatus: c.eval_status || '-'
      }));
    }
  } catch {}

  renderRoster(residents);
}

function renderRoster(residents) {
  // Stats
  const counts = {};
  residents.forEach(r => { counts[r.pgy] = (counts[r.pgy] || 0) + 1; });
  const statHtml = Object.entries(counts).map(([pgy, count]) =>
    `<div class="rr-stat"><strong>${count}</strong> ${pgy}</div>`
  ).join('');
  statHtml += `<div class="rr-stat"><strong>${residents.length}</strong> Total</div>`;
  document.getElementById('rrStats').innerHTML = statHtml;

  // Table
  const tbody = residents.map(r => {
    const pgyClass = r.pgy.toLowerCase().replace('-', '');
    return `<tr>
      <td><strong>${escapeHtml(r.name)}</strong></td>
      <td><span class="rr-pgy ${pgyClass}">${escapeHtml(r.pgy)}</span></td>
      <td><a href="mailto:${escapeHtml(r.email)}" style="color:var(--link)">${escapeHtml(r.email)}</a></td>
      <td style="color:var(--text-muted);font-size:12px">${escapeHtml(r.phone)}</td>
      <td>${r.evalStatus !== '-' ? `<span class="eval-badge ${r.evalStatus.toLowerCase()}">${r.evalStatus}</span>` : '—'}</td>
    </tr>`;
  }).join('');

  document.getElementById('rrTable').innerHTML = `
    <table class="rr-table">
      <thead><tr><th>Name</th><th>Level</th><th>Email</th><th>Phone</th><th>Eval Status</th></tr></thead>
      <tbody>${tbody}</tbody>
    </table>
  `;
}

function filterRoster() {
  const q = (document.getElementById('rrSearch')?.value || '').toLowerCase();
  const pgyFilter = document.getElementById('rrFilter')?.value || 'all';
  
  let filtered = [...ROSTER_DATA];
  
  if (pgyFilter !== 'all') {
    filtered = filtered.filter(r => r.pgy === pgyFilter);
  }
  if (q) {
    filtered = filtered.filter(r => 
      r.name.toLowerCase().includes(q) ||
      r.pgy.toLowerCase().includes(q) ||
      r.email.toLowerCase().includes(q)
    );
  }
  
  renderRoster(filtered);
}

function exportRosterCSV() {
  const headers = ['Name', 'PGY Level', 'Email', 'Phone', 'Program', 'Status', 'Eval Status'];
  const rows = ROSTER_DATA.map(r => [
    r.name, r.pgy, r.email, r.phone, r.program, r.status, r.evalStatus
  ]);
  let csv = headers.join(',') + '\n' + rows.map(r => r.map(c => '"' + String(c).replace(/"/g,'""') + '"').join(',')).join('\n');
  const blob = new Blob([csv], {type: 'text/csv'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'Resident_Roster.csv'; a.click();
  URL.revokeObjectURL(url);
}
