function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span class="toast-icon">${icons[type] || icons.info}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(20px)'; setTimeout(() => toast.remove(), 300); }, 3500);
}

function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function formatDate(iso) {
  if (!iso) return '-';
  try { return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }); }
  catch { return iso; }
}

function timeAgo(iso) {
  if (!iso) return '-';
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function statusColor(status) {
  const s = (status || '').toLowerCase();
  if (['online', 'healthy', 'active', 'pass', 'ok'].includes(s)) return { bg: 'var(--green-dim)', dot: 'var(--green)', text: 'var(--green)' };
  if (['warning', 'warn', 'degraded'].includes(s)) return { bg: 'var(--yellow-dim)', dot: 'var(--yellow)', text: 'var(--yellow)' };
  if (['offline', 'error', 'fail', 'down'].includes(s)) return { bg: 'var(--red-dim)', dot: 'var(--red)', text: 'var(--red)' };
  return { bg: 'var(--bg-card)', dot: 'var(--text-muted)', text: 'var(--text-muted)' };
}

function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const isCollapsed = sidebar.classList.toggle('collapsed');
  localStorage.setItem('sidebarCollapsed', isCollapsed);
  const icon = sidebar.querySelector('.toggle-icon');
  if (icon) {
    icon.style.transform = isCollapsed ? 'rotate(180deg)' : '';
  }
}

function toggleTheme() {
  const html = document.documentElement;
  const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
}

function loadTheme() {
  const saved = localStorage.getItem('theme');
  if (saved) document.documentElement.setAttribute('data-theme', saved);
  const sidebarCollapsed = localStorage.getItem('sidebarCollapsed');
  if (sidebarCollapsed === 'true') {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.add('collapsed');
    const icon = sidebar.querySelector('.toggle-icon');
    if (icon) icon.style.transform = 'rotate(180deg)';
  }
}

function showModal(title, bodyHtml, footerHtml) {
  const container = document.getElementById('modalContainer');
  container.innerHTML = `
    <div class="modal-overlay" onclick="if(event.target===this)closeModal()">
      <div class="modal">
        <div class="modal-header">
          <span class="modal-title">${title}</span>
          <button class="modal-close" onclick="closeModal()">✕</button>
        </div>
        <div class="modal-body">${bodyHtml}</div>
        ${footerHtml ? `<div class="modal-footer">${footerHtml}</div>` : ''}
      </div>
    </div>
  `;
}

function closeModal() {
  document.getElementById('modalContainer').innerHTML = '';
}

/**
 * Central navigation configuration — single source of truth for the sidebar,
 * window titles, breadcrumbs, route availability, and command search.
 *
 * Each route item carries:
 *   page        (required)  hash key used in the router
 *   title       (required)  top bar title
 *   breadcrumb  (required)  top bar breadcrumb
 *   icon        (required)  emoji shown next to the label in the sidebar
 *   label       (required)  sidebar label (may differ from title)
 *   enabled     (default true)    if false, route shows a "Coming soon" empty state
 *   hidden      (default false)   if true, route is routable but NOT shown in the sidebar
 *   badgeId     (optional)        DOM id of a sidebar badge element to preserve
 *
 * Visible sidebar groups live in `groups`. Routes that should remain
 * reachable (via direct hash or command search) but not appear in the
 * sidebar live in `hiddenRoutes`. External links live in `external`.
 */
