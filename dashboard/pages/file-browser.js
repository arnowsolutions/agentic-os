async function renderFileBrowser() {
  const content = document.getElementById('pageContent');
  let currentPath = '/workspace';

  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">🗂 File Browser</div>
        <div class="page-subtitle">Browse and view files in <span id="fbCurrentPath">${currentPath}</span></div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderFileBrowser()">🔄 Reset</button>
      </div>
    </div>
    <div class="fb-bar">
      <button class="btn btn-ghost btn-sm" onclick="fbGoUp()" id="fbUpBtn" disabled>⬆ Up</button>
      <input type="text" id="fbPathInput" class="fb-path-input" value="${currentPath}" onkeydown="if(event.key==='Enter')fbGoTo(this.value)">
      <button class="btn btn-sm btn-primary" onclick="fbGoTo(document.getElementById('fbPathInput').value)">Go</button>
    </div>
    <div id="fbContent" class="fb-content"><div class="loading"><div class="loading-spinner"></div><span>Loading...</span></div></div>
    <div id="fbPreview" class="fb-preview" style="display:none">
      <div class="fb-preview-header">
        <span id="fbPreviewName" style="font-weight:600;font-size:13px"></span>
        <button class="btn btn-ghost btn-sm" onclick="document.getElementById('fbPreview').style.display='none'">✕</button>
      </div>
      <pre id="fbPreviewBody" style="padding:12px;font-size:11px;overflow:auto;max-height:400px;white-space:pre-wrap;background:rgba(0,0,0,0.15);margin:0"></pre>
    </div>
    <style>
      .fb-bar { display:flex; gap:6px; align-items:center; margin-top:12px; }
      .fb-path-input { flex:1; padding:7px 10px; border:1px solid var(--border); border-radius:6px; background:var(--bg); color:var(--text); font-size:12px; font-family:monospace; }
      .fb-content { margin-top:8px; background:var(--bg-card); border-radius:var(--radius-md); border:1px solid var(--border); overflow:hidden; }
      .fb-item { display:flex; align-items:center; gap:8px; padding:6px 12px; font-size:12px; border-bottom:1px solid rgba(255,255,255,0.03); cursor:pointer; }
      .fb-item:hover { background:rgba(255,255,255,0.04); }
      .fb-item .icon { width:18px; text-align:center; }
      .fb-item .name { flex:1; }
      .fb-item .size { color:var(--text-muted); font-size:11px; width:70px; text-align:right; }
      .fb-item .date { color:var(--text-muted); font-size:11px; width:120px; text-align:right; }
      .fb-preview { margin-top:8px; background:var(--bg-card); border-radius:var(--radius-md); border:1px solid var(--border); overflow:hidden; }
      .fb-preview-header { display:flex; justify-content:space-between; align-items:center; padding:8px 12px; border-bottom:1px solid var(--border); }
      .btn-sm { padding:4px 10px; font-size:11px; }
    </style>
  `;
  window._fbPath = currentPath;
  await fbLoad(currentPath);
}

async function fbLoad(path) {
  window._fbPath = path;
  document.getElementById('fbPathInput').value = path;
  document.getElementById('fbCurrentPath').textContent = path;
  document.getElementById('fbUpBtn').disabled = path === '/' || path === '/workspace';
  
  try {
    const res = await fetch(`/api/fs/list?path=${encodeURIComponent(path)}`);
    const data = await res.json();
    const items = data.items || [];
    const container = document.getElementById('fbContent');

    if (items.length === 0) {
      container.innerHTML = '<div style="padding:24px;text-align:center;color:var(--text-muted);font-size:13px">📭 Empty directory</div>';
      return;
    }

    container.innerHTML = items.map(item => {
      const isDir = item.type === 'dir' || item.type === 'directory';
      const icon = isDir ? '📁' : '📄';
      return `<div class="fb-item" onclick="${isDir ? `fbLoad('${escapeHtml(item.path)}')` : `fbPreview('${escapeHtml(item.path)}')`}">
        <span class="icon">${icon}</span>
        <span class="name">${escapeHtml(item.name)}</span>
        <span class="size">${isDir ? '' : formatBytes(item.size || 0)}</span>
        <span class="date">${item.modified ? formatDate(item.modified) : ''}</span>
      </div>`;
    }).join('');
  } catch(e) {
    document.getElementById('fbContent').innerHTML = `<div style="padding:24px;text-align:center;color:#d63031;font-size:13px">⚠️ ${escapeHtml(e.message)}</div>`;
  }
}

function fbGoUp() {
  const p = window._fbPath || '/workspace';
  const up = p.substring(0, p.lastIndexOf('/')) || '/';
  fbLoad(up);
}

function fbGoTo(path) {
  fbLoad(path || '/workspace');
}

async function fbPreview(path) {
  const preview = document.getElementById('fbPreview');
  const name = document.getElementById('fbPreviewName');
  const body = document.getElementById('fbPreviewBody');
  preview.style.display = 'block';
  name.textContent = path.split('/').pop();
  body.textContent = 'Loading...';
  try {
    const res = await fetch(`/api/fs/read?path=${encodeURIComponent(path)}`);
    const data = await res.json();
    body.textContent = data.content || '(empty file)';
  } catch(e) {
    body.textContent = `Error: ${e.message}`;
  }
}
