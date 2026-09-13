let _gsProjects = [];
let _gsCurrentProject = null;
let _gsCurrentFiles = [];
let _gsActiveFileIndex = 0;
let _gsEditorTimer = null;

async function renderGoogleStudio() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">Google Dev Studio</h1>
        <p class="page-subtitle">Build Google Apps Script add-ons and web apps</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="gsNewProject()">➕ New Project</button>
        <button class="btn" onclick="gsRefresh()">🔄 Refresh</button>
        <a class="btn" href="https://script.google.com" target="_blank" rel="noopener">🚀 Open Script Editor</a>
      </div>
    </div>
    <div class="google-studio-layout">
      <div class="google-studio-sidebar">
        <div class="google-studio-sidebar-header">
          <h3>📁 My Scripts</h3>
          <button class="btn btn-sm" onclick="gsNewProject()" title="New Project">➕</button>
        </div>
        <div class="google-studio-project-list" id="gsProjectList">
          <div class="google-studio-empty" style="padding:20px;font-size:12px;color:var(--text-muted);text-align:center">
            Loading projects...
          </div>
        </div>
      </div>
      <div class="google-studio-main" id="gsMain">
        <div class="google-studio-empty" id="gsEmptyState">
          <div class="google-studio-empty-icon">📝</div>
          <div class="google-studio-empty-title">Select a project</div>
          <div class="google-studio-empty-desc">Choose a script from the left sidebar, or create a new one to start building Google add-ons and web apps.</div>
          <div style="display:flex;gap:8px;margin-top:8px">
            <button class="btn btn-sm" onclick="gsNewProject()">➕ New Project</button>
            <a class="btn btn-sm" href="https://script.google.com" target="_blank" rel="noopener">🚀 Open Script Editor</a>
          </div>
        </div>
        <div class="google-studio-editor-area" id="gsEditorArea" style="display:none">
          <div class="google-studio-toolbar">
            <span class="google-studio-toolbar-title" id="gsProjectTitle">Untitled</span>
            <div class="google-studio-toolbar-actions">
              <button class="btn btn-sm" onclick="gsSaveProject()" title="Save to Google Drive">💾 Save</button>
              <a class="google-studio-open-btn" id="gsOpenInScriptEditor" href="#" target="_blank" rel="noopener">▶ Open in Script Editor</a>
            </div>
          </div>
          <div class="google-studio-files-bar" id="gsFilesBar">
            <div class="google-studio-file-tab active" onclick="gsSwitchFile(0)">Code.gs</div>
          </div>
          <textarea class="google-studio-code-editor" id="gsCodeEditor" spellcheck="false"
            placeholder="// Write your Apps Script code here..."
            oninput="gsEditorChanged()">// Write your Apps Script code here
