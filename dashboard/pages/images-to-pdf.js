async function renderImagesToPdf() {
  const content = document.getElementById('pageContent');

  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">🖼️ Images → PDF</div>
        <div class="page-subtitle">Upload images, reorder by dragging, convert to a single PDF</div>
      </div>
      <div class="btn-group" id="convActions" style="display:none">
        <button class="btn btn-ghost" onclick="clearPdfUploads()">🗑️ Clear All</button>
        <button class="btn btn-primary" onclick="convertToPdf()" id="convertBtn">📄 Convert to PDF</button>
      </div>
    </div>

    <div class="ip-grid">
      <div class="ip-dropzone" id="dropzone">
        <div class="ip-dropzone-inner" id="dropzoneInner">
          <div class="ip-dropzone-icon">📁</div>
          <div class="ip-dropzone-text">Drop images here or click to browse</div>
          <div class="ip-dropzone-hint">PNG, JPG, GIF, BMP, TIFF, WEBP</div>
          <input type="file" id="fileInput" multiple accept=".png,.jpg,.jpeg,.gif,.bmp,.tiff,.tif,.webp" style="display:none">
          <button class="btn btn-primary mt-2" onclick="document.getElementById('fileInput').click()">Choose Files</button>
        </div>
      </div>

      <div class="ip-list" id="fileList">
        <div class="ip-list-empty" id="emptyState">
          <div class="ip-list-empty-icon">📸</div>
          <div class="ip-list-empty-text">No images added yet</div>
          <div class="ip-list-empty-hint">Drop files above or click the button</div>
        </div>
      </div>
    </div>

    <div class="ip-output" id="outputArea" style="display:none">
      <div class="ip-output-header">
        <span id="outputTitle">📄 Output</span>
        <div>
          <button class="btn btn-ghost btn-xs" onclick="downloadPdf()" id="downloadBtn" style="display:none">⬇️ Download</button>
        </div>
      </div>
      <iframe id="pdfPreview" style="width:100%;height:500px;border:none;border-radius:6px;background:#fff" sandbox="allow-scripts"></iframe>
    </div>

    <style>
      .ip-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }
      @media (max-width: 900px) { .ip-grid { grid-template-columns: 1fr; } }

      .ip-dropzone { background: var(--bg-card); border: 2px dashed var(--border); border-radius: var(--radius-md); padding: 32px; text-align: center; transition: all 0.2s; min-height: 280px; display: flex; align-items: center; justify-content: center; }
      .ip-dropzone.dragover { border-color: var(--primary); background: rgba(99,102,241,0.08); }
      .ip-dropzone-inner { display: flex; flex-direction: column; align-items: center; gap: 8px; }
      .ip-dropzone-icon { font-size: 48px; }
      .ip-dropzone-text { font-size: 15px; font-weight: 500; color: var(--text); }
      .ip-dropzone-hint { font-size: 12px; color: var(--text-muted); }

      .ip-list { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 12px; min-height: 280px; max-height: 400px; overflow-y: auto; }
      .ip-list-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; min-height: 240px; gap: 8px; }
      .ip-list-empty-icon { font-size: 40px; opacity: 0.5; }
      .ip-list-empty-text { font-size: 14px; color: var(--text-muted); }
      .ip-list-empty-hint { font-size: 12px; color: var(--text-muted); opacity: 0.7; }

      .ip-file-item { display: flex; align-items: center; gap: 10px; padding: 8px 10px; border: 1px solid var(--border); border-radius: 6px; margin-bottom: 6px; background: var(--surface); cursor: grab; transition: all 0.15s; }
      .ip-file-item:hover { border-color: var(--primary); background: rgba(99,102,241,0.05); }
      .ip-file-item.dragging { opacity: 0.5; }
      .ip-file-icon { font-size: 20px; flex-shrink: 0; }
      .ip-file-info { flex: 1; min-width: 0; }
      .ip-file-name { font-size: 12px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .ip-file-size { font-size: 10px; color: var(--text-muted); }
      .ip-file-remove { width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; border: none; background: transparent; color: var(--red); cursor: pointer; border-radius: 4px; font-size: 14px; flex-shrink: 0; }
      .ip-file-remove:hover { background: rgba(214,48,49,0.1); }
      .ip-file-drag { color: var(--text-muted); font-size: 12px; cursor: grab; flex-shrink: 0; }

      .ip-output { margin-top: 16px; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-md); overflow: hidden; }
      .ip-output-header { display: flex; justify-content: space-between; align-items: center; padding: 10px 16px; border-bottom: 1px solid var(--border); font-size: 13px; font-weight: 600; }

      .btn-xs { padding: 4px 8px; font-size: 11px; }
      .mt-2 { margin-top: 8px; }
    </style>
  `;

  // Wire up drag-and-drop
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');

  dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
  });

  // Click on dropzone also opens file picker
  dropzone.addEventListener('click', (e) => {
    if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'INPUT') {
      fileInput.click();
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) handleFiles(fileInput.files);
  });

  // Load existing files from session storage
  window._pdfFiles = window._pdfFiles || [];
  renderFileList();
}

// ─── File handling ────────────────────────────────────────

const SUPPORTED_EXTS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.webp'];

function handleFiles(fileList) {
  let added = 0;
  for (const f of fileList) {
    const ext = '.' + f.name.split('.').pop().toLowerCase();
    if (!SUPPORTED_EXTS.includes(ext)) continue;
    // Check duplicate by name + size
    if (window._pdfFiles.some(ex => ex.name === f.name && ex.size === f.size)) continue;
    window._pdfFiles.push({ name: f.name, size: f.size, file: f });
    added++;
  }
  if (added) renderFileList();
  else showToast('No new valid images (check format or duplicates)', 'info');
}

function removePdfFile(index) {
  window._pdfFiles.splice(index, 1);
  renderFileList();
}

function clearPdfUploads() {
  window._pdfFiles = [];
  document.getElementById('outputArea').style.display = 'none';
  document.getElementById('convActions').style.display = 'none';
  const preview = document.getElementById('pdfPreview');
  if (preview) preview.src = '';
  renderFileList();
}

function formatSize(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatSizeShort(bytes) {
  return formatSize(bytes);
}

let _dragSrcIdx = null;

function renderFileList() {
  const list = document.getElementById('fileList');
  const empty = document.getElementById('emptyState');
  const actions = document.getElementById('convActions');
  const files = window._pdfFiles || [];

  if (files.length === 0) {
    list.innerHTML = `
      <div class="ip-list-empty" id="emptyState">
        <div class="ip-list-empty-icon">📸</div>
        <div class="ip-list-empty-text">No images added yet</div>
        <div class="ip-list-empty-hint">Drop files or click the button</div>
      </div>
    `;
    actions.style.display = 'none';
    return;
  }

  actions.style.display = 'flex';
  document.getElementById('convertBtn').textContent = `📄 Convert ${files.length} file${files.length > 1 ? 's' : ''} to PDF`;

  list.innerHTML = files.map((f, i) => `
    <div class="ip-file-item" draggable="true" data-idx="${i}">
      <span class="ip-file-drag" title="Drag to reorder">⠿</span>
      <span class="ip-file-icon">🖼️</span>
      <div class="ip-file-info">
        <div class="ip-file-name">${escapeHtml(f.name)}</div>
        <div class="ip-file-size">${formatSize(f.size)}</div>
      </div>
      <button class="ip-file-remove" onclick="removePdfFile(${i})" title="Remove">✕</button>
    </div>
  `).join('');

  // Drag reorder
  const items = list.querySelectorAll('.ip-file-item');
  items.forEach(item => {
    item.addEventListener('dragstart', (e) => {
      _dragSrcIdx = parseInt(item.dataset.idx);
      item.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
    });
    item.addEventListener('dragend', () => {
      item.classList.remove('dragging');
      _dragSrcIdx = null;
    });
    item.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
    });
    item.addEventListener('drop', (e) => {
      e.preventDefault();
      const targetIdx = parseInt(item.dataset.idx);
      if (_dragSrcIdx !== null && _dragSrcIdx !== targetIdx) {
        const arr = window._pdfFiles;
        const [moved] = arr.splice(_dragSrcIdx, 1);
        arr.splice(targetIdx, 0, moved);
        renderFileList();
      }
    });
  });
}

// ─── Conversion ───────────────────────────────────────────

let _lastPdfBlobUrl = null;
let _lastPdfBlob = null;

async function convertToPdf() {
  const files = window._pdfFiles || [];
  if (files.length === 0) {
    showToast('No images to convert', 'warning');
    return;
  }

  const btn = document.getElementById('convertBtn');
  const originalText = btn.textContent;
  btn.textContent = '⏳ Converting...';
  btn.disabled = true;

  try {
    const formData = new FormData();
    for (const f of files) {
      formData.append('files', f.file, f.name);
    }

    const res = await fetch('/api/pdf/images2pdf', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
      throw new Error(err.error || `Request failed: ${res.status}`);
    }

    // Get the blob and show preview
    const blob = await res.blob();
    _lastPdfBlob = blob;

    if (_lastPdfBlobUrl) URL.revokeObjectURL(_lastPdfBlobUrl);
    _lastPdfBlobUrl = URL.createObjectURL(blob);

    // Show output area
    const outputArea = document.getElementById('outputArea');
    outputArea.style.display = 'block';
    document.getElementById('downloadBtn').style.display = 'inline-flex';

    const filename = `images_${files.length}_${new Date().toISOString().slice(0,10)}.pdf`;
    document.getElementById('outputTitle').textContent = `📄 ${filename} (${formatSize(blob.size)})`;

    // Display preview
    const preview = document.getElementById('pdfPreview');
    preview.src = _lastPdfBlobUrl;

    showToast(`✅ PDF created — ${files.length} page${files.length > 1 ? 's' : ''}`, 'success');
  } catch (err) {
    showToast(`❌ ${err.message}`, 'error');
  } finally {
    btn.textContent = originalText;
    btn.disabled = false;
  }
}

function downloadPdf() {
  if (!_lastPdfBlob || !_lastPdfBlobUrl) return;
  const a = document.createElement('a');
  a.href = _lastPdfBlobUrl;
  a.download = `images2pdf_${new Date().toISOString().slice(0,10)}.pdf`;
  a.click();
}
