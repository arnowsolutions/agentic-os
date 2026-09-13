"use strict";

const pageCache = {};

/** Toggle mobile sidebar + overlay */
function toggleMobileMenu() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  if (sidebar && overlay) {
    sidebar.classList.toggle('open');
    overlay.classList.toggle('active');
  }
}

/** Track recently visited pages (max 5) */
function trackRecentPage(hash) {
  if (!hash || hash === 'dashboard') return;
  try {
    let recent = JSON.parse(localStorage.getItem('aos_recent') || '[]');
    recent = recent.filter(p => p !== hash);
    recent.unshift(hash);
    recent = recent.slice(0, 5);
    localStorage.setItem('aos_recent', JSON.stringify(recent));
  } catch (e) { /* ignore */ }
}

const PAGE_BASE = '/dashboard/pages/';

const DEFAULT_ROUTE = 'dashboard';

// Legacy merged routes (PR5+PR6) → canonical target. Keeps old bookmarks alive:
// `#oncall` opens the Schedule Suite on its Weekly Call tab, `#cal-new` and
// `#calendar2` open the canonical Calendar; PR6 adds the Compliance Suite,
// Grand Rounds Hub and CRM suite redirects.
const LEGACY_REDIRECTS = {
  'oncall':             'schedule-suite?tab=call',
  'staff-schedule':     'schedule-suite?tab=staff',
  'call-schedule-pdf':  'schedule-suite?tab=pdf',
  'cal-new':            'calendar',
  'calendar2':          'calendar',
  // PR6 — Compliance Suite
  'compliance':             'compliance-suite?tab=overview',
  'eval-portal':            'compliance-suite?tab=eval-portal',
  'eval-dashboard':         'compliance-suite?tab=eval-dashboard',
  'gme-tracker':            'compliance-suite?tab=gme-tracker',
  'gme-detail':             'compliance-suite?tab=gme-detail',
  // PR6 — Grand Rounds Hub
  'grand-rounds':           'grand-rounds-hub?tab=events',
  'grand-rounds-attendance': 'grand-rounds-hub?tab=attendance',
  'conference-email':       'grand-rounds-hub?tab=invites',
  'chief-meetings':         'grand-rounds-hub?tab=chief-meetings',
  // PR6 — CRM suite
  'people':                 'crm-suite?tab=people',
  'contacts':               'crm-suite?tab=contacts',
  'resident-roster':        'crm-suite?tab=residents',
  'crm-audit':              'crm-suite?tab=audit',
  // PR7 — AI Builder Suite
  'ai-builder':             'ai-builder-suite?tab=builder',
  'prompt-tools-image':     'ai-builder-suite?tab=image',
  'prompt-tools-video':     'ai-builder-suite?tab=video',
  'image-gallery':          'ai-builder-suite?tab=gallery',
  // PR7 — Workspace suite
  'file-browser':           'workspace-suite?tab=files',
  'script-runner':          'workspace-suite?tab=scripts',
  'vs-coder':               'workspace-suite?tab=coder',
  'google-studio':          'workspace-suite?tab=apps',
  // 2026-09 SSOT stage 3 — overview collapse (Today + Health Suite)
  'unified-dashboard':      'today?tab=overview',
  'manager':                'today?tab=manager',
  'health':                 'health-suite?tab=services',
  'system-overview':        'health-suite?tab=overview',
  'operations':             'health-suite?tab=metrics',
  'agent-health':           'health-suite?tab=agents',
};