const NAV_CONFIG = {
  groups: [
    {
      label: '🏠 Home',
      items: [
        { page: 'dashboard',       icon: '◉',  label: 'Dashboard',       title: 'Dashboard',       breadcrumb: 'Overview' },
        { page: 'tools',           icon: '🔗', label: 'My Tools',        title: 'My Tools',        breadcrumb: 'NotebookLM, Cron, KB, Hermes & more' },
        { page: 'chat',            icon: '💬', label: 'AI Chat',         title: 'AI Chat',         breadcrumb: 'Multi-agent terminal' },
        { page: 'morning-briefing', icon: '🌅', label: 'Morning Briefing', title: '🌅 Morning Briefing', breadcrumb: 'Daily urology briefing — call, evals, events' },
        { page: 'calendar',         icon: '📅', label: 'Calendar',          title: '📅 Calendar of Events', breadcrumb: 'Vacation dates, call schedule & department events' },
        { page: 'system-overview', icon: '🏥', label: 'System Overview', title: '🏥 System Overview', breadcrumb: 'Central services, cron health & monitoring' },
        { page: 'compliance',      icon: '📊', label: 'Compliance',      title: '📊 Compliance Dashboard', breadcrumb: 'Attendance, evals & GME — color-coded metrics' },
        { page: 'quick-actions',   icon: '⚡', label: 'Quick Actions',   title: '⚡ Quick Actions', breadcrumb: 'One-click operations for common workflows' },
        { page: 'notifications',   icon: '🔔', label: 'Notifications',   title: '🔔 Notification Feed', breadcrumb: 'Cron, eval & system events feed' },
        { page: 'images-to-pdf',   icon: '📄', label: 'Images → PDF',    title: '🖼️ Images → PDF',    breadcrumb: 'Combine images into a single PDF' },
      ],
    },
    {
      label: '💼 Work',
      items: [
        // Urology-specific pages
        { page: 'unified-dashboard',      icon: '🏥', label: 'Unified Dashboard',      title: '🏥 Unified Dashboard',      breadcrumb: 'Montefiore Urology — all systems in one view' },
        { page: 'platforms',             icon: '🔌', label: 'Platforms',             title: '🔌 Platform Connections', breadcrumb: 'Connected systems — SCL, Reimbursement, Qgenda' },
        { page: 'manager',                icon: '📋', label: 'Manager Command Center', title: '📋 Manager Command Center', breadcrumb: 'Schedule, coverage & approvals at a glance' },
        { page: 'oncall',                 icon: '📅', label: 'Call Schedule',          title: 'Call Schedule',             breadcrumb: 'Weekly resident call rotation' },
        { page: 'grand-rounds',           icon: '📋', label: 'Grand Rounds',           title: 'Grand Rounds',              breadcrumb: 'Urology academic schedule & Outlook invites' },
        { page: 'grand-rounds-attendance', icon: '📊', label: 'Attendance',            title: '📊 Grand Rounds Attendance', breadcrumb: 'Faculty compliance tracking & reports' },
        { page: 'call-schedule-pdf',      icon: '📄', label: 'Call Schedule PDF',      title: '📄 Call Schedule PDF',      breadcrumb: 'Generate and email call schedule PDFs' },
        { page: 'gme-tracker',            icon: '💰', label: 'GME Tracker',            title: 'GME Reimbursement Tracker', breadcrumb: 'Resident education fund management' },
        { page: 'eval-portal',            icon: '📝', label: 'Eval Portal',            title: '📝 Eval Portal',            breadcrumb: 'CMS evaluation forms — track & remind' },
        { page: 'eval-dashboard',         icon: '📊', label: 'Eval Dashboard',        title: '📊 Eval Dashboard',        breadcrumb: 'Completion stats, charts, and activity feed' },
        { page: 'gme-detail',             icon: '📈', label: 'GME Deep Dive',          title: '📈 GME Deep Dive',          breadcrumb: 'Resident fund usage breakdown with charts' },
        { page: 'staff-schedule',         icon: '👥', label: 'Staff Schedule',         title: '👥 Staff Schedule',         breadcrumb: 'NP/PA/coordinator schedules by hospital' },
        { page: 'pdf-archive',            icon: '📄', label: 'PDF Archive',            title: '📄 PDF Archive',            breadcrumb: 'All generated PDFs in one place' },
        { page: 'voice-commands',         icon: '🎤', label: 'Voice Commands',         title: '🎤 Voice Commands',         breadcrumb: 'Telegram report generator cheat sheet' },
        // General work pages
        { page: 'kanban',    icon: '📌', label: 'Kanban Board', title: 'Kanban Board', breadcrumb: 'Multi-agent task management' },
        { page: 'goals',     icon: '🎯', label: 'Goals',        title: 'Goals',        breadcrumb: 'Project targets and progress' },
        { page: 'journal',   icon: '📓', label: 'Journal',      title: 'Journal',      breadcrumb: 'Daily entries and notes' },
        { page: 'drive-sync', icon: '📁', label: 'Drive Sync',  title: 'Drive Sync',   breadcrumb: 'Location-roster files from Drive' },
        { page: 'reports',   icon: '📄', label: 'Report Center', title: 'Report Center', breadcrumb: 'Generate & deliver reports' },
      ],
    },
    {
      label: '🤖 Agents',
      items: [
        { page: 'skills',        icon: '⚡', label: 'Skills',        title: 'Skills Hub',      breadcrumb: 'Browse & execute skills',    badgeId: 'skillCount' },
        { page: 'memory',        icon: '🧠', label: 'Memory',        title: 'Memory',          breadcrumb: 'Shared brain context' },
        { page: 'smart-router',  icon: '🧭', label: 'Smart Router',  title: 'Smart Router',    breadcrumb: 'Task routing intelligence' },
        { page: 'omniroute',     icon: '🌐', label: 'OmniRoute',     title: '🌐 OmniRoute AI Gateway', breadcrumb: 'Free LLM routing · 237 providers · Claude Code integration' },
        { page: 'agent-health',  icon: '🏥', label: 'Agent Health',  title: 'Agent Health',    breadcrumb: 'Real-time agent monitoring', badgeId: 'agentHealthCount' },
        { page: 'health',        icon: '📈', label: 'System Health', title: '🏥 System Health', breadcrumb: 'Central services & cron health monitor' },
        { page: 'ai-builder',    icon: '🤖', label: 'AI Builder',    title: 'AI Builder',      breadcrumb: 'Google Antigravity — build with Gemini' },
        // Development tools
        { page: 'claude-code',          icon: '🤖', label: 'Claude Code',          title: '🤖 Claude Code',          breadcrumb: 'Free LLM terminal — powered by OmniRoute (Groq + Z.AI)' },
        { page: 'vs-coder',            icon: '💻', label: 'VS Coder',            title: '💻 VS Coder',            breadcrumb: 'Full code editor — edit, run, commit' },
        { page: 'google-studio',       icon: '🔷', label: 'Google Studio',       title: 'Google Dev Studio',      breadcrumb: 'Apps Script editor & project manager' },
        { page: 'prompt-tools-image',  icon: '🖼️', label: 'Image Builder',       title: '🖼️ Image Prompt Builder', breadcrumb: 'Build professional image prompts visually' },
        { page: 'prompt-tools-video',  icon: '🎬', label: 'Video Builder',       title: '🎬 Video Prompt Builder', breadcrumb: 'Build professional video prompts visually' },
        { page: 'image-gallery',       icon: '🎨', label: 'Image Gallery',       title: '🎨 Image Gallery',       breadcrumb: 'Browse design mockups and generated images' },
        { page: 'file-browser',        icon: '🗂',  label: 'File Browser',        title: '🗂 File Browser',        breadcrumb: 'Browse and view workspace files' },
        { page: 'script-runner',       icon: '⚙️', label: 'Script Runner',       title: '⚙️ Script Runner',       breadcrumb: 'Run workspace scripts from the dashboard' },
      ],
    },
    {
      label: '📋 Operations',
      items: [
        { page: 'scheduler', icon: '⏱', label: 'Scheduler', title: 'Scheduler', breadcrumb: 'Automated workflows' },
        { page: 'audit',     icon: '📋', label: 'Audit',     title: 'Audit Log', breadcrumb: 'System activity trail' },
        { page: 'cost',      icon: '💰', label: 'Cost Analytics', title: 'Cost Analytics', breadcrumb: 'Usage & spending' },
        { page: 'backups',   icon: '💾', label: 'Backups',   title: 'Backups',   breadcrumb: 'Disaster recovery' },
      ],
    },
    {
      label: '⚙️ Manage',
      items: [
        { page: 'people',          icon: '👥', label: 'People',          title: 'People',          breadcrumb: 'Contact directory', enabled: true },
        { page: 'resident-roster', icon: '🩺', label: 'Resident Roster', title: '🩺 Resident Roster', breadcrumb: 'Urology residents contact info and status' },
        { page: 'contacts',        icon: '📇', label: 'CRM',             title: 'CRM',             breadcrumb: 'Contact management system' },
        { page: 'crm-audit',       icon: '🔍', label: 'CRM Audit',       title: 'CRM Audit',       breadcrumb: 'Access log for CRM operations' },
        { page: 'email-templates', icon: '📋', label: 'Email Templates', title: 'Email Templates', breadcrumb: 'Pre-built email templates for quick sending' },
        { page: 'conference-email', icon: '📤', label: 'One-Click Resend', title: '📤 One-Click Email Resend', breadcrumb: 'Grand Rounds & Conference invite resend' },
        { page: 'telegram',        icon: '✈️', label: 'Telegram',        title: 'Telegram Sessions', breadcrumb: 'Messaging conversations from state.db', badgeId: 'telegramCount' },
        { page: 'telegram-logs',   icon: '📋', label: 'Telegram Logs',   title: '✈️ Telegram Logs', breadcrumb: 'Recent messages, gateway status & log viewer' },
        { page: 'prompts',         icon: '📝', label: 'Prompts',         title: 'Prompt Library',  breadcrumb: 'Reusable templates' },
        { page: 'standards',       icon: '📐', label: 'Standards',       title: 'Standards',       breadcrumb: 'Project conventions' },
        { page: 'plugins',         icon: '🔌', label: 'Plugins',         title: 'Plugin Registry', breadcrumb: 'Manage plugins' },
        { page: 'pin-manager',     icon: '🔑', label: 'PIN Manager',     title: 'PIN Manager',     breadcrumb: 'Secure PIN management' },
        { page: 'settings',        icon: '⚙',  label: 'Settings',        title: 'Settings',        breadcrumb: 'Configuration' },
      ],
    },
  ],

  // Hidden but routable — reachable via direct hash + command search, not shown in sidebar.
  hiddenRoutes: [
    { page: 'learning-analytics', icon: '📊', label: 'Learning Analytics', title: 'Learning Analytics', breadcrumb: 'Skill improvement tracking', hidden: true },
    { page: 'session-replay',     icon: '🔄', label: 'Session Replay',     title: 'Session Replay',     breadcrumb: 'Conversation history playback', hidden: true },
    { page: 'setup-wizard',       icon: '🚀', label: 'Setup Wizard',       title: 'Setup Wizard',       breadcrumb: 'Guided configuration', hidden: true },
    { page: 'user',               icon: '👤', label: 'User Dashboard',     title: '👤 User Dashboard', breadcrumb: 'Resident self-service — EZ ID lookup', hidden: true },
  ],

  // External links — never get the `data-page` attribute, never become active.
  external: [
    { page: 'vscode', href: 'https://code.visualstudio.com/', icon: '💻', label: 'VS Code' },
    { page: 'overlay-designer', href: 'https://charter-constraints-civil-loved.trycloudflare.com/designer/', icon: '🎨', label: 'Overlay Designer' },
    { page: 'video-editor', href: 'https://charter-constraints-civil-loved.trycloudflare.com', icon: '✂️', label: 'Video Editor' },
  ],
};

