async function renderNotifications() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">Notification Feed</div>
        <div class="page-subtitle">Cron completions, eval reminders, system events — all in one place</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderNotifications()">↻ Refresh</button>
        <button class="btn btn-primary" onclick="clearNotifications()">✕ Clear All</button>
      </div>
    </div>
    <div class="nt-controls">
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        <button class="nt-filter active" data-filter="all" onclick="filterNotif('all',this)">All</button>
        <button class="nt-filter" data-filter="cron" onclick="filterNotif('cron',this)">Cron</button>
        <button class="nt-filter" data-filter="eval" onclick="filterNotif('eval',this)">Evals</button>
        <button class="nt-filter" data-filter="system" onclick="filterNotif('system',this)">System</button>
        <button class="nt-filter" data-filter="telegram" onclick="filterNotif('telegram',this)">Telegram</button>
      </div>
    </div>
    <div id="ntFeed" class="nt-feed"><div class="loading"><div class="loading-spinner"></div><span>Loading feed...</span></div></div>
    <style>
      .nt-controls { margin-top:12px; padding:8px 12px; background:var(--bg-card); border-radius:var(--radius-md); border:1px solid var(--border); }
      .nt-filter { padding:4px 12px; border-radius:12px; border:1px solid var(--border); background:transparent; color:var(--text); font-size:11px; cursor:pointer; }
      .nt-filter.active { background:var(--primary); border-color:var(--primary); color:#fff; }
      .nt-feed { margin-top:8px; }
      .nt-item { display:flex; gap:10px; padding:10px 14px; background:var(--bg-card); border-radius:var(--radius-md); border:1px solid var(--border); margin-bottom:6px; align-items:start; transition:opacity 0.2s; }
      .nt-item .icon { font-size:16px; width:24px; text-align:center; flex-shrink:0; margin-top:1px; }
      .nt-item .body { flex:1; min-width:0; }
      .nt-item .title { font-size:13px; font-weight:500; }
      .nt-item .desc { font-size:11px; color:var(--text-muted); margin-top:2px; }
      .nt-item .time { font-size:10px; color:#636e72; flex-shrink:0; white-space:nowrap; }
      .nt-empty { padding:32px; text-align:center; color:var(--text-muted); font-size:13px; }
    </style>
  `;
  loadNotifications();
}

let _allNotifs = [];

async function loadNotifications() {
  try {
    const res = await fetch('/api/notifications').then(r => r.json()).catch(() => ({notifications: []}));
    stampPage(res);
    const notifs = res.notifications || [];
    _allNotifs = notifs;
    renderNotifFeed('all');
  } catch(e) {
    document.getElementById('ntFeed').innerHTML = `<div class="nt-empty">! ${escapeHtml(e.message)}</div>`;
  }
}

function renderNotifFeed(filter) {
  const feed = document.getElementById('ntFeed');
  const filtered = filter === 'all' ? _allNotifs : _allNotifs.filter(n => n.type === filter);
  if (filtered.length === 0) {
    feed.innerHTML = '<div class="nt-empty">No notifications</div>';
    return;
  }
  feed.innerHTML = filtered.map(n => `
    <div class="nt-item" data-type="${n.type}">
      <div class="icon">${n.icon}</div>
      <div class="body">
        <div class="title">${escapeHtml(n.title)}</div>
        <div class="desc">${escapeHtml(n.desc || '')}</div>
      </div>
      <div class="time">${n.time || ''}</div>
    </div>
  `).join('');
}

function filterNotif(filter, btn) {
  document.querySelectorAll('.nt-filter').forEach(el => el.classList.remove('active'));
  btn.classList.add('active');
  renderNotifFeed(filter);
}

function clearNotifications() {
  _allNotifs = [];
  renderNotifFeed('all');
  showToast('Notifications cleared', 'info');
}