async function loadPage(name) {
  // Remove any previously loaded page script so it always reloads fresh
  const old = document.querySelector(`script[src*="${PAGE_BASE}${name}.js"]`);
  if (old) old.remove();
  delete pageCache[name];
  
  try {
    // Cache-bust so page modules are always fetched fresh (prevents stale browsers
    // showing old code after a deploy). A timestamp forces revalidation every load.
    const src = PAGE_BASE + name + '.js?v=' + Date.now();
    await loadScript(src);
    pageCache[name] = true;
  } catch (err) {
    showToast(`Failed to load page: ${name}`, 'error');
    throw err;
  }
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load ${src}`));
    document.body.appendChild(script);
  });
}

function capitalize(str) { return str.charAt(0).toUpperCase() + str.slice(1); }

/**
 * Shared page loading flow — loads the page JS module, finds the render
 * function, and renders it. Used by navigate() and CUSTOM_PAGES entries.
 */
async function navigateLoadPage(hash, info) {
  const bar = document.getElementById('topLoadingBar');
  const content = document.getElementById('pageContent');

  document.getElementById('pageTitle').textContent = info.title;
  document.getElementById('pageBreadcrumb').textContent = info.breadcrumb || '';

  // Close search results
  const searchResults = document.getElementById('searchResults');
  if (searchResults) { searchResults.innerHTML = ''; searchResults.style.display = 'none'; }

  // Loading state
  content.innerHTML = `<div class="loading"><div class="loading-spinner"></div><span>Loading ${info.title}...</span></div>`;
  if (bar) { bar.classList.add('active'); bar.style.width = '30%'; }

  try {
    await loadPage(hash);
    const renderFnName = `render${capitalize(hash.replace(/-./g, m => m[1].toUpperCase()))}`;
    const renderFn = window[renderFnName];
    if (renderFn) {
      content.innerHTML = '';
      content.className = 'page-content page-enter';
      if (bar) bar.style.width = '70%';
      await renderFn();
      trackRecentPage(hash);
      renderSidebar();
      if (bar) { bar.style.width = '100%'; setTimeout(() => { bar.style.width = '0'; bar.classList.remove('active'); }, 400); }
    } else {
      content.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⌕</div><div class="empty-state-title">Page not found</div><div class="empty-state-desc">The page "${escapeHtml(hash)}" doesn't have a render function</div><button class="btn btn-primary mt-3" onclick="navigate('dashboard')">Go to Dashboard</button></div>`;
      if (bar) { bar.style.width = '0'; bar.classList.remove('active'); }
    }
  } catch (err) {
    content.innerHTML = `<div class="empty-state"><div class="empty-state-icon">!</div><div class="empty-state-title">Failed to load</div><div class="empty-state-desc">${escapeHtml(err.message)}</div><button class="btn btn-primary mt-3" onclick="navigate('dashboard')">Go to Dashboard</button></div>`;
    if (bar) { bar.style.width = '0'; bar.classList.remove('active'); }
  }
}

/**
 * Hash-aware router.
 *
 * - When called with an explicit `page` that differs from the current hash,
 *   we set the hash and bail. The `hashchange` listener re-invokes
 *   `navigate()` with no argument, so the render happens exactly once and
 *   browser back/forward stays in sync. When called from `hashchange` (no
 *   arg) or when the hash already matches, we proceed to render.
 * - Routes are resolved via `getNavRoute(hash)` rather than relying solely
 *   on `window[renderFn]` existence. Unknown routes render the existing
 *   "Page not found" empty state. Disabled routes (`enabled === false`,
 *   e.g. `people`) set their title/breadcrumb + active state from config,
 *   then render a clear "Coming soon" empty state instead of attempting to
 *   load a missing module. Enabled routes keep the current
 *   `loadPage` + `render*` flow.
 * - Active-state handling: `.active` is cleared from every `[data-page]`
 *   item and set on the matched one. The external VS Code link has no
 *   `data-page` attribute, so it can never become active.
 * - Legacy-route handling (PR5): hashes in LEGACY_REDIRECTS rewrite to their
 *   canonical target (suite + tab param) before route resolution.
 */
