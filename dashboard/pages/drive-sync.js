// Drive Sync — Dashboard Page
// Sync Now button + freshness table for location roster files
async function renderDriveSync() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">Drive Sync</h1>
        <p class="page-subtitle">Location-roster files pulled from Google Drive</p>
      </div>
      <button class="btn btn-primary" id="syncNowBtn" onclick="syncDriveNow()">Sync Now</button>
    </div>
    <div id="statusMsg"></div>
    <div id="driveTable"><div class="loading"><div class="loading-spinner"></div></div></div>
  `;
  await refreshDriveTable();
}

async function syncDriveNow() {
  const btn = document.getElementById('syncNowBtn');
  btn.disabled = true;
  btn.textContent = 'Syncing...';
  const status = document.getElementById('statusMsg');
  status.innerHTML = '';

  try {
    const result = await api.syncDrive();
    if (result.success) {
      showToast(`Done: ${result.synced || 0} synced, ${result.skipped || 0} skipped`, 'success');
    } else {
      status.innerHTML = `<div class="alert alert-warning">${result.reason || 'Sync failed'}: ${result.action || ''} ${result.error || ''}</div>`;
    }
  } catch (err) {
    status.innerHTML = `<div class="alert alert-error">Error: ${err.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Sync Now';
    await refreshDriveTable();
  }
}

async function refreshDriveTable() {
  const container = document.getElementById('driveTable');
  try {
    const data = await api.getDriveSyncStatus();
    const files = data.files || [];

    if (files.length === 0) {
      container.innerHTML = `<div class="empty-state">
        <div class="empty-state-icon">📁</div>
        <div class="empty-state-title">No files synced yet</div>
        <div class="empty-state-desc">Click "Sync Now" to pull roster files from Drive</div>
      </div>`;
      return;
    }

    const now = new Date();
    container.innerHTML = `
      <div class="table-wrapper">
        <table>
          <thead><tr>
            <th>File</th>
            <th>Last Synced</th>
            <th>Age</th>
            <th>Parse Status</th>
          </tr></thead>
          <tbody>
            ${files.map(f => `
              <tr>
                <td><strong>${esc(f.name)}</strong></td>
                <td style="font-size:12px;color:var(--text-muted)">${formatDateStr(f.last_synced) || 'Never'}</td>
                <td>${ageBadge(f.age_days)}</td>
                <td>${parseBadge(f.parse_status)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
      <p style="font-size:11px;color:var(--text-muted);margin-top:8px">${data.total_files} file(s) tracked</p>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert alert-error">Could not load sync status: ${err.message}</div>`;
  }
}

function esc(s) { return (s || '').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

function formatDateStr(iso) {
  if (!iso) return 'Never';
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
}

function ageBadge(days) {
  if (days == null) return '<span class="badge badge-warning">Unknown</span>';
  if (days < 0.05) return '<span class="badge badge-success">Just now</span>';
  if (days < 1) return `<span class="badge badge-success">${days * 24}h ago</span>`;
  if (days < 3) return `<span class="badge badge-success">${days}d ago</span>`;
  if (days < 7) return `<span class="badge badge-warning">${days}d ago</span>`;
  return `<span class="badge badge-error">${days}d ago</span>`;
}

function parseBadge(status) {
  switch (status) {
    case 'ok': return '<span class="badge badge-success">Parsed</span>';
    case 'skipped': return '<span class="badge badge-warning">Not parsed</span>';
    case 'error': return '<span class="badge badge-error">Error</span>';
    default: return `<span class="badge">${esc(status)}</span>`;
  }
}
