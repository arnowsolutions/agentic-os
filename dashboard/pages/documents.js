async function renderDocuments() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">Documents</div>
        <div class="page-subtitle">Reviews &amp; audits · social media plans · campaign hubs — every deliverable in one place</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderDocuments()">↻ Refresh</button>
      </div>
    </div>
    <div id="docTabs" class="doc-tabs"></div>
    <div id="docGrid" class="doc-grid"><div class="loading"><div class="loading-spinner"></div></div></div>
    <style>
      .doc-tabs { display:flex; flex-wrap:wrap; gap:8px; margin:16px 0 4px; }
      .doc-tab { padding:6px 14px; border-radius:18px; font-size:12px; font-weight:600; cursor:pointer;
                 border:1px solid var(--border); background:var(--bg-card); color:var(--text-muted); }
      .doc-tab.active { background:var(--accent); border-color:var(--accent); color:#fff; }
      .doc-group-label { font-size:12px; color:var(--text-muted); text-transform:uppercase; letter-spacing:.5px; margin:18px 0 8px; font-weight:600; }
      .doc-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:12px; margin-top:10px; }
      .doc-card { background:var(--bg-card); border-radius:var(--radius-md); border:1px solid var(--border); padding:16px; display:flex; flex-direction:column; }
      .doc-card .cat { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.5px; }
      .doc-card .name { font-size:14px; font-weight:600; margin-top:6px; line-height:1.35; }
      .doc-card .desc { font-size:12px; color:var(--text-muted); margin-top:6px; flex:1; }
      .doc-card .meta { font-size:11px; color:var(--text-muted); margin-top:8px; }
      .doc-card .actions { margin-top:10px; display:flex; gap:6px; }
      .doc-live { color:var(--ok, #16a34a); }
      .doc-local { color:var(--warn, #d97706); }
      .doc-empty { grid-column:1/-1; text-align:center; padding:32px; color:var(--text-muted); font-size:13px; }
    </style>
  `;
  try {
    const raw = await fetch('/api/documents').then(r => r.json()).catch(() => ({}));
    const docs = Array.isArray(raw) ? raw : (raw.documents || []);

    const CATS = [
      { id: 'all',               label: 'All documents' },
      { id: 'reviews-audits',    label: 'Reviews & Audits' },
      { id: 'social-media-plans',label: 'Social Media Plans' },
      { id: 'campaign-hubs',     label: 'Campaign Hubs' },
    ];
    const catColors = { 'reviews-audits':'#7c3aed', 'social-media-plans':'#e1306c', 'campaign-hubs':'#0a66c2' };
    const catNames  = { 'reviews-audits':'Review / Audit', 'social-media-plans':'Social Media Plan', 'campaign-hubs':'Campaign Hub' };

    let activeCat = localStorage.getItem('docs-cat') || 'all';

    function draw() {
      const tabsHtml = CATS.map(c => {
        const count = c.id === 'all' ? docs.length : docs.filter(d => d.category === c.id).length;
        return `<div class="doc-tab ${activeCat === c.id ? 'active' : ''}" onclick="setDocCat('${c.id}')">${c.label} (${count})</div>`;
      }).join('');
      document.getElementById('docTabs').innerHTML = tabsHtml;

      const list = activeCat === 'all' ? docs : docs.filter(d => d.category === activeCat);
      const grid = document.getElementById('docGrid');
      if (!list.length) {
        grid.innerHTML = `<div class="doc-empty">No documents in this category yet</div>`;
        return;
      }
      grid.innerHTML = list.map(d => {
        const color = catColors[d.category] || '#6b7280';
        const isLocal = !d.url;
        return `
          <div class="doc-card">
            <div class="cat" style="color:${color}">${catNames[d.category] || d.category}</div>
            <div class="name">${escapeHtml(d.title)}</div>
            <div class="desc">${escapeHtml(d.description || '')}</div>
            <div class="meta">${d.added || ''} · ${isLocal ? '<span class="doc-local">local file</span>' : '<span class="doc-live">● live link</span>'}</div>
            <div class="actions">
              ${isLocal
                ? `<button class="btn btn-sm btn-primary" onclick="showToast('Open from workspace: ${escapeHtml(d.source || '')}','info')">📄 Workspace file</button>`
                : `<a class="btn btn-sm btn-primary" href="${d.url}" target="_blank" rel="noopener">🔗 Open</a>`}
            </div>
          </div>`;
      }).join('');
    }

    window.setDocCat = (id) => { activeCat = id; localStorage.setItem('docs-cat', id); draw(); };
    draw();
  } catch(e) {
    document.getElementById('docGrid').innerHTML = `<div class="doc-empty">⚠ ${escapeHtml(e.message)}</div>`;
  }
}