async function navigate(page) {
  // Redirect-to-hash short-circuit. When the caller passes a page that
  // doesn't match the current hash, mutate the hash and return. The
  // hashchange listener will re-invoke navigate() with no argument to
  // do the actual render. This prevents a double render and keeps URL
  // back/forward in sync.
  // Legacy merged routes (PR5): rewrite to the canonical target and bail —
  // the hashchange listener re-invokes navigate() for the actual render.
  const requested = page || window.location.hash.slice(1) || DEFAULT_ROUTE;
  const hashBase = requested.split('?')[0];
  if (LEGACY_REDIRECTS[hashBase]) {
    const target = LEGACY_REDIRECTS[hashBase];
    if (window.location.hash.slice(1) !== target) {
      window.location.hash = target;
      return;
    }
  }

  // Redirect-to-hash short-circuit (legacy keys excluded — handled above).
  // The hash may carry ?tab=… params; compare only the route part.
  if (page && !LEGACY_REDIRECTS[page] && window.location.hash.slice(1).split('?')[0] !== page) {
    window.location.hash = page;
    return;
  }

  const hash = (page || window.location.hash.slice(1) || DEFAULT_ROUTE).split('?')[0];
  if (!hash) { window.location.hash = DEFAULT_ROUTE; return; }
  // AI-generalist: remember the last data page so chat can pre-attach context.
  if (hash !== 'chat') window._lastDataPage = hash;

  const route = getNavRoute(hash);

  // Close mobile menu on navigation
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  if (sidebar) sidebar.classList.remove('open');
  if (overlay) overlay.classList.remove('active');

  // Show loading bar
  const bar = document.getElementById('topLoadingBar');
  if (bar) { bar.classList.add('active'); bar.style.width = '30%'; }

  // Active-state handling (external link has no data-page → never active)
  document.querySelectorAll('.nav-item[data-page]').forEach(el => el.classList.remove('active'));
  const navItem = document.querySelector(`[data-page="${hash}"]`);
  if (navItem) navItem.classList.add('active');

  // Custom pages not in NAV_CONFIG (social-media-hub, etc.)
  const CUSTOM_PAGES = {
    'tasks': { title: 'Tasks', breadcrumb: 'Your task list' },
    'social-media-hub': { title: 'Social Media Hub', breadcrumb: '42+ integrated social skills' },
    'distribution': { title: 'Distribution Lists', breadcrumb: 'Recipient groups — faculty, residents, supervisors' },
  };
  if (!route && CUSTOM_PAGES[hash]) {
    return navigateLoadPage(hash, CUSTOM_PAGES[hash]);
  }

  // Title/breadcrumb
  const info = route
    ? { title: route.title, breadcrumb: route.breadcrumb || '' }
    : (PAGE_TITLES[hash] || { title: 'Unknown', breadcrumb: '' });
  document.getElementById('pageTitle').textContent = info.title;
  document.getElementById('pageBreadcrumb').textContent = info.breadcrumb;

  const content = document.getElementById('pageContent');

  // Close any open search results when navigating
  const searchResults = document.getElementById('searchResults');
  if (searchResults) { searchResults.innerHTML = ''; searchResults.style.display = 'none'; }

  // Unknown route — render "Page not found"
  if (!route) {
    content.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⌕</div><div class="empty-state-title">Page not found</div><div class="empty-state-desc">The page "${escapeHtml(hash)}" isn't a known route.</div><button class="btn btn-primary mt-3" onclick="navigate('dashboard')">Go to Dashboard</button></div>`;
    if (bar) { bar.style.width = '0'; bar.classList.remove('active'); }
    return;
  }

  // Disabled route — render "Coming soon" empty state
  if (route.enabled === false) {
    content.innerHTML = `<div class="empty-state"><div class="empty-state-icon">△</div><div class="empty-state-title">Coming soon</div><div class="empty-state-desc">${escapeHtml(route.title)} is not yet available.</div><button class="btn btn-primary mt-3" onclick="navigate('dashboard')">Go to Dashboard</button></div>`;
    if (bar) { bar.style.width = '0'; bar.classList.remove('active'); }
    return;
  }

  // Enabled route — keep the loadPage + render* flow
  content.innerHTML = `<div class="loading"><div class="loading-spinner"></div><span>Loading ${info.title}...</span></div>`;

  try {
    await loadPage(hash);
    const renderFnName = `render${capitalize(hash.replace(/-./g, m => m[1].toUpperCase()))}`;
    const renderFn = window[renderFnName];
    if (renderFn) {
      content.innerHTML = '';
      content.className = 'page-content page-enter';
      if (bar) bar.style.width = '70%';
      await renderFn();
      trackRecentPage(hash);
      renderSidebar();  // update "Recent" section
      if (bar) { bar.style.width = '100%'; setTimeout(() => { bar.style.width = '0'; bar.classList.remove('active'); }, 400); }
    } else {
      content.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⌕</div><div class="empty-state-title">Page not found</div><div class="empty-state-desc">The page "${escapeHtml(hash)}" doesn't have a render function</div></div>`;
      if (bar) { bar.style.width = '0'; bar.classList.remove('active'); }
    }
  } catch (err) {
    content.innerHTML = `<div class="empty-state"><div class="empty-state-icon">!</div><div class="empty-state-title">Failed to load</div><div class="empty-state-desc">${escapeHtml(err.message)}</div><button class="btn btn-primary mt-3" onclick="navigate('dashboard')">Go to Dashboard</button></div>`;
    if (bar) { bar.style.width = '0'; bar.classList.remove('active'); }
  }
}