function doGet() {
  return HtmlService.createHtmlOutput('&lt;h1&gt;Hello, world!&lt;/h1&gt;');
}</textarea>
          <div class="google-studio-status-bar" id="gsStatusBar">
            <span class="status-dot offline" id="gsStatusDot"></span>
            <span id="gsStatusText">Not connected</span>
            <span style="flex:1"></span>
            <span id="gsFileInfo">App Script | JavaScript</span>
          </div>
        </div>
      </div>
    </div>
  `;

  await gsRefresh();
}

async function gsRefresh() {
  const list = document.getElementById('gsProjectList');
  if (!list) return;
  
  list.innerHTML = '<div style="padding:20px;font-size:12px;color:var(--text-muted);text-align:center">Loading...</div>';
  
  try {
    const data = await api.get('/api/google/projects');
    if (data.status === 'ok') {
      _gsProjects = data.projects || [];
      renderGsProjectList();
      document.getElementById('gsStatusDot').className = 'status-dot online';
      document.getElementById('gsStatusText').textContent = `Connected as letsgetmoney2009 • ${_gsProjects.length} projects`;
    } else {
      list.innerHTML = `<div style="padding:20px;font-size:12px;color:#ff4757;text-align:center">⚠ ${escapeHtml(data.message)}</div>`;
      document.getElementById('gsStatusDot').className = 'status-dot offline';
      document.getElementById('gsStatusText').textContent = 'Not connected';
    }
  } catch (err) {
    list.innerHTML = `<div style="padding:20px;font-size:12px;color:#ff4757;text-align:center">⚠ ${escapeHtml(err.message)}</div>`;
  }
}

function renderGsProjectList() {
  const list = document.getElementById('gsProjectList');
  if (!list) return;
  
  if (_gsProjects.length === 0) {
    list.innerHTML = '<div style="padding:20px;font-size:12px;color:var(--text-muted);text-align:center">No scripts yet.<br>Create your first one!</div>';
    return;
  }
  
  list.innerHTML = _gsProjects.map(p => {
    const isActive = _gsCurrentProject && _gsCurrentProject.id === p.id;
    const time = timeAgo(p.modifiedTime);
    return `<div class="google-studio-project-item ${isActive ? 'active' : ''}" onclick="gsSelectProject('${p.id}')">
      <span class="google-studio-project-icon">📜</span>
      <span class="google-studio-project-name">${escapeHtml(p.name)}</span>
      <span class="google-studio-project-time">${time}</span>
    </div>`;
  }).join('');
}

async function gsSelectProject(projectId) {
  const project = _gsProjects.find(p => p.id === projectId);
  if (!project) return;
  
  _gsCurrentProject = project;
  renderGsProjectList();
  
  // Show editor area
  document.getElementById('gsEmptyState').style.display = 'none';
  document.getElementById('gsEditorArea').style.display = 'flex';
  document.getElementById('gsProjectTitle').textContent = project.name;
  
  // Set open in script editor link
  const openBtn = document.getElementById('gsOpenInScriptEditor');
  openBtn.href = project.webViewLink || `https://script.google.com/home/projects/${projectId}/edit`;
  
  // Update status
  document.getElementById('gsStatusText').textContent = `Editing: ${project.name}`;
  
  // Try fetching project content from Google
  try {
    const data = await api.get(`/api/google/projects/${projectId}`);
    if (data.status === 'ok' && data.project && data.project.files) {
      _gsCurrentFiles = data.project.files;
      renderGsFileTabs();
      if (_gsCurrentFiles.length > 0) {
        loadFileIntoEditor(0);
        return;
      }
    }
  } catch {}
  
  // Fallback: default code template
  _gsCurrentFiles = [{name: 'Code.gs', type: 'SERVER_JS', source: '// ' + project.name + '\n\nfunction doGet() {\n  return HtmlService.createHtmlOutput(\'<h1>Hello from ' + project.name + '!</h1>\');\n}'}];
  renderGsFileTabs();
  loadFileIntoEditor(0);
}

function renderGsFileTabs() {
  const bar = document.getElementById('gsFilesBar');
  if (!bar) return;
  bar.innerHTML = _gsCurrentFiles.map((f, i) => {
    const icon = f.type === 'HTML' ? '🌐' : f.type === 'JSON' ? '📋' : '📜';
    const ext = f.name.split('.').pop();
    return `<div class="google-studio-file-tab ${i === _gsActiveFileIndex ? 'active' : ''}" onclick="gsSwitchFile(${i})">
      ${icon} ${escapeHtml(f.name)}
    </div>`;
  }).join('');
}

function gsSwitchFile(index) {
  if (index < 0 || index >= _gsCurrentFiles.length) return;
  // Save current editor content to current file
  if (_gsCurrentFiles[_gsActiveFileIndex]) {
    _gsCurrentFiles[_gsActiveFileIndex].source = document.getElementById('gsCodeEditor').value;
  }
  _gsActiveFileIndex = index;
  renderGsFileTabs();
  loadFileIntoEditor(index);
}

function loadFileIntoEditor(index) {
  const file = _gsCurrentFiles[index];
  if (!file) return;
  document.getElementById('gsCodeEditor').value = file.source || '';
  document.getElementById('gsFileInfo').textContent = `${file.type || 'SERVER_JS'} | ${file.name}`;
}

function gsEditorChanged() {
  // Auto-save after 2 seconds of inactivity
  clearTimeout(_gsEditorTimer);
  _gsEditorTimer = setTimeout(() => {
    if (_gsCurrentFiles[_gsActiveFileIndex]) {
      _gsCurrentFiles[_gsActiveFileIndex].source = document.getElementById('gsCodeEditor').value;
      document.getElementById('gsStatusText').textContent = `✎ Auto-saved ${_gsCurrentFiles[_gsActiveFileIndex].name}`;
    }
  }, 2000);
}

