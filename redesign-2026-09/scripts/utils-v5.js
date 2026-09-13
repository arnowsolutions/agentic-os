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
  // Sidebar zones (v3, 2026-09-12 redesign). Zones keep groups SMALL by moving
  // secondary destinations into sub-sections that collapse by default.
  // Everything remains routable: merged/secondary pages live in `hiddenRoutes`.
  groups: [
    {
      label: 'Home',
      items: [
        { page: 'dashboard',       icon: '▸', label: 'Dashboard',        title: 'Dashboard',         breadcrumb: 'Launchpad & system pulse' },
        { page: 'tools',           icon: '▸', label: 'My Tools',         title: 'My Tools',          breadcrumb: 'NotebookLM, Cron, KB & services' },
      ],
      sections: [
        {
          label: 'Daily', collapsed: false, items: [
            { page: 'chat',            icon: '▸', label: 'AI Chat',          title: 'AI Chat',          breadcrumb: 'Multi-agent terminal' },
            { page: 'calendar',        icon: '▸', label: 'Calendar',         title: 'Calendar of Events', breadcrumb: 'Vacation, call schedule & events' },
            { page: 'morning-briefing',icon: '▸', label: 'Briefings & Cron', title: 'Briefings & Cron', breadcrumb: 'Outgoing briefs, cron jobs & scheduled deliveries' },
            { page: 'quick-actions',   icon: '▸', label: 'Quick Actions',    title: 'Quick Actions',    breadcrumb: 'One-click workflow operations' },
            { page: 'notifications',   icon: '▸', label: 'Notifications',    title: 'Notification Feed', breadcrumb: 'Cron, eval & system events' },
          ]
        },
      ],
    },
    {
      label: 'Work',
      items: [
        { page: 'unified-dashboard', icon: '▸', label: 'Unified Dashboard', title: 'Unified Dashboard', breadcrumb: 'Montefiore Urology — all systems' },
        { page: 'manager',           icon: '▸', label: 'Command Center',    title: 'Command Center',    breadcrumb: 'Schedule, coverage & approvals' },
        { page: 'manager-command-center', icon: '▸', label: 'Staff Command Center', title: 'Staff Command Center', breadcrumb: 'Tier 2 — NPs & staff leads' },
        { page: 'schedule-suite',    icon: '▸', label: 'Schedule Suite',    title: 'Schedule Suite',    breadcrumb: 'Call schedule · staff schedules · PDF export' },
        { page: 'mass-email',        icon: '▸', label: 'Mass Email & Invites', title: 'Mass Email & Invites', breadcrumb: 'Grand Rounds · Sub-I · Chief Meetings · Resend' },
        { page: 'compliance-suite',  icon: '▸', label: 'Compliance Suite',  title: 'Compliance Suite',  breadcrumb: 'Compliance · evals · GME tracking' },
      ],
      sections: [
        {
          label: 'Rotation ops', collapsed: true, items: [
            { page: 'system-overview',        icon: '▸', label: 'System Overview',  title: 'System Overview',  breadcrumb: 'Central services, cron health & monitoring' },
            { page: 'email-send-log',         icon: '▸', label: 'Email Log',        title: 'Email Send Log',   breadcrumb: 'Invite tracking — real vs test' },
            { page: 'pdf-archive',            icon: '▸', label: 'PDF Archive',      title: 'PDF Archive',      breadcrumb: 'Generated PDFs' },
            { page: 'platforms',              icon: '▸', label: 'Platforms',        title: 'Platform Connections', breadcrumb: 'SCL, Reimbursement, Qgenda' },
            { page: 'calendar-invites',     icon: '▸', label: 'Calendar Invites',  title: 'Calendar Invites',  breadcrumb: 'Outlook invite builder & schedule editor' },
          ]
        },
        {
          label: 'Collection & comms', collapsed: true, items: [
            { page: 'voice-commands',    icon: '▸', label: 'Voice Commands',   title: 'Voice Commands',    breadcrumb: 'Telegram report generator' },
            { page: 'telegram',          icon: '▸', label: 'Telegram Sessions', title: 'Telegram Sessions', breadcrumb: 'Messages from state.db', badgeId: 'telegramCount' },
            { page: 'telegram-logs',     icon: '▸', label: 'Telegram Logs',    title: 'Telegram Logs',     breadcrumb: 'Gateway status & log viewer' },
            { page: 'email-templates',   icon: '▸', label: 'Email Templates',  title: 'Email Templates',   breadcrumb: 'Pre-built templates' },
            { page: 'grand-rounds-hub',  icon: '▸', label: 'Grand Rounds Hub', title: 'Grand Rounds Hub',  breadcrumb: 'Events & faculty attendance' },
            { page: 'subi-exit-interviews', icon: '▸', label: 'Sub-I Exit Interviews', title: 'Sub-I Exit Interviews', breadcrumb: 'Interview scheduling' },
            { page: 'resident-letters',  icon: '▸', label: 'Resident Letters', title: 'Resident Letters',  breadcrumb: 'Letter generator' },
          ]
        },
      ],
    },
    {
      label: 'Build',
      items: [
        { page: 'skills',         icon: '▸', label: 'Skills',       title: 'Skills Hub',        breadcrumb: 'Browse & execute skills', badgeId: 'skillCount' },
        { page: 'claude-code',    icon: '▸', label: 'Claude Code',  title: 'Claude Code',       breadcrumb: 'Free LLM terminal (OmniRoute)' },
        { page: 'omniroute',      icon: '▸', label: 'OmniRoute',    title: 'OmniRoute AI Gateway', breadcrumb: '237 providers · free LLM routing' },
        { page: 'ai-builder-suite', icon: '▸', label: 'AI Builder Suite', title: 'AI Builder Suite', breadcrumb: 'Gemini builder · image & video prompts · gallery' },
        { page: 'workspace-suite',  icon: '▸', label: 'Workspace',        title: 'Workspace',        breadcrumb: 'Files · scripts · VS Coder · Apps Script' },
        { page: 'social-media-hub', icon: '▸', label: 'Social Media Hub', title: 'Social Media Hub', breadcrumb: '42+ integrated social skills' },
      ],
      sections: [
        {
          label: 'Work tracking', collapsed: true, items: [
            { page: 'scheduler',     icon: '▸', label: 'Scheduler',     title: 'Scheduler',     breadcrumb: 'Automated workflows' },
            { page: 'kanban',        icon: '▸', label: 'Kanban',        title: 'Kanban Board',  breadcrumb: 'Task management' },
            { page: 'goals',         icon: '▸', label: 'Goals',         title: 'Goals',         breadcrumb: 'Project targets & progress' },
            { page: 'journal',       icon: '▸', label: 'Journal',       title: 'Journal',       breadcrumb: 'Daily entries & notes' },
            { page: 'meeting-reports', icon: '▸', label: 'Meeting Reports', title: 'Meeting Reports', breadcrumb: 'Transcribe + analyze meetings into reports' },
            { page: 'reports',       icon: '▸', label: 'Report Center', title: 'Report Center', breadcrumb: 'Generate & deliver reports' },
            { page: 'drive-sync',    icon: '▸', label: 'Drive Sync',    title: 'Drive Sync',    breadcrumb: 'Location-roster files' },
            { page: 'images-to-pdf', icon: '▸', label: 'Images to PDF', title: 'Images to PDF', breadcrumb: 'Combine images into a single PDF' },
          ]
        },
      ],
    },
    {
      label: 'System',
      items: [
        { page: 'agent-health', icon: '▸', label: 'Agent Health',  title: 'Agent Health',  breadcrumb: 'Real-time agent monitoring', badgeId: 'agentHealthCount' },
        { page: 'health',       icon: '▸', label: 'System Health', title: 'System Health', breadcrumb: 'Central services & cron health' },
        { page: 'operations',   icon: '▸', label: 'Operations',    title: 'Operations',    breadcrumb: 'System metrics, agents & recent activity' },
        { page: 'cost',         icon: '▸', label: 'Cost Analytics', title: 'Cost Analytics', breadcrumb: 'Usage & spending' },
        { page: 'settings',     icon: '▸', label: 'Settings',      title: 'Settings',      breadcrumb: 'Configuration' },
      ],
      sections: [
        {
          label: 'Admin', collapsed: true, items: [
            { page: 'memory',        icon: '▸', label: 'Memory',        title: 'Memory',        breadcrumb: 'Shared brain context' },
            { page: 'smart-router',  icon: '▸', label: 'Smart Router',  title: 'Smart Router',  breadcrumb: 'Task routing intelligence' },
            { page: 'crm-suite',     icon: '▸', label: 'CRM',           title: 'CRM',           breadcrumb: 'People, contacts, residents & audit' },
            { page: 'prompts',       icon: '▸', label: 'Prompts',       title: 'Prompt Library', breadcrumb: 'Reusable templates' },
            { page: 'standards',     icon: '▸', label: 'Standards',     title: 'Standards',     breadcrumb: 'Project conventions' },
            { page: 'plugins',       icon: '▸', label: 'Plugins',       title: 'Plugin Registry', breadcrumb: 'Manage plugins' },
            { page: 'pin-manager',   icon: '▸', label: 'PIN Manager',   title: 'PIN Manager',   breadcrumb: 'Secure PIN management' },
            { page: 'audit',         icon: '▸', label: 'Audit Log',     title: 'Audit Log',     breadcrumb: 'System activity trail' },
            { page: 'backups',       icon: '▸', label: 'Backups',       title: 'Backups',       breadcrumb: 'Disaster recovery' },
            { page: 'tasks',         icon: '▸', label: 'Task List',     title: 'Task List',     breadcrumb: 'Your task list' },
            { page: 'email-groups',  icon: '▸', label: 'Email Groups',  title: 'Email Groups',  breadcrumb: 'Recipient groups' },
            { page: 'distribution',  icon: '▸', label: 'Distribution Lists', title: 'Distribution Lists', breadcrumb: 'Faculty, residents, supervisors' },
            { page: 'data-gaps',     icon: '▸', label: 'Data Gaps',     title: 'Data Gaps',     breadcrumb: 'Source coverage audit' },
            { page: 'colophon',      icon: '▸', label: 'Colophon',      title: 'Colophon',      breadcrumb: 'Build ledger & production notes' },
          ]
        },
      ],
    },
  ],

  // Hidden but routable — reachable via direct hash + command search.
  hiddenRoutes: [
    { page: 'learning-analytics', icon: '▸', label: 'Learning Analytics', title: 'Learning Analytics', breadcrumb: 'Skill improvement tracking', hidden: true },
    { page: 'session-replay',     icon: '▸', label: 'Session Replay',     title: 'Session Replay',     breadcrumb: 'Conversation history playback', hidden: true },
    { page: 'setup-wizard',       icon: '▸', label: 'Setup Wizard',       title: 'Setup Wizard',       breadcrumb: 'Guided configuration', hidden: true },
    { page: 'user',               icon: '▸', label: 'User Dashboard',     title: 'User Dashboard',     breadcrumb: 'Resident self-service — EZ ID lookup', hidden: true },
    { page: 'calendar2',          icon: '▸', label: 'Calendar v2',        title: 'Calendar v2',        breadcrumb: 'Merged into Calendar', hidden: true },
    { page: 'oncall',            icon: '▸', label: 'Call Schedule',       title: 'Call Schedule',       breadcrumb: 'Merged into Schedule Suite', hidden: true },
    { page: 'staff-schedule',    icon: '▸', label: 'Staff Schedule',      title: 'Staff Schedule',      breadcrumb: 'Merged into Schedule Suite', hidden: true },
    { page: 'call-schedule-pdf', icon: '▸', label: 'Schedule PDF',        title: 'Call Schedule PDF',   breadcrumb: 'Merged into Schedule Suite', hidden: true },
    { page: 'cal-new',           icon: '▸', label: 'Calendar (legacy)',   title: 'Calendar (legacy)',   breadcrumb: 'Merged into Calendar', hidden: true },
    { page: 'compliance',             icon: '▸', label: 'Compliance',      title: 'Compliance',      breadcrumb: 'Merged into Compliance Suite', hidden: true },
    { page: 'eval-portal',            icon: '▸', label: 'Eval Portal',     title: 'Eval Portal',     breadcrumb: 'Merged into Compliance Suite', hidden: true },
    { page: 'eval-dashboard',         icon: '▸', label: 'Eval Dashboard',  title: 'Eval Dashboard',  breadcrumb: 'Merged into Compliance Suite', hidden: true },
    { page: 'gme-tracker',            icon: '▸', label: 'GME Tracker',     title: 'GME Tracker',     breadcrumb: 'Merged into Compliance Suite', hidden: true },
    { page: 'gme-detail',             icon: '▸', label: 'GME Deep Dive',   title: 'GME Deep Dive',   breadcrumb: 'Merged into Compliance Suite', hidden: true },
    { page: 'grand-rounds',           icon: '▸', label: 'Grand Rounds',    title: 'Grand Rounds',    breadcrumb: 'Merged into Grand Rounds Hub', hidden: true },
    { page: 'grand-rounds-attendance',icon: '▸', label: 'Attendance',      title: 'Attendance',      breadcrumb: 'Merged into Grand Rounds Hub', hidden: true },
    { page: 'conference-email',       icon: '▸', label: 'Conference Email', title: 'Conference Email', breadcrumb: 'Merged into Grand Rounds Hub', hidden: true },
    { page: 'chief-meetings',         icon: '▸', label: 'Chief Meetings',   title: 'Chief Meetings',   breadcrumb: 'Merged into Grand Rounds Hub', hidden: true },
    { page: 'people',                 icon: '▸', label: 'CRM People',      title: 'CRM People',      breadcrumb: 'Merged into CRM', hidden: true },
    { page: 'contacts',               icon: '▸', label: 'Contacts',        title: 'Contacts',        breadcrumb: 'Merged into CRM', hidden: true },
    { page: 'resident-roster',        icon: '▸', label: 'Resident Roster', title: 'Resident Roster', breadcrumb: 'Merged into CRM', hidden: true },
    { page: 'crm-audit',              icon: '▸', label: 'CRM Audit',       title: 'CRM Audit',       breadcrumb: 'Merged into CRM', hidden: true },
    { page: 'ai-builder',             icon: '▸', label: 'AI Builder',      title: 'AI Builder',         breadcrumb: 'Merged into AI Builder Suite', hidden: true },
    { page: 'prompt-tools-image',     icon: '▸', label: 'Image Builder',   title: 'Image Prompt Builder', breadcrumb: 'Merged into AI Builder Suite', hidden: true },
    { page: 'prompt-tools-video',     icon: '▸', label: 'Video Builder',   title: 'Video Prompt Builder', breadcrumb: 'Merged into AI Builder Suite', hidden: true },
    { page: 'image-gallery',          icon: '▸', label: 'Image Gallery',   title: 'Image Gallery',       breadcrumb: 'Merged into AI Builder Suite', hidden: true },
    { page: 'file-browser',           icon: '▸', label: 'File Browser',    title: 'File Browser',        breadcrumb: 'Merged into Workspace', hidden: true },
    { page: 'script-runner',          icon: '▸', label: 'Script Runner',   title: 'Script Runner',       breadcrumb: 'Merged into Workspace', hidden: true },
    { page: 'vs-coder',               icon: '▸', label: 'VS Coder',        title: 'VS Coder',            breadcrumb: 'Merged into Workspace', hidden: true },
    { page: 'google-studio',          icon: '▸', label: 'Google Studio',   title: 'Google Dev Studio',   breadcrumb: 'Merged into Workspace', hidden: true },
  ],

  // External links — never get the `data-page` attribute, never become active.
  external: [],
};