async function updateAgentStatus() {
  try {
    const status = await api.getStatus();
    const agents = status.agents || [];
    const bar = document.getElementById('agentStatusBar');
    const online = agents.filter(a => a.status === 'online').length;
    const total = agents.length;
    const dot = bar.querySelector('.agent-dot');
    if (online === total) { dot.className = 'agent-dot online'; bar.querySelector('span').textContent = 'All agents online'; }
    else if (online > 0) { dot.className = 'agent-dot warning'; bar.querySelector('span').textContent = `${online}/${total} online`; }
    else { dot.className = 'agent-dot offline'; bar.querySelector('span').textContent = 'All agents offline'; }

    const badge = document.getElementById('skillCount');
    if (badge && status.skills_count !== undefined) badge.textContent = status.skills_count;
  } catch {
    const bar = document.getElementById('agentStatusBar');
    if (bar) { bar.querySelector('.agent-dot').className = 'agent-dot offline'; bar.querySelector('span').textContent = 'Disconnected'; }
  }
}

window.addEventListener('hashchange', () => navigate());
window.addEventListener('DOMContentLoaded', () => {
  loadTheme();
  // Build the sidebar from NAV_CONFIG before the first navigate() so nav
  // items exist when active-state is applied.
  renderSidebar();
  navigate(window.location.hash.slice(1) || DEFAULT_ROUTE);
  updateAgentStatus();
  loadHealth();
  setInterval(updateAgentStatus, 15000);
  setInterval(loadHealth, 30000);
});

// Dismiss the search dropdown when clicking outside the search box.
document.addEventListener('click', (ev) => {
  const searchBox = document.querySelector('.topbar-search');
  const resultsEl = document.getElementById('searchResults');
  if (!searchBox || !resultsEl) return;
  if (!searchBox.contains(ev.target)) {
    resultsEl.innerHTML = '';
    resultsEl.style.display = 'none';
  }
});

// ══════════════════════════════════════════════════════════════
//  SHARED RSVP TEMPLATE + EDIT-THEN-SEND MODAL  (global helpers)
//  One consistent rich email format for every event type, plus a
//  modal to edit subject/body/recipients before opening Outlook.
// ══════════════════════════════════════════════════════════════

/**
 * Build the canonical rich invite body (single template for all events).
 * config: {
 *   header   : string  e.g. "Montefiore Urology - Grand Rounds"
 *   date     : string  pre-formatted ("Monday, September 14, 2026")
 *   time     : string  e.g. "7:00 - 9:00 AM (Eastern)"
 *   location : string
 *   agenda   : [{ time, item }]  (optional)
 *   zoom     : { link, id, passcode }  (optional)
 *   extra    : [string]  additional labeled lines (optional)
 *   footer   : string  override department footer (optional)
 * }
 */
window.buildRsvpBody = function(config) {
  const e = (s) => String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  const lines = [];
  lines.push(`<strong>${e(config.header || 'Montefiore Urology')}</strong>`);
  lines.push('<hr>');
  lines.push(`<strong>Date</strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${e(config.date)}`);
  lines.push(`<strong>Time</strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${e(config.time)}`);
  if (config.location) lines.push(`<strong>Location</strong>&nbsp;&nbsp;&nbsp;${e(config.location)}`);
  if (config.type) lines.push(`<strong>Type</strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${e(config.type)}`);
  if (config.extra && config.extra.length) {
    for (const x of config.extra) lines.push(e(x));
  }
  if (config.agenda && config.agenda.length) {
    lines.push('<hr>');
    lines.push('<strong>AGENDA</strong>');
    lines.push('');
    for (const a of config.agenda) {
      lines.push(`<strong>${e(a.time)}</strong>&nbsp;&nbsp;${e(a.item || '')}`);
    }
  }
  if (config.zoom && config.zoom.link) {
    lines.push('<hr>');
    lines.push('<strong>ZOOM MEETING DETAILS</strong>');
    lines.push('');
    lines.push(`<strong>Join</strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href="${e(config.zoom.link)}">Click here to join Zoom</a>`);
    if (config.zoom.id) lines.push(`<strong>Meeting ID</strong>&nbsp;&nbsp;<span style="background:#f5f5f5;padding:2px 6px;border-radius:3px">${e(config.zoom.id)}</span>`);
    if (config.zoom.passcode) lines.push(`<strong>Passcode</strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="background:#f5f5f5;padding:2px 6px;border-radius:3px">${e(config.zoom.passcode)}</span>`);
    lines.push('<hr>');
    lines.push('<strong>PHONE DIAL-IN</strong>');
    lines.push('');
    lines.push('&bull; +1 646-558-8656 (New York)');
    lines.push('&bull; +1 301-715-8592 (Washington, DC)');
    lines.push('&bull; +1 312-626-6799 (Chicago)');
    lines.push('');
    lines.push('<i>Enter Meeting ID, then Passcode when prompted.</i>');
  }
  lines.push('<hr>');
  lines.push('<strong>Montefiore Medical Center | Department of Urology</strong>');
  lines.push('<span style="font-size:11px">1250 Waters Place, Tower One, PH-2, Bronx, NY 10461</span>');
  return lines.join('<br>');
};

