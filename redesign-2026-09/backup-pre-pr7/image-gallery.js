async function renderImageGallery() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">🎨 Image Gallery</div>
        <div class="page-subtitle">Browse design mockups and generated images</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="igRefresh()">🔄 Refresh</button>
        <a href="https://aistudio.google.com" target="_blank" class="btn btn-primary">✨ Create in AI Studio</a>
        <a href="https://chatgpt.com" target="_blank" class="btn btn-primary">🎨 DALL-E</a>
      </div>
    </div>
    <div class="ig-layout">
      <div class="ig-sidebar">
        <div class="ig-sidebar-title">📁 Folders</div>
        <div id="igFolderList">
          <div class="ig-folder ig-folder-active" data-folder="" onclick="igSelectFolder('')">📂 All Images</div>
        </div>
        <div class="ig-sidebar-divider"></div>
        <div class="ig-sidebar-title">Filter</div>
        <div class="ig-filter-group">
          <label class="ig-filter-label">Type</label>
          <select id="igTypeFilter" class="ig-select" onchange="igApplyFilters()">
            <option value="all">All</option>
            <option value="image">Images</option>
            <option value="png">PNG</option>
            <option value="jpg">JPG/JPEG</option>
            <option value="webp">WebP</option>
            <option value="gif">GIF</option>
            <option value="svg">SVG</option>
          </select>
        </div>
        <div class="ig-filter-group">
          <label class="ig-filter-label">Min Size</label>
          <select id="igSizeFilter" class="ig-select" onchange="igApplyFilters()">
            <option value="0">Any</option>
            <option value="100000">&gt; 100 KB</option>
            <option value="500000">&gt; 500 KB</option>
            <option value="1000000">&gt; 1 MB</option>
            <option value="5000000">&gt; 5 MB</option>
          </select>
        </div>
        <div class="ig-filter-group">
          <label class="ig-filter-label">Search</label>
          <input type="text" id="igSearch" class="ig-input" placeholder="Search filenames..." oninput="igApplyFilters()">
        </div>
      </div>
      <div class="ig-main">
        <div class="ig-toolbar">
          <div class="ig-view-toggle">
            <button class="ig-view-btn ig-view-active" onclick="igSetView('grid')" title="Grid view">▦</button>
            <button class="ig-view-btn" onclick="igSetView('list')" title="List view">☰</button>
          </div>
          <div id="igImageCount" class="ig-count">0 images</div>
        </div>
        <div id="igGrid" class="ig-grid"></div>
        <div id="igFullscreen" class="ig-fullscreen" style="display:none" onclick="igCloseFullscreen()">
          <div class="ig-fullscreen-toolbar">
            <span id="igFSName" class="ig-fs-name"></span>
            <div class="ig-fs-actions">
              <button class="btn btn-ghost" onclick="event.stopPropagation(); igDownloadCurrent()">⬇ Download</button>
              <button class="btn btn-ghost" onclick="event.stopPropagation(); igCopyPath()">📋 Copy Path</button>
              <button class="btn btn-ghost ig-fs-close" onclick="igCloseFullscreen()">✕</button>
            </div>
          </div>
          <div class="ig-fullscreen-image-wrap">
            <button class="ig-nav-btn ig-nav-prev" onclick="event.stopPropagation(); igNavFS(-1)">‹</button>
            <img id="igFSImage" class="ig-fullscreen-image" src="" alt="">
            <button class="ig-nav-btn ig-nav-next" onclick="event.stopPropagation(); igNavFS(1)">›</button>
          </div>
          <div class="ig-fs-info" id="igFSInfo"></div>
        </div>
      </div>
    </div>
  `;

  // Load data
  await igLoad();
}

// ── State ──
let _igAllImages = [];
let _igFiltered = [];
let _igFolders = [];
let _igView = 'grid';
let _igActiveFolder = '';
let _igFSIndex = -1;

// ── Loading ──
async function igLoad() {
  const grid = document.getElementById('igGrid');
  if (!grid) return;
  grid.innerHTML = '<div class="ig-loading">📂 Scanning workspace...</div>';

  try {
    const res = await fetch('/api/images/list');
    const data = await res.json();
    _igAllImages = data.images || [];
    _igFolders = data.folders || [];

    // Render folder list
    const fl = document.getElementById('igFolderList');
    if (fl) {
      fl.innerHTML = '<div class="ig-folder ig-folder-active" data-folder="" onclick="igSelectFolder(\'\')">📂 All Images</div>';
      _igFolders.forEach(f => {
        const name = f.replace(/^\/workspace\//, '');
        fl.innerHTML += `<div class="ig-folder" data-folder="${f}" onclick="igSelectFolder('${f}')">📁 ${name}</div>`;
      });
    }

    igApplyFilters();
  } catch (err) {
    grid.innerHTML = `<div class="ig-error">❌ Failed to load: ${err.message}</div>`;
  }
}

function igRefresh() { igLoad(); }

// ── Filtering ──
function igSelectFolder(folder) {
  _igActiveFolder = folder;
  document.querySelectorAll('.ig-folder').forEach(el => el.classList.remove('ig-folder-active'));
  const target = document.querySelector(`.ig-folder[data-folder="${folder}"]`);
  if (target) target.classList.add('ig-folder-active');
  igApplyFilters();
}

function igApplyFilters() {
  const typeFilter = document.getElementById('igTypeFilter')?.value || 'all';
  const sizeFilter = parseInt(document.getElementById('igSizeFilter')?.value || '0');
  const search = (document.getElementById('igSearch')?.value || '').toLowerCase();

  _igFiltered = _igAllImages.filter(img => {
    // Folder filter
    if (_igActiveFolder && !img.path.startsWith(_igActiveFolder)) return false;

    // Type filter
    const ext = (img.ext || '').toLowerCase().replace('.', '');
    if (typeFilter !== 'all') {
      if (typeFilter === 'image' && !['png','jpg','jpeg','gif','webp','svg'].includes(ext)) return false;
      else if (typeFilter !== 'image' && ext !== typeFilter) return false;
    }

    // Size filter
    if (img.size < sizeFilter) return false;

    // Search
    if (search && !img.name.toLowerCase().includes(search)) return false;

    return true;
  });

  // Update count
  const count = document.getElementById('igImageCount');
  if (count) count.textContent = `${_igFiltered.length} images`;

  igRender();
}

// ── Render ──
function igRender() {
  const grid = document.getElementById('igGrid');
  if (!grid) return;

  if (_igFiltered.length === 0) {
    grid.innerHTML = '<div class="ig-empty">📭 No images found</div>';
    return;
  }

  if (_igView === 'grid') {
    grid.className = 'ig-grid';
    grid.innerHTML = _igFiltered.map((img, i) => `
      <div class="ig-card" onclick="igOpenFS(${i})" title="${img.name}">
        <div class="ig-card-img-wrap">
          <img class="ig-card-img" src="/api/images/file?path=${encodeURIComponent(img.path)}" alt="${img.name}" loading="lazy">
        </div>
        <div class="ig-card-footer">
          <div class="ig-card-name">${img.name}</div>
          <div class="ig-card-meta">${igFormatSize(img.size)}</div>
        </div>
      </div>
    `).join('');
  } else {
    grid.className = 'ig-list';
    grid.innerHTML = `
      <div class="ig-list-header">
        <span class="ig-list-col-name">Name</span>
        <span class="ig-list-col-size">Size</span>
        <span class="ig-list-col-date">Modified</span>
        <span class="ig-list-col-folder">Folder</span>
        <span class="ig-list-col-actions"></span>
      </div>
      ${_igFiltered.map((img, i) => `
        <div class="ig-list-row" onclick="igOpenFS(${i})">
          <span class="ig-list-col-name"><img class="ig-list-thumb" src="/api/images/file?path=${encodeURIComponent(img.path)}" alt=""> ${img.name}</span>
          <span class="ig-list-col-size">${igFormatSize(img.size)}</span>
          <span class="ig-list-col-date">${img.modified || ''}</span>
          <span class="ig-list-col-folder">${img.folder.replace('/workspace/', '')}</span>
          <span class="ig-list-col-actions">
            <button class="btn btn-ghost btn-sm" onclick="event.stopPropagation(); igDownload('${encodeURIComponent(img.path)}', '${img.name}')">⬇</button>
          </span>
        </div>
      `).join('')}
    `;
  }
}

// ── View Toggle ──
function igSetView(view) {
  _igView = view;
  document.querySelectorAll('.ig-view-btn').forEach(b => b.classList.remove('ig-view-active'));
  const btns = document.querySelectorAll('.ig-view-btn');
  if (view === 'grid') btns[0]?.classList.add('ig-view-active');
  else btns[1]?.classList.add('ig-view-active');
  igRender();
}

// ── Fullscreen ──
let _igFSItems = [];

function igOpenFS(index) {
  _igFSItems = _igFiltered;
  _igFSIndex = index;
  const img = _igFSItems[index];
  if (!img) return;

  const fs = document.getElementById('igFullscreen');
  const fsImg = document.getElementById('igFSImage');
  const fsName = document.getElementById('igFSName');
  const fsInfo = document.getElementById('igFSInfo');

  fsImg.src = `/api/images/file?path=${encodeURIComponent(img.path)}`;
  fsName.textContent = img.name;
  fsInfo.textContent = `${img.width || '?'} × ${img.height || '?'} · ${igFormatSize(img.size)} · ${img.modified || ''}`;
  fs.style.display = 'flex';
}

function igCloseFullscreen() {
  document.getElementById('igFullscreen').style.display = 'none';
}

function igNavFS(dir) {
  const newIdx = _igFSIndex + dir;
  if (newIdx >= 0 && newIdx < _igFSItems.length) {
    igOpenFS(newIdx);
  }
}

function igDownloadCurrent() {
  const img = _igFSItems[_igFSIndex];
  if (!img) return;
  igDownload(img.path, img.name);
}

function igDownload(path, name) {
  const a = document.createElement('a');
  a.href = `/api/images/file?path=${encodeURIComponent(path)}`;
  a.download = name;
  a.click();
}

function igCopyPath() {
  const img = _igFSItems[_igFSIndex];
  if (!img) return;
  navigator.clipboard.writeText(img.path).then(() => {
    const btn = document.querySelector('.ig-fs-close');
    const orig = btn.textContent;
    btn.textContent = '✅ Copied!';
    setTimeout(() => btn.textContent = orig, 1500);
  });
}

// ── Helpers ──
function igFormatSize(bytes) {
  if (!bytes) return '';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}

// Keyboard navigation
document.addEventListener('keydown', function(e) {
  const fs = document.getElementById('igFullscreen');
  if (!fs || fs.style.display === 'none') return;
  if (e.key === 'Escape') igCloseFullscreen();
  else if (e.key === 'ArrowLeft') igNavFS(-1);
  else if (e.key === 'ArrowRight') igNavFS(1);
});