/** Flatten all routes (groups + sections + hidden) into a lookup map. */
function _allRoutes() {
  const out = {};
  NAV_CONFIG.groups.forEach(g => {
    (g.items || []).forEach(r => { out[r.page] = r; });
    (g.sections || []).forEach(sec => (sec.items || []).forEach(r => { out[r.page] = r; }));
  });
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

/** Build one nav item anchor. */
function _navItemHtml(item) {
  const disabled = item.enabled === false ? ' nav-item-disabled' : '';
  const badge = item.badgeId
    ? `<span class="nav-badge" id="${item.badgeId}">0</span>`
    : '';
  return `<a href="#${item.page}" class="nav-item${disabled}" data-page="${item.page}">` +
         `<span class="nav-icon">${item.icon}</span>` +
         `<span class="nav-label">${item.label}</span>` +
         badge +
         `</a>`;
}

/** Build the grouped sidebar HTML string from NAV_CONFIG (zones + collapsible sections). */
function buildSidebarNav() {
  const groupsHtml = NAV_CONFIG.groups.map(group => {
    const itemsHtml = (group.items || []).map(_navItemHtml).join('');
    let sectionsHtml = '';
    (group.sections || []).forEach((sec, si) => {
      const collapsed = sec.collapsed !== false; // default collapsed=true
      const secItems = sec.items.map(_navItemHtml).join('');
      sectionsHtml +=
        `<div class="sidebar-subsection" data-subsection="${group.label}-${si}">` +
        `<button class="sidebar-subsection-toggle${collapsed ? ' collapsed' : ''}" ` +
        `onclick="toggleSubsection(this)" title="Toggle ${sec.label}">` +
        `<span class="subsection-caret">▸</span>` +
        `<span class="sidebar-section-label">${sec.label}</span>` +
        `</button>` +
        `<div class="sidebar-subsection-items"${collapsed ? ' style="display:none"' : ''}>${secItems}</div>` +
        `</div>`;
    });
    return `<div class="sidebar-section">` +
           (itemsHtml ? `<div class="sidebar-section-label sidebar-zone-label">${group.label}</div>` : '') +
           itemsHtml +
           sectionsHtml +
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
  restoreSubsectionState();
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

/** Toggle a collapsible sidebar sub-section. */
function toggleSubsection(btn) {
  const wrap = btn.closest('.sidebar-subsection');
  if (!wrap) return;
  const items = wrap.querySelector('.sidebar-subsection-items');
  const isCollapsed = btn.classList.toggle('collapsed');
  if (items) items.style.display = isCollapsed ? 'none' : '';
  try {
    const key = 'aos_subsection_' + (wrap.getAttribute('data-subsection') || '');
    localStorage.setItem(key, isCollapsed ? '1' : '0');
  } catch (e) { /* ignore */ }
}

/** Restore saved sub-section collapse states after render. */
function restoreSubsectionState() {
  document.querySelectorAll('.sidebar-subsection').forEach(wrap => {
    const key = 'aos_subsection_' + (wrap.getAttribute('data-subsection') || '');
    let saved = null;
    try { saved = localStorage.getItem(key); } catch (e) { /* ignore */ }
    if (saved === null) return;
    const btn = wrap.querySelector('.sidebar-subsection-toggle');
    const items = wrap.querySelector('.sidebar-subsection-items');
    if (!btn || !items) return;
    if (saved === '1') { btn.classList.add('collapsed'); items.style.display = 'none'; }
    else { btn.classList.remove('collapsed'); items.style.display = ''; }
  });
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
      const icon = ok ? '●' : '○';
      return `<span title="${n}: ${ok ? 'OK' : services[n].error || 'down'}" style="display:inline-flex;align-items:center;gap:4px;cursor:pointer;color:var(--text)" onclick="navigate('health')">${icon}<span style="color:${color};font-weight:600">${n}</span></span>`;
    }).join('');
    widget.onclick = null;
  } catch (err) {
    widget.innerHTML = `<span style="color:var(--red);cursor:pointer" onclick="navigate('health')">▸ Health unavailable</span>`;
  }
}