/** Flatten all routes (groups + hidden) into a lookup map. */
function _allRoutes() {
  const out = {};
  NAV_CONFIG.groups.forEach(g => g.items.forEach(r => { out[r.page] = r; }));
  NAV_CONFIG.hiddenRoutes.forEach(r => { out[r.page] = r; });
  return out;
}

/** Page titles, derived from NAV_CONFIG for backward compatibility. */
const PAGE_TITLES = (() => {
  const titles = {};
  Object.values(_allRoutes()).forEach(r => {
    titles[r.page] = { title: r.title, breadcrumb: r.breadcrumb };
  });
  return titles;
})();

/** Look up a route by page key across visible groups, hidden routes, and external. */
function getNavRoute(page) {
  if (!page) return undefined;
  const routes = _allRoutes();
  if (routes[page]) return routes[page];
  const ext = NAV_CONFIG.external.find(e => e.page === page);
  return ext ? { page: ext.page, title: ext.label, breadcrumb: '', external: true } : undefined;
}

/** Build the grouped sidebar HTML string from NAV_CONFIG. */
function buildSidebarNav() {
  const groupsHtml = NAV_CONFIG.groups.map(group => {
    const itemsHtml = group.items.map(item => {
      const disabled = item.enabled === false ? ' nav-item-disabled' : '';
      const badge = item.badgeId
        ? `<span class="nav-badge" id="${item.badgeId}">0</span>`
        : '';
      return `<a href="#${item.page}" class="nav-item${disabled}" data-page="${item.page}">` +
             `<span class="nav-icon">${item.icon}</span>` +
             `<span class="nav-label">${item.label}</span>` +
             badge +
             `</a>`;
    }).join('');
    return `<div class="sidebar-section">` +
           `<div class="sidebar-section-label">${group.label}</div>` +
           itemsHtml +
           `</div>`;
  }).join('');

  const externalHtml = NAV_CONFIG.external.map(link =>
    `<a href="${link.href}" class="nav-item nav-external" target="_blank" rel="noopener">` +
    `<span class="nav-icon">${link.icon}</span>` +
    `<span class="nav-label">${link.label}</span>` +
    `<span class="nav-icon nav-external-glyph">↗</span>` +
    `</a>`
  ).join('');

  return groupsHtml + (externalHtml ? `<div class="sidebar-external">${externalHtml}</div>` : '');
}

