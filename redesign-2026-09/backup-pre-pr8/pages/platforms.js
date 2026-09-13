async function renderPlatforms() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <style>
      .pages-platforms .pf-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(340px,1fr)); gap:16px; }
      .pages-platforms .pf-card { background:var(--bg-card); border:1px solid var(--border); border-radius:14px; overflow:hidden; transition:box-shadow .2s, transform .15s; cursor:pointer; }
      .pages-platforms .pf-card:hover { box-shadow:0 8px 24px rgba(0,0,0,.15); transform:translateY(-2px); }
      .pages-platforms .pf-header { padding:16px 18px; display:flex; align-items:center; gap:12px; border-bottom:1px solid var(--border-dim); }
      .pages-platforms .pf-icon { font-size:28px; width:44px; height:44px; border-radius:12px; display:flex; align-items:center; justify-content:center; }
      .pages-platforms .pf-title { font-size:16px; font-weight:700; color:var(--text); }
      .pages-platforms .pf-subtitle { font-size:11px; color:var(--text-dim); margin-top:1px; }
      .pages-platforms .pf-body { padding:12px 18px 16px; min-height:120px; }
      .pages-platforms .pf-item { display:flex; justify-content:space-between; align-items:center; padding:6px 0; border-bottom:1px solid var(--border-dim); font-size:12px; }
      .pages-platforms .pf-item:last-child { border-bottom:none; }
      .pages-platforms .pf-item-name { color:var(--text); font-weight:500; }
      .pages-platforms .pf-item-meta { color:var(--text-dim); font-size:11px; }
      .pages-platforms .pf-item-empty { color:var(--text-dim); font-size:12px; text-align:center; padding:20px 0; }
      .pages-platforms .pf-footer { padding:8px 18px 14px; border-top:1px solid var(--border-dim); text-align:center; }
      .pages-platforms .pf-btn { background:var(--bg); border:1px solid var(--border); border-radius:8px; padding:6px 16px; font-size:12px; font-weight:600; color:var(--text); cursor:pointer; transition:background .15s; }
      .pages-platforms .pf-btn:hover { background:var(--accent-bg); border-color:var(--accent); color:var(--accent); }
    </style>
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">🔌 Platform Connections</h1>
        <p class="page-subtitle">Connected systems — top 10 items from each platform</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="renderPlatforms()">🔄 Refresh All</button>
      </div>
    </div>
    <div class="pages-platforms pf-grid" id="platformGrid">
      ${buildCard('scl', '🤒', '#fef2f2', 'Sick Call Line', 'Staff absence & coverage management', '/scl')}
      ${buildCard('reimbursement', '💰', '#f0fdf4', 'Reimbursement', 'GME & expense tracking', '/reimbursement')}
      ${buildCard('qgenda', '📅', '#eff6ff', 'Qgenda Scheduler', 'OR schedule, swaps & resident assignments', '/qgenda')}
    </div>
  `;

  loadSclTop10();
  loadReimbursementTop10();
  loadQgendaTop10();
}

function buildCard(id, icon, color, title, desc, link) {
  return `
    <div class="pf-card">
      <div class="pf-header">
        <div class="pf-icon" style="background:${color}">${icon}</div>
        <div>
          <div class="pf-title">${title}</div>
          <div class="pf-subtitle">${desc}</div>
        </div>
      </div>
      <div class="pf-body" id="body-${id}">
        <div style="text-align:center;padding:20px;color:var(--text-dim);font-size:13px"><div class="loading-spinner" style="margin:0 auto 8px"></div>Loading...</div>
      </div>
      <div class="pf-footer">
        <button class="pf-btn" onclick="window.open('${link}','_blank')">Open ${title} →</button>
      </div>
    </div>`;
}

async function fetchJson(url) {
  try {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.json();
  } catch (e) {
    return { error: e.message };
  }
}

async function loadSclTop10() {
  const body = document.getElementById('body-scl');
  const data = await fetchJson('/api/crm/contacts');
  if (data.error) { body.innerHTML = `<div class="pf-item-empty">⚠️ ${escapeHtml(data.error)}</div>`; return; }

  const contacts = Array.isArray(data) ? data : (data.contacts || []);
  const byCat = {};
  contacts.forEach(c => {
    const cat = c.category || 'Other';
    if (!byCat[cat]) byCat[cat] = [];
    if (byCat[cat].length < 4) byCat[cat].push(c);
  });

  const cats = Object.keys(byCat).slice(0, 3);
  if (cats.length === 0) { body.innerHTML = '<div class="pf-item-empty">No contacts loaded</div>'; return; }

  body.innerHTML = cats.map(cat => byCat[cat].map(c =>
    `<div class="pf-item">
      <span class="pf-item-name">${escapeHtml(c.firstName||'')} ${escapeHtml(c.lastName||'')}</span>
      <span class="pf-item-meta">${cat}${c.ezId ? ' · ' + escapeHtml(c.ezId) : ''}</span>
    </div>`
  ).join('')).join('');
}

async function loadReimbursementTop10() {
  const body = document.getElementById('body-reimbursement');
  const data = await fetchJson('/api/admin/audit-log?limit=10');
  if (!data.error && data.length > 0) {
    body.innerHTML = data.slice(0, 10).map(e =>
      `<div class="pf-item">
        <span class="pf-item-name">${escapeHtml(e.actor_name||'System')}</span>
        <span class="pf-item-meta">${escapeHtml(e.action.replace(/_/g,' '))}${e.person_name ? ' — ' + escapeHtml(e.person_name) : ''}</span>
      </div>`
    ).join('');
    return;
  }

  // Fallback: show residents
  const r2 = await fetchJson('/api/reimbursement/residents');
  if (r2.error) { body.innerHTML = `<div class="pf-item-empty">${escapeHtml(r2.error)}</div>`; return; }
  const residents = Array.isArray(r2) ? r2 : (r2.residents || r2.persons || []);
  body.innerHTML = residents.slice(0, 10).map(r =>
    `<div class="pf-item">
      <span class="pf-item-name">${escapeHtml(r.name||'')}</span>
      <span class="pf-item-meta">${r.cls||''}${r.email ? ' · ' + escapeHtml(r.email) : ''}</span>
    </div>`
  ).join('') || '<div class="pf-item-empty">No data</div>';
}

async function loadQgendaTop10() {
  const body = document.getElementById('body-qgenda');
  const data = await fetchJson('/api/qgenda/users?limit=10');
  if (data.error) { body.innerHTML = `<div class="pf-item-empty">⚠️ ${escapeHtml(data.error)}</div>`; return; }
  body.innerHTML = (Array.isArray(data) ? data : []).map(u =>
    `<div class="pf-item">
      <span class="pf-item-name">${escapeHtml(u.name||'')}</span>
      <span class="pf-item-meta">${u.role||''}${u.email ? ' · ' + escapeHtml(u.email) : ''}</span>
    </div>`
  ).join('') || '<div class="pf-item-empty">No users loaded</div>';
}
