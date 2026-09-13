/**
 * Meeting Reports — Upload + Transcribe + Analyze + Report Pipeline
 *
 * Workflow:
 *   1. Upload any file (PDF, DOCX, TXT, etc.) or paste text
 *   2. Server extracts text from documents
 *   3. AI extracts: attendees, decisions, action items, summary
 *   4. Generates formatted markdown report
 *   5. Optionally email the report
 *
 * API:
 *   POST /api/crm/workflows/upload  — multipart file upload
 *   POST /api/crm/workflows/run     — run pipeline
 */

let _uploadedFilePath = null;
let _uploadedFileName = null;

async function renderMeetingReports() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">Meeting Reports</div>
        <div class="page-subtitle">Upload meeting docs or paste notes — get a structured report with action items</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderMeetingReports()">Refresh</button>
      </div>
    </div>

    <div class="grid-2" style="margin-top:16px;gap:16px;align-items:start;">
      <div class="card" style="padding:20px;">
        <div style="font-size:15px;font-weight:600;color:var(--text-primary);margin-bottom:16px;">Input</div>

        <div id="meetingFileDrop" style="border:2px dashed var(--border);border-radius:var(--radius);padding:24px 16px;text-align:center;cursor:pointer;transition:border-color 0.2s,background 0.2s;margin-bottom:16px;background:var(--bg-input);"
             onclick="document.getElementById('meetingFileInput').click()"
             ondragover="Meetings_onDragOver(event)"
             ondragleave="Meetings_onDragLeave(event)"
             ondrop="Meetings_onDrop(event)">
          <div style="font-size:32px;margin-bottom:8px;" id="meetingFileIcon">&#x1F4C4;</div>
          <div style="font-size:14px;color:var(--text-primary);font-weight:500;" id="meetingFileLabel">Drop a file or click to browse</div>
          <div style="font-size:12px;color:var(--text-muted);margin-top:4px;">PDF, DOCX, TXT, MD, CSV — any meeting document</div>
          <div id="meetingFileStatus" style="font-size:12px;color:var(--accent);margin-top:6px;display:none;"></div>
          <input type="file" id="meetingFileInput" accept=".pdf,.docx,.txt,.md,.csv,.json,.log,.mp3,.wav,.m4a" style="display:none;" onchange="Meetings_onFileSelect(event)">
        </div>

        <div style="font-size:13px;color:var(--text-muted);text-align:center;margin-bottom:16px;">— or paste text below —</div>

        <label style="display:block;font-size:13px;color:var(--text-secondary);margin-bottom:6px;">Meeting text / transcript</label>
        <textarea id="meetingTextInput" placeholder="Paste meeting notes, transcript, or discussion points here..."
          style="width:100%;min-height:120px;background:var(--bg-input);border:1px solid var(--border);border-radius:var(--radius-sm);color:var(--text-primary);padding:12px;font-size:14px;font-family:var(--font);resize:vertical;"
        ></textarea>

        <label style="display:block;font-size:13px;color:var(--text-secondary);margin-top:14px;margin-bottom:6px;">Email report to (optional)</label>
        <input type="text" id="meetingEmailInput" placeholder="comma-separated email addresses"
          style="width:100%;background:var(--bg-input);border:1px solid var(--border);border-radius:var(--radius-sm);color:var(--text-primary);padding:10px 12px;font-size:14px;font-family:var(--font);"
        />

        <button id="meetingRunBtn" class="btn btn-primary" style="width:100%;margin-top:16px;padding:12px;font-size:15px;" onclick="Meetings_runPipeline()">
          Generate Report
        </button>

        <div id="meetingStatus" style="margin-top:12px;font-size:13px;color:var(--text-secondary);min-height:20px;"></div>
        <div id="meetingProgress" style="margin-top:4px;display:none;">
          <div style="height:3px;background:var(--bg-card-hover);border-radius:3px;overflow:hidden;">
            <div id="meetingProgressBar" style="height:100%;width:0%;background:var(--accent);border-radius:3px;transition:width 0.5s;"></div>
          </div>
        </div>
      </div>

      <div class="card" style="padding:20px;">
        <div style="font-size:15px;font-weight:600;color:var(--text-primary);margin-bottom:16px;">Report</div>
        <div id="meetingReportOutput" style="font-size:14px;color:var(--text-secondary);">
          <div style="text-align:center;padding:40px 20px;color:var(--text-muted);">
            <div style="font-size:48px;margin-bottom:12px;">&#x1F4CB;</div>
            <div>Your report appears here</div>
            <div style="font-size:12px;margin-top:6px;">Drop a PDF/DOCX or paste text and hit Generate</div>
          </div>
        </div>
      </div>
    </div>
  `;

  _uploadedFilePath = null;
  _uploadedFileName = null;
}

// ─── Drag & Drop ────────────────────────────────────────────────

function Meetings_onDragOver(e) {
  e.preventDefault();
  e.stopPropagation();
  e.currentTarget.style.borderColor = 'var(--accent)';
  e.currentTarget.style.background = 'var(--accent-dim)';
}

function Meetings_onDragLeave(e) {
  e.preventDefault();
  e.stopPropagation();
  e.currentTarget.style.borderColor = 'var(--border)';
  e.currentTarget.style.background = 'var(--bg-input)';
}

function Meetings_onDrop(e) {
  e.preventDefault();
  e.stopPropagation();
  e.currentTarget.style.borderColor = 'var(--border)';
  e.currentTarget.style.background = 'var(--bg-input)';
  const file = e.dataTransfer.files[0];
  if (file) Meetings_handleFile(file);
}

function Meetings_onFileSelect(e) {
  const file = e.target.files[0];
  if (file) Meetings_handleFile(file);
}

async function Meetings_handleFile(file) {
  const label = document.getElementById('meetingFileLabel');
  const icon = document.getElementById('meetingFileIcon');
  const status = document.getElementById('meetingFileStatus');
  const drop = document.getElementById('meetingFileDrop');

  label.textContent = file.name;
  label.style.color = 'var(--text-primary)';
  icon.innerHTML = Meetings_fileIcon(file.name);
  drop.style.borderColor = 'var(--accent)';
  status.style.display = 'block';
  status.textContent = 'Uploading...';
  status.style.color = 'var(--yellow)';

  // Clear text input since we're using a file
  document.getElementById('meetingTextInput').value = '';

  try {
    const formData = new FormData();
    formData.append('file', file);

    const resp = await fetch('/api/crm/workflows/upload', {
      method: 'POST',
      body: formData,
    });
    const result = await resp.json();

    if (result.success) {
      _uploadedFilePath = result.file_path;
      _uploadedFileName = result.filename;
      status.textContent = 'Uploaded (' + Meetings_fmtSize(result.size) + ')';
      status.style.color = 'var(--green)';
    } else {
      status.textContent = 'Upload failed: ' + (result.error || 'unknown');
      status.style.color = 'var(--red)';
      _uploadedFilePath = null;
    }
  } catch (err) {
    status.textContent = 'Upload failed: ' + err.message;
    status.style.color = 'var(--red)';
    _uploadedFilePath = null;
  }
}

function Meetings_fileIcon(name) {
  const ext = (name || '').split('.').pop().toLowerCase();
  const icons = { pdf: '&#x1F4D5;', docx: '&#x1F4DD;', doc: '&#x1F4DD;', txt: '&#x1F4C4;', md: '&#x1F4DD;', csv: '&#x1F4CA;', json: '&#x1F4BE;', mp3: '&#x1F3A4;', wav: '&#x1F3A4;', m4a: '&#x1F3A4;' };
  return icons[ext] || '&#x1F4C4;';
}

function Meetings_fmtSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ─── Pipeline Runner ────────────────────────────────────────────

async function Meetings_runPipeline() {
  const btn = document.getElementById('meetingRunBtn');
  const statusEl = document.getElementById('meetingStatus');
  const outputEl = document.getElementById('meetingReportOutput');
  const progressEl = document.getElementById('meetingProgress');
  const progressBar = document.getElementById('meetingProgressBar');

  const text = document.getElementById('meetingTextInput').value.trim();
  const emailRecipients = document.getElementById('meetingEmailInput').value.trim();

  if (!text && !_uploadedFilePath) {
    statusEl.innerHTML = '<span style="color:var(--red);">Drop a file or paste meeting text.</span>';
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Processing...';
  progressEl.style.display = 'block';
  progressBar.style.width = '10%';
  statusEl.innerHTML = _uploadedFilePath ? 'Extracting text from ' + _uploadedFileName + '...' : 'Analyzing meeting text...';
  outputEl.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);"><div class="spinner"></div><div style="margin-top:12px;">Processing...</div></div>';

  try {
    const body = {
      workflow_id: 'meeting-report',
    };
    if (_uploadedFilePath) body.file_path = _uploadedFilePath;
    if (text) body.text = text;
    if (emailRecipients) body.email_recipients = emailRecipients;

    progressBar.style.width = '30%';
    statusEl.innerHTML = 'Extracting decisions, action items, generating report...';

    const resp = await fetch('/api/crm/workflows/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    progressBar.style.width = '80%';
    const result = await resp.json();

    if (result.success) {
      progressBar.style.width = '100%';
      statusEl.innerHTML = '<span style="color:var(--green);">Report saved to ' + (result.output_dir || 'disk') + '</span>';
      Meetings_renderReport(result);
    } else {
      statusEl.innerHTML = '<span style="color:var(--red);">' + (result.error || 'Pipeline failed') + '</span>';
      outputEl.innerHTML = '<div style="padding:20px;color:var(--red);background:var(--red-dim);border-radius:var(--radius-sm);">' + _esc(result.error || 'Unknown error') + '</div>';
    }
  } catch (err) {
    statusEl.innerHTML = '<span style="color:var(--red);">' + err.message + '</span>';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate Report';
    setTimeout(function() { progressEl.style.display = 'none'; progressBar.style.width = '0%'; }, 1500);
  }
}

// ─── Report Renderer ────────────────────────────────────────────

function Meetings_renderReport(result) {
  const outputEl = document.getElementById('meetingReportOutput');
  const d = result.data || {};
  const report = result.report || '';

  let html = '';

  // Quick stats
  html += '<div class="grid-4" style="gap:10px;margin-bottom:16px;">';
  html += '<div class="stat-card" style="padding:12px;"><div style="font-size:22px;font-weight:700;color:var(--accent);">' + (d.action_items || []).length + '</div><div style="font-size:12px;color:var(--text-secondary);">Action Items</div></div>';
  html += '<div class="stat-card" style="padding:12px;"><div style="font-size:22px;font-weight:700;color:var(--accent);">' + (d.decisions || []).length + '</div><div style="font-size:12px;color:var(--text-secondary);">Decisions</div></div>';
  html += '<div class="stat-card" style="padding:12px;"><div style="font-size:22px;font-weight:700;color:var(--accent);">' + (d.attendees || []).length + '</div><div style="font-size:12px;color:var(--text-secondary);">Attendees</div></div>';
  html += '<div class="stat-card" style="padding:12px;"><div style="font-size:22px;font-weight:700;color:var(--green);">' + (result.email_sent ? 'Sent' : 'Saved') + '</div><div style="font-size:12px;color:var(--text-secondary);">Status</div></div>';
  html += '</div>';

  // Title
  if (d.title) {
    html += '<div style="font-size:18px;font-weight:700;color:var(--text-primary);margin-bottom:4px;">' + _esc(d.title) + '</div>';
  }
  if (d.date) {
    html += '<div style="font-size:13px;color:var(--text-secondary);margin-bottom:12px;">' + _esc(d.date) + '</div>';
  }

  // Tabs
  html += '<div class="tabs" style="margin-bottom:12px;">';
  html += '<button class="tab active" onclick="Meetings_switchTab(event,\'summary\')">Summary</button>';
  html += '<button class="tab" onclick="Meetings_switchTab(event,\'actions\')">Action Items</button>';
  html += '<button class="tab" onclick="Meetings_switchTab(event,\'decisions\')">Decisions</button>';
  html += '<button class="tab" onclick="Meetings_switchTab(event,\'full\')">Full Report</button>';
  html += '</div>';

  // Summary tab
  html += '<div id="tab-summary" class="tab-content" style="display:block;">';
  html += '<div style="font-size:14px;line-height:1.6;color:var(--text-primary);white-space:pre-wrap;">' + _esc(d.summary || 'No summary available.') + '</div>';
  if (d.key_discussion_points && d.key_discussion_points.length > 0) {
    html += '<div style="font-size:14px;font-weight:600;color:var(--text-primary);margin-top:16px;margin-bottom:8px;">Key Discussion Points</div>';
    html += '<ol style="margin:0;padding-left:20px;font-size:14px;color:var(--text-primary);line-height:1.8;">';
    d.key_discussion_points.forEach(function(p) { html += '<li>' + _esc(p) + '</li>'; });
    html += '</ol>';
  }
  html += '</div>';

  // Action Items tab
  html += '<div id="tab-actions" class="tab-content" style="display:none;">';
  if ((d.action_items || []).length > 0) {
    html += '<table style="width:100%;border-collapse:collapse;font-size:14px;">';
    html += '<thead><tr style="border-bottom:1px solid var(--border);"><th style="text-align:left;padding:8px;color:var(--text-secondary);">Item</th><th style="text-align:left;padding:8px;color:var(--text-secondary);">Owner</th><th style="text-align:left;padding:8px;color:var(--text-secondary);">Deadline</th></tr></thead><tbody>';
    d.action_items.forEach(function(a) {
      html += '<tr style="border-bottom:1px solid var(--border);">';
      html += '<td style="padding:8px;color:var(--text-primary);">' + _esc(a.item || a) + '</td>';
      html += '<td style="padding:8px;color:var(--accent);">' + _esc(a.owner || '-') + '</td>';
      html += '<td style="padding:8px;color:var(--text-secondary);">' + _esc(a.deadline || '-') + '</td>';
      html += '</tr>';
    });
    html += '</tbody></table>';
  } else {
    html += '<div style="padding:16px;color:var(--text-muted);">No action items extracted.</div>';
  }
  html += '</div>';

  // Decisions tab
  html += '<div id="tab-decisions" class="tab-content" style="display:none;">';
  if ((d.decisions || []).length > 0) {
    d.decisions.forEach(function(dec) {
      html += '<div style="background:var(--bg-card-hover);border-left:3px solid var(--accent);padding:12px;margin-bottom:8px;border-radius:0 var(--radius-sm) var(--radius-sm) 0;">';
      html += '<div style="font-weight:600;color:var(--text-primary);">' + _esc(dec.decision || dec) + '</div>';
      if (dec.context) html += '<div style="font-size:13px;color:var(--text-secondary);margin-top:4px;">' + _esc(dec.context) + '</div>';
      html += '</div>';
    });
  } else {
    html += '<div style="padding:16px;color:var(--text-muted);">No decisions extracted.</div>';
  }
  html += '</div>';

  // Full Report tab
  html += '<div id="tab-full" class="tab-content" style="display:none;">';
  html += '<div style="font-size:13px;line-height:1.7;color:var(--text-primary);white-space:pre-wrap;max-height:500px;overflow-y:auto;background:var(--bg-input);padding:16px;border-radius:var(--radius-sm);font-family:var(--font-mono);">' + _esc(report) + '</div>';
  html += '</div>';

  // Attendees
  if ((d.attendees || []).length > 0) {
    html += '<div style="margin-top:16px;padding-top:12px;border-top:1px solid var(--border);">';
    html += '<div style="font-size:13px;font-weight:600;color:var(--text-secondary);margin-bottom:6px;">Attendees</div>';
    html += '<div style="display:flex;flex-wrap:wrap;gap:6px;">';
    d.attendees.forEach(function(a) {
      html += '<span style="background:var(--bg-card-hover);color:var(--text-primary);padding:4px 10px;border-radius:12px;font-size:12px;">' + _esc(a.name || a) + (a.role ? ' <span style="color:var(--text-secondary);">· ' + _esc(a.role) + '</span>' : '') + '</span>';
    });
    html += '</div></div>';
  }

  // Tags
  if ((d.tags || []).length > 0) {
    html += '<div style="margin-top:8px;">';
    d.tags.forEach(function(t) {
      html += '<span style="display:inline-block;background:var(--accent-dim);color:var(--accent-light);padding:2px 8px;border-radius:4px;font-size:11px;margin-right:4px;margin-top:4px;">#' + _esc(t) + '</span>';
    });
    html += '</div>';
  }

  outputEl.innerHTML = html;
}

function Meetings_switchTab(event, tabId) {
  var tabs = event.target.parentElement.querySelectorAll('.tab');
  tabs.forEach(function(t) { t.classList.remove('active'); });
  event.target.classList.add('active');
  var contents = document.querySelectorAll('#meetingReportOutput .tab-content');
  contents.forEach(function(c) { c.style.display = 'none'; });
  var target = document.getElementById('tab-' + tabId);
  if (target) target.style.display = 'block';
}

function _esc(str) {
  if (!str) return '';
  var div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
