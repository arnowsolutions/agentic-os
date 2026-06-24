async function renderCrmAudit() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">🔍 CRM Audit</h1>
        <p class="page-subtitle">Access log for all CRM operations — read, write, add, delete</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="renderCrmAudit()">🔄 Refresh</button>
        <button class="btn btn-danger" onclick="confirmClearAccessLog()">🗑 Clear Log</button>
      </div>
    </div>
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px">
      <div style="flex:1;min-width:200px">
        <input type="text" id="auditSearch" placeholder="🔍 Search by contact name..." 
               style="width:100%;padding:10px 14px;border:1px solid var(--border);border-radius:8px;
                      background:var(--surface);color:var(--text);font-size:14px"
               oninput="filterAuditLog()">
      </div>
      <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center" id="auditActionFilters">
        <span style="font-size:13px;color:var(--text-muted);margin-right:4px">Action:</span>
        <button class="tag audit-filter-btn active-filter" data-action="" onclick="setAuditFilter(this,'')">All</button>
        <button class="tag audit-filter-btn" data-action="read" onclick="setAuditFilter(this,'read')">📖 Read</button>
        <button class="tag audit-filter-btn" data-action="write" onclick="setAuditFilter(this,'write')">✏️ Write</button>
        <button class="tag audit-filter-btn" data-action="add" onclick="setAuditFilter(this,'add')">➕ Add</button>
        <button class="tag audit-filter-btn" data-action="delete" onclick="setAuditFilter(this,'delete')">🗑 Delete</button>
      </div>
    </div>
    <div id="auditLogContainer">
      <div class="loading"><div class="loading-spinner"></div><span>Loading audit log...</span></div>
    </div>
  `;
  await loadAuditLog();
}

let allAuditEntries = [];

async function loadAuditLog() {
  try {
    const data = await api.get('/api/crm/access-log');
    allAuditEntries = data.entries || [];
    renderAuditTable(allAuditEntries);
  } catch (err) {
    document.getElementById('auditLogContainer').innerHTML = 
      `<div class="empty-state"><div class="empty-state-icon">⚠</div><div class="empty-state-title">Error loading audit log</div><div class="empty-state-desc">${escapeHtml(err.message)}</div></div>`;
  }
}

function setAuditFilter(el, action) {
  document.querySelectorAll('.audit-filter-btn').forEach(b => b.classList.remove('active-filter'));
  el.classList.add('active-filter');
  el.dataset.action = action;
  filterAuditLog();
}

function filterAuditLog() {
  const q = (document.getElementById('auditSearch').value || '').toLowerCase();
  const activeAction = document.querySelector('.audit-filter-btn.active-filter')?.dataset?.action || '';
  
  let filtered = allAuditEntries;
  if (activeAction) {
    filtered = filtered.filter(e => e.action === activeAction);
  }
  if (q) {
    filtered = filtered.filter(e => 
      (e.contact_name || '').toLowerCase().includes(q) ||
      (e.contact_id || '').toLowerCase().includes(q)
    );
  }
  renderAuditTable(filtered);
}

function renderAuditTable(entries) {
  const container = document.getElementById('auditLogContainer');
  if (!entries.length) {
    container.innerHTML = '<div class="empty-state" style="padding:40px"><div class="empty-state-title">No entries found</div><div class="empty-state-desc">CRM access log is empty or filter returned no results</div></div>';
    return;
  }
  
  const actionIcons = { read: '📖', write: '✏️', add: '➕', delete: '🗑' };
  const actionColors = { read: '#0984e3', write: '#fdcb6e', add: '#00b894', delete: '#e17055' };
  
  let html = `<div style="font-size:12px;color:var(--text-muted);margin-bottom:8px">${entries.length} entr${entries.length!==1?'ies':'y'}</div>
    <div style="overflow-x:auto">
    <table style="width:100%;border-collapse:collapse;font-size:13px">
      <thead>
        <tr style="border-bottom:1px solid var(--border);color:var(--text-muted);font-size:11px;text-transform:uppercase;letter-spacing:0.5px">
          <th style="padding:8px 10px;text-align:left">Time</th>
          <th style="padding:8px 10px;text-align:left">Action</th>
          <th style="padding:8px 10px;text-align:left">Contact</th>
          <th style="padding:8px 10px;text-align:left">Endpoint</th>
          <th style="padding:8px 10px;text-align:left">Method</th>
          <th style="padding:8px 10px;text-align:left">Source</th>
        </tr>
      </thead>
      <tbody>`;
  
  entries.forEach(e => {
    const icon = actionIcons[e.action] || '❓';
    const color = actionColors[e.action] || '#636e72';
    const ts = e.datetime ? formatDate(e.datetime) : (e.timestamp ? new Date(e.timestamp * 1000).toLocaleString() : '-');
    const name = escapeHtml(e.contact_name || '-');
    const endpoint = escapeHtml(e.endpoint || '-');
    const method = escapeHtml(e.method || '-');
    const agent = escapeHtml(e.agent || '-');
    
    html += `
      <tr style="border-bottom:1px solid var(--border-light, rgba(255,255,255,0.05))">
        <td style="padding:8px 10px;white-space:nowrap;font-size:12px;color:var(--text-muted)">${ts}</td>
        <td style="padding:8px 10px"><span style="color:${color};font-weight:600">${icon} ${e.action}</span></td>
        <td style="padding:8px 10px;font-weight:500">${name}</td>
        <td style="padding:8px 10px;font-size:12px;color:var(--text-muted);font-family:monospace">${endpoint}</td>
        <td style="padding:8px 10px"><span class="tag" style="font-size:10px">${method}</span></td>
        <td style="padding:8px 10px;font-size:12px;color:var(--text-muted)">${agent}</td>
      </tr>`;
  });
  
  html += '</tbody></table></div>';
  container.innerHTML = html;
}

function confirmClearAccessLog() {
  if (!confirm('Are you sure you want to clear the entire CRM access log? This cannot be undone.')) return;
  clearAccessLog();
}

async function clearAccessLog() {
  try {
    await api.post('/api/crm/access-log/clear?confirm=true', {});
    showToast('Access log cleared', 'success');
    allAuditEntries = [];
    renderAuditTable([]);
  } catch (err) {
    showToast(`Failed to clear log: ${err.message}`, 'error');
  }
}