/** Inject buildSidebarNav() into the nav container (called early in DOMContentLoaded). */
function renderSidebar() {
  const nav = document.getElementById('sidebarNav');
  if (nav) nav.innerHTML = buildSidebarNav();
}

/** Command-style global search over enabled NAV_CONFIG routes. */
function handleGlobalSearch(value) {
  const resultsEl = document.getElementById('searchResults');
  if (!resultsEl) return;
  if (!value || value.length < 2) { resultsEl.innerHTML = ''; resultsEl.style.display = 'none'; return; }

  const q = value.toLowerCase();
  const routes = Object.values(_allRoutes());
  const matches = routes
    .filter(r => r.enabled !== false)
    .filter(r => (r.label || '').toLowerCase().includes(q) || (r.title || '').toLowerCase().includes(q))
    .slice(0, 8);

  if (matches.length === 0) {
    resultsEl.innerHTML = `<div class="search-result-empty">No pages match "${escapeHtml(value)}"</div>`;
    resultsEl.style.display = 'block';
    return;
  }

  resultsEl.innerHTML = matches.map((r, i) =>
    `<div class="search-result${i === 0 ? ' search-result-active' : ''}" data-page="${r.page}">` +
    `<span class="search-result-icon">${r.icon}</span>` +
    `<span class="search-result-label">${escapeHtml(r.label)}</span>` +
    (r.hidden ? '<span class="search-result-flag">hidden</span>' : '') +
    `</div>`
  ).join('');
  resultsEl.style.display = 'block';

  resultsEl.querySelectorAll('.search-result').forEach(el => {
    el.addEventListener('click', () => {
      const page = el.getAttribute('data-page');
      resultsEl.innerHTML = ''; resultsEl.style.display = 'none';
      const searchInput = document.getElementById('globalSearch');
      if (searchInput) searchInput.value = '';
      navigate(page);
    });
  });
}