async function gsSaveProject() {
  if (!_gsCurrentProject) {
    showToast('No project selected', 'error');
    return;
  }
  
  // Save current editor content
  if (_gsCurrentFiles[_gsActiveFileIndex]) {
    _gsCurrentFiles[_gsActiveFileIndex].source = document.getElementById('gsCodeEditor').value;
  }
  
  const saveBtn = document.querySelector('.google-studio-toolbar-actions .btn');
  if (saveBtn) {
    saveBtn.textContent = '⏳ Saving...';
    saveBtn.disabled = true;
  }
  
  try {
    const payload = {
      files: _gsCurrentFiles.map(f => ({
        name: f.name,
        type: f.type || 'SERVER_JS',
        source: f.source || ''
      }))
    };
    
    const data = await api.post(`/api/google/projects/${_gsCurrentProject.id}/content`, payload);
    if (data.status === 'ok') {
      showToast('✅ Saved to Google Drive!', 'success');
      document.getElementById('gsStatusText').textContent = '✅ Saved';
    } else {
      showToast(`⚠ ${data.message}`, 'error');
    }
  } catch (err) {
    showToast(`⚠ ${err.message}`, 'error');
  }
  
  if (saveBtn) {
    saveBtn.textContent = '💾 Save';
    saveBtn.disabled = false;
  }
}

function gsNewProject() {
  // Show modal
  const overlay = document.createElement('div');
  overlay.className = 'google-studio-modal-overlay';
  overlay.id = 'gsModal';
  overlay.innerHTML = `
    <div class="google-studio-modal">
      <h3>📜 New Apps Script Project</h3>
      <p>Create a new Google Apps Script project for building add-ons or web apps.</p>
      <input type="text" id="gsNewProjectName" placeholder="Project name..." value="My Add-on" autofocus>
      <div style="margin-bottom:12px;font-size:12px;color:var(--text-muted)">
        <label style="display:flex;align-items:center;gap:8px">
          <input type="checkbox" id="gsNewProjectType" checked>
          Create as web app (with doGet/doPost)
        </label>
      </div>
      <div class="google-studio-modal-actions">
        <button class="btn" onclick="gsCloseModal()">Cancel</button>
        <button class="btn btn-primary" onclick="gsCreateProject()">Create</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);
  setTimeout(() => document.getElementById('gsNewProjectName')?.focus(), 100);
}

function gsCloseModal() {
  const modal = document.getElementById('gsModal');
  if (modal) modal.remove();
}

async function gsCreateProject() {
  const name = document.getElementById('gsNewProjectName').value.trim();
  const asWebApp = document.getElementById('gsNewProjectType').checked;
  if (!name) { showToast('Enter a project name', 'error'); return; }
  
  gsCloseModal();
  
  try {
    const data = await api.post('/api/google/projects', { title: name });
    if (data.status === 'ok') {
      showToast(`✅ Created "${name}"`, 'success');
      // Create initial files
      const files = [{
        name: 'Code.gs',
        type: 'SERVER_JS',
        source: asWebApp ? 
`/**
 * ${name} - Google Apps Script Web App
 * Deploy as: Deploy → New Deployment → Web app
 */

function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('${name}');
}

function doPost(e) {
  return ContentService
    .createTextOutput(JSON.stringify({status: 'ok', data: e.parameter}))
    .setMimeType(ContentService.MimeType.JSON);
}` :
`/**
 * ${name} - Google Apps Script Project
 */

function myFunction() {
  Logger.log('Hello from ${name}!');
}`
      }];
      
      if (asWebApp) {
        files.push({
          name: 'Index.html',
          type: 'HTML',
          source: `<!DOCTYPE html>
<html>
  <head>
    <base target="_top">
    <style>
      body { font-family: system-ui, sans-serif; padding: 20px; }
      h1 { color: #1a73e8; }
    </style>
  </head>
  <body>
    <h1>${name}</h1>
    <p>Your web app is running!</p>
    <button onclick="google.script.run.withSuccessHandler(function(msg){alert(msg)}).myFunction()">
      Click me
    </button>
  </body>
</html>`
        });
      }
      
      if (data.project && data.project.scriptId) {
        await api.post(`/api/google/projects/${data.project.scriptId}/content`, { files });
        await gsRefresh();
        gsSelectProject(data.project.scriptId);
      }
    } else {
      showToast(`⚠ ${data.message}`, 'error');
    }
  } catch (err) {
    showToast(`⚠ ${err.message}`, 'error');
  }
}