// Current event being edited
let rsvpEditing = null;

/**
 * Open the edit-then-send modal for an event.
 * event: { subject, body, to, startdt, enddt, location, bodyType }
 */
window.openEventEditor = function(event) {
  if (!event) { showToast('No event to edit', 'warning'); return; }
  rsvpEditing = event;
  const toVal = event.to || '';
  const bodyHtml =
    `<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
       <div style="grid-column:1/-1">
         <label style="display:block;font-size:11px;color:var(--muted);margin-bottom:4px;font-weight:600">Subject</label>
         <input type="text" id="rsvpSubject" value="${escapeHtml(event.subject ?? '')}" style="width:100%;padding:9px 10px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text);font-size:13px">
       </div>
       <div style="grid-column:1/-1">
         <label style="display:block;font-size:11px;color:var(--muted);margin-bottom:4px;font-weight:600">Email Body (rich text — click to edit)</label>
         <div id="rsvpBody" contenteditable="true" style="width:100%;min-height:260px;padding:12px;border:1px solid var(--border);border-radius:8px;background:#fff;color:#1a1a1a;font-size:13px;line-height:1.6;overflow-y:auto">${event.body || ''}</div>
       </div>
       <div>
         <label style="display:block;font-size:11px;color:var(--muted);margin-bottom:4px;font-weight:600">Recipients (comma or ; separated)</label>
         <textarea id="rsvpTo" rows="4" style="width:100%;padding:9px 10px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text);font-size:12px">${escapeHtml(toVal)}</textarea>
       </div>
       <div>
         <label style="display:block;font-size:11px;color:var(--muted);margin-bottom:4px;font-weight:600">Location</label>
         <input type="text" id="rsvpLocation" value="${escapeHtml(event.location ?? '')}" style="width:100%;padding:9px 10px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text);font-size:12px">
         <label style="display:block;font-size:11px;color:var(--muted);margin:8px 0 4px;font-weight:600">Start (ISO)</label>
         <input type="text" id="rsvpStart" value="${escapeHtml(event.startdt ?? '')}" style="width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text);font-size:12px;font-family:monospace">
         <label style="display:block;font-size:11px;color:var(--muted);margin:8px 0 4px;font-weight:600">End (ISO)</label>
         <input type="text" id="rsvpEnd" value="${escapeHtml(event.enddt ?? '')}" style="width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text);font-size:12px;font-family:monospace">
       </div>
     </div>`;

  const footer =
    `<button class="btn btn-cancel" onclick="closeModal()">Cancel</button>
     <button class="btn" style="background:#f59e0b;color:#0f172a;border:none;font-weight:700" onclick="sendEdited()">Open in Outlook</button>`;

  showModal('Edit Invite & Send', bodyHtml, footer);
};

/**
 * Collect edited values and open Outlook with the resulting deeplink.
 */
window.sendEdited = function() {
  if (!rsvpEditing) { closeModal(); return; }
  const subject = document.getElementById('rsvpSubject').value;
  const body = document.getElementById('rsvpBody').innerHTML;
  const to = document.getElementById('rsvpTo').value.trim();
  const location = document.getElementById('rsvpLocation').value;
  const startdt = document.getElementById('rsvpStart').value.trim();
  const enddt = document.getElementById('rsvpEnd').value.trim();
  const params = new URLSearchParams();
  params.set('subject', subject || 'Invitation');
  params.set('body', body || '');
  params.set('bodyType', 'HTML');
  if (to) params.set('to', to);
  if (location) params.set('location', location);
  if (startdt) params.set('startdt', startdt);
  if (enddt) params.set('enddt', enddt);
  const url = 'https://outlook.office.com/calendar/deeplink/compose?' + params.toString();
  closeModal();
  window.open(url, '_blank');
};

/**
 * Build a deeplink-open without the editor (used by batch "open all").
 */
window.openEventDirect = function(event) {
  if (!event) return;
  const params = new URLSearchParams({
    subject: event.subject || 'Invitation',
    body: event.body || '',
    bodyType: event.bodyType || 'HTML',
  });
  const optional = [['to', event.to], ['location', event.location], ['startdt', event.startdt], ['enddt', event.enddt]];
  for (const [k, v] of optional) if (v) params.set(k, v);
  window.open('https://outlook.office.com/calendar/deeplink/compose?' + params.toString(), '_blank');
};