/** Enter-key handling for the search input — navigates to top match. */
function handleGlobalSearchKeydown(ev) {
  const resultsEl = document.getElementById('searchResults');
  if (!resultsEl || resultsEl.style.display === 'none' || resultsEl.style.display === '') return;
  if (ev.key === 'Enter') {
    const top = resultsEl.querySelector('.search-result[data-page]');
    if (top) top.click();
    ev.preventDefault();
  } else if (ev.key === 'Escape') {
    resultsEl.innerHTML = ''; resultsEl.style.display = 'none';
  }
}

function renderSkeleton(count = 3) {
  return Array(count).fill(0).map(() =>
    `<div class="card"><div class="skeleton" style="height:20px;width:60%;margin-bottom:12px"></div><div class="skeleton" style="height:14px;width:90%;margin-bottom:8px"></div><div class="skeleton" style="height:14px;width:40%"></div></div>`
  ).join('');
}



async function loadHealth() {
  const widget = document.getElementById('healthWidget');
  if (!widget) return;
  widget.innerHTML = '<span style="color:var(--text-muted)">Checking...</span>';
  try {
    const data = await fetch('/api/health/full').then(r => r.json());
    const services = data.services || {};
    const names = Object.keys(services);
    const allOk = names.length > 0 && names.every(n => services[n].ok);
    widget.innerHTML = names.map(n => {
      const ok = services[n].ok;
      const color = ok ? 'var(--green)' : 'var(--red)';
      const icon = ok ? '🟢' : '🔴';
      return `<span title="${n}: ${ok ? 'OK' : services[n].error || 'down'}" style="display:inline-flex;align-items:center;gap:4px;cursor:pointer;color:var(--text)" onclick="navigate('health')">${icon}<span style="color:${color};font-weight:600">${n}</span></span>`;
    }).join('');
    widget.onclick = null;
  } catch (err) {
    widget.innerHTML = `<span style="color:var(--red);cursor:pointer" onclick="navigate('health')">⚠️ Health unavailable</span>`;
  }
}
