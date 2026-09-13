async function renderDataGaps() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title"> Data Gaps</div>
        <div class="page-subtitle">CRM contacts missing information</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderDataGaps()"> Refresh</button>
      </div>
    </div>
    <div class="loading" id="gapsLoading"><div class="loading-spinner"></div><span>Analyzing CRM data...</span></div>
    <div id="gapsContent"></div>
    <style>
      .gap-card { background:var(--bg-card); border-radius:var(--radius-md); border:1px solid var(--border); padding:16px; margin-bottom:12px; }
      .gap-card h3 { font-size:13px; font-weight:600; margin-bottom:8px; display:flex; align-items:center; gap:6px; }
      .gap-tag { display:inline-block; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:600; margin:2px; }
      .gap-tag.missing { background:rgba(214,48,49,0.15); color:#d63031; }
      .gap-tag.ok { background:rgba(0,184,148,0.15); color:#00b894; }
      .gap-table { width:100%; border-collapse:collapse; }
      .gap-table th { text-align:left; padding:8px 12px; font-size:11px; color:#888; border-bottom:1px solid #2a2a3a; text-transform:uppercase; }
      .gap-table td { padding:8px 12px; font-size:12px; border-bottom:1px solid rgba(255,255,255,0.04); }
      .gap-summary { display:flex; gap:12px; flex-wrap:wrap; margin-bottom:16px; }
      .gap-stat { flex:1; min-width:100px; background:#232340; border-radius:8px; padding:12px; text-align:center; border:1px solid #2a2a3a; }
      .gap-stat div:first-child { font-size:24px; font-weight:700; }
      .gap-stat div:last-child { font-size:11px; color:#888; margin-top:4px; }
    </style>
  `;

  try {
    const res = await fetch('/api/crm-data-gaps').then(r => r.json());
    renderGaps(res);
  } catch(e) {
    // Fallback: parse directly from stored CRM
    renderGapsFallback();
  }
}

function renderGapsFallback() {
  document.getElementById('gapsLoading').style.display = 'none';
  document.getElementById('gapsContent').innerHTML = '<div class="gap-card" style="text-align:center;padding:32px;color:#888"> API not available. Load CRM data first.</div>';
}

function renderGaps(data) {
  document.getElementById('gapsLoading').style.display = 'none';
  
  const byCategory = data.by_category || {};
  const stats = data.stats || {};
  const total = stats.total || 0;
  const withGaps = stats.with_gaps || 0;
  const fields = stats.by_field || [];

  let summaryHtml = `
    <div class="gap-summary">
      <div class="gap-stat"><div>${total}</div><div>Total Contacts</div></div>
      <div class="gap-stat" style="border-color:${withGaps > 0 ? 'rgba(214,48,49,0.3)' : 'rgba(0,184,148,0.3)'}"><div>${withGaps}</div><div>Missing Data</div></div>
      <div class="gap-stat"><div>${total - withGaps}</div><div>Complete</div></div>
    </div>`;

  let fieldsHtml = '<div class="gap-card"><h3> Most Missing Fields</h3>';
  for (const f of fields) {
    const pct = Math.round((f.count / total) * 100);
    fieldsHtml += `<div style="display:flex;align-items:center;gap:8px;padding:4px 0;font-size:12px">
      <span style="min-width:130px">${f.field}</span>
      <div style="flex:1;height:6px;background:rgba(255,255,255,0.06);border-radius:3px">
        <div style="height:100%;width:${pct}%;background:${pct > 50 ? '#d63031' : pct > 20 ? '#fdcb6e' : '#00b894'};border-radius:3px"></div>
      </div>
      <span style="min-width:60px;text-align:right;color:#888">${f.count}/${total}</span>
    </div>`;
  }
  fieldsHtml += '</div>';

  // By category
  let catHtml = '';
  for (const [cat, contacts] of Object.entries(byCategory)) {
    if (contacts.length === 0) continue;
    catHtml += `<div class="gap-card"><h3>${cat}</h3><table class="gap-table">
      <tr><th>Name</th><th>Missing Fields</th><th>EZID</th><th>Email</th></tr>`;
    for (const c of contacts) {
      const missing = (c.dataGaps || []).map(g => `<span class="gap-tag missing">${g}</span>`).join(' ');
      catHtml += `<tr>
        <td>${c.firstName || ''} ${c.lastName || ''}</td>
        <td>${missing || '<span class="gap-tag ok">complete</span>'}</td>
        <td style="color:${c.ezId ? '#e0e0e0' : '#888'}">${c.ezId || '—'}</td>
        <td style="color:${c.email ? '#e0e0e0' : '#888'}">${c.email || '—'}</td>
      </tr>`;
    }
    catHtml += '</table></div>';
  }

  document.getElementById('gapsContent').innerHTML = summaryHtml + fieldsHtml + catHtml;
}

// Expose for routing
window.renderDataGaps = renderDataGaps;
