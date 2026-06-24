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

function handleGlobalSearch(value) {
  if (value.length < 2) return;
  if (window.location.hash !== '#skills') navigate('skills');
}

function renderSkeleton(count = 3) {
  return Array(count).fill(0).map(() =>
    `<div class="card"><div class="skeleton" style="height:20px;width:60%;margin-bottom:12px"></div><div class="skeleton" style="height:14px;width:90%;margin-bottom:8px"></div><div class="skeleton" style="height:14px;width:40%"></div></div>`
  ).join('');
}

const PAGE_TITLES = {
  dashboard: { title: 'Dashboard', breadcrumb: 'Overview' },
  skills: { title: 'Skills Hub', breadcrumb: 'Browse & execute skills' },
  memory: { title: 'Memory', breadcrumb: 'Shared brain context' },
  scheduler: { title: 'Scheduler', breadcrumb: 'Automated workflows' },
  audit: { title: 'Audit Log', breadcrumb: 'System activity trail' },
  cost: { title: 'Cost Analytics', breadcrumb: 'Usage & spending' },
  plugins: { title: 'Plugin Registry', breadcrumb: 'Manage plugins' },
  backups: { title: 'Backups', breadcrumb: 'Disaster recovery' },
  prompts: { title: 'Prompt Library', breadcrumb: 'Reusable templates' },
  standards: { title: 'Standards', breadcrumb: 'Project conventions' },
  settings: { title: 'Settings', breadcrumb: 'Configuration' },
  'setup-wizard': { title: 'Setup Wizard', breadcrumb: 'Guided configuration' },
  chat: { title: 'AI Chat', breadcrumb: 'Multi-agent terminal' },
  kanban: { title: 'Kanban Board', breadcrumb: 'Multi-agent task management' },
  goals: { title: 'Goals', breadcrumb: 'Project targets and progress' },
  journal: { title: 'Journal', breadcrumb: 'Daily entries and notes' },
  'agent-health': { title: 'Agent Health', breadcrumb: 'Real-time agent monitoring' },
  'smart-router': { title: 'Smart Router', breadcrumb: 'Task routing intelligence' },
  'learning-analytics': { title: 'Learning Analytics', breadcrumb: 'Skill improvement tracking' },
  'drive-sync': { title: 'Drive Sync', breadcrumb: 'Location-roster files from Drive' },
  'session-replay': { title: 'Session Replay', breadcrumb: 'Conversation history playback' },
  tools: { title: 'My Tools', breadcrumb: 'NotebookLM, Cron, KB, Hermes & more' },
  telegram: { title: 'Telegram Sessions', breadcrumb: 'Messaging conversations from state.db' },
  contacts: { title: 'CRM', breadcrumb: 'Contact management system' },
  'prompt-tools-image': { title: '🖼️ Image Prompt Builder', breadcrumb: 'Build professional image prompts visually' },
  'prompt-tools-video': { title: '🎬 Video Prompt Builder', breadcrumb: 'Build professional video prompts visually' },
  'email-templates': { title: 'Email Templates', breadcrumb: 'Pre-built email templates for quick sending' },
  'gme-tracker': { title: 'GME Reimbursement Tracker', breadcrumb: 'Resident education fund management' },
  'google-studio': { title: 'Google Dev Studio', breadcrumb: 'Apps Script editor & project manager' },
  'image-gallery': { title: '🎨 Image Gallery', breadcrumb: 'Browse design mockups and generated images' },
  'ai-builder': { title: 'AI Builder', breadcrumb: 'Google Antigravity — build with Gemini' },
  'crm-audit': { title: 'CRM Audit', breadcrumb: 'Access log for CRM operations' },
  oncall: { title: 'Call Schedule', breadcrumb: 'Weekly resident call rotation' },
  'grand-rounds': { title: 'Grand Rounds', breadcrumb: 'Urology academic schedule & Outlook invites' },
  'grand-rounds-attendance': { title: '📊 Grand Rounds Attendance', breadcrumb: 'Faculty compliance tracking & reports' },
  'unified-dashboard': { title: '🏥 Unified Dashboard', breadcrumb: 'Montefiore Urology — all systems in one view' },
  manager: { title: '📋 Manager Command Center', breadcrumb: 'Schedule, coverage & approvals at a glance' },
  'voice-commands': { title: '🎤 Voice Commands', breadcrumb: 'Telegram report generator cheat sheet' },
  health: { title: '🏥 System Health', breadcrumb: 'Central services & cron health monitor' },
  'vs-coder': { title: '💻 VS Coder', breadcrumb: 'Full code editor — edit, run, commit' },
  'system-overview': { title: '🏥 System Overview', breadcrumb: 'Central services, cron health & monitoring' },
  'quick-actions': { title: '⚡ Quick Actions', breadcrumb: 'One-click operations for common workflows' },
  'eval-portal': { title: '📝 Eval Portal', breadcrumb: 'CMS evaluation forms — track & remind' },
  'call-schedule-pdf': { title: '📄 Call Schedule PDF', breadcrumb: 'Generate and email call schedule PDFs' },
  'telegram-logs': { title: '✈️ Telegram Logs', breadcrumb: 'Recent messages, gateway status & log viewer' },
  'script-runner': { title: '⚙️ Script Runner', breadcrumb: 'Run workspace scripts from the dashboard' },
  'resident-roster': { title: '🩺 Resident Roster', breadcrumb: 'Urology residents contact info and status' },
  'compliance': { title: '📊 Compliance Dashboard', breadcrumb: 'Attendance, evals & GME — color-coded metrics' },
  'morning-briefing': { title: '🌅 Morning Briefing', breadcrumb: 'Daily urology briefing — call, evals, events' },
  'file-browser': { title: '🗂 File Browser', breadcrumb: 'Browse and view workspace files' },
  'notifications': { title: '🔔 Notification Feed', breadcrumb: 'Cron, eval & system events feed' },
  'staff-schedule': { title: '👥 Staff Schedule', breadcrumb: 'NP/PA/coordinator schedules by hospital' },
  'pdf-archive': { title: '📄 PDF Archive', breadcrumb: 'All generated PDFs in one place' },
  'gme-detail': { title: '📈 GME Deep Dive', breadcrumb: 'Resident fund usage breakdown with charts' },
};

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
