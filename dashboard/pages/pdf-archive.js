async function renderPdfArchive() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">PDF Archive</div>
        <div class="page-subtitle">All generated PDFs — call schedules, GME reports, attendance records</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderPdfArchive()">↻ Refresh</button>
      </div>
    </div>
    <div id="paGrid" class="pa-grid"><div class="loading"><div class="loading-spinner"></div></div></div>
    <style>
      .pa-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:12px; margin-top:16px; }
      .pa-card { background:var(--bg-card); border-radius:var(--radius-md); border:1px solid var(--border); padding:16px; }
      .pa-card .icon { font-size:28px; margin-bottom:8px; }
      .pa-card .name { font-size:13px; font-weight:600; }
      .pa-card .meta { font-size:11px; color:var(--text-muted); margin-top:4px; }
      .pa-card .actions { margin-top:10px; display:flex; gap:6px; }
      .pa-empty { grid-column:1/-1; text-align:center; padding:32px; color:var(--text-muted); font-size:13px; }
    </style>
  `;
  try {
    const res = await fetch('/api/pdf-archive').then(r => r.json()).catch(() => ({}));
    stampPage(res);
    const pdfs = res.pdfs || [];
    const data = pdfs;
    const grid = document.getElementById('paGrid');

    if (data.length === 0) {
      grid.innerHTML = '<div class="pa-empty">No PDFs generated yet</div>';
      return;
    }

    grid.innerHTML = data.map(p => `
      <div class="pa-card">
        <div class="icon">${p.icon || ''}</div>
        <div class="name">${escapeHtml(p.name)}</div>
        <div class="meta">${p.date || ''} ${p.size ? '· ' + p.size : ''}</div>
        <div class="actions">
          <button class="btn btn-sm btn-primary" onclick="showToast('Download started','info')">↓ Download</button>
          <button class="btn btn-sm btn-ghost" onclick="showToast('Re-emailing PDF','info')">Re-email</button>
        </div>
      </div>
    `).join('');
  } catch(e) {
    document.getElementById('paGrid').innerHTML = `<div class="pa-empty">! ${escapeHtml(e.message)}</div>`;
  }
}
