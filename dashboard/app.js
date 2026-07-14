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

async function loadPage(name) {
  // Remove any previously loaded page script so it always reloads fresh
  const old = document.querySelector(`script[src*="${PAGE_BASE}${name}.js"]`);
  if (old) old.remove();
  delete pageCache[name];
  
  try {
    const src = PAGE_BASE + name + '.js';
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
 */
async function navigate(page) {
  // Redirect-to-hash short-circuit. When the caller passes a page that
  // doesn't match the current hash, mutate the hash and return. The
  // hashchange listener will re-invoke navigate() with no argument to
  // do the actual render. This prevents a double render and keeps URL
  // back/forward in sync.
  if (page && `#${page}` !== window.location.hash) {
    window.location.hash = page;
    return;
  }

  const DEFAULT_ROUTE = 'dashboard';
  const hash = page || window.location.hash.slice(1) || DEFAULT_ROUTE;
  if (!hash) { window.location.hash = DEFAULT_ROUTE; return; }

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

  // Title/breadcrumb — use config if available, fall back to PAGE_TITLES,
  // finally a generic "Unknown" placeholder. Disabled routes still get a
  // title/breadcrumb from their config entry so the top bar looks right.
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
    content.innerHTML = `<div class="empty-state"><div class="empty-state-icon">🔍</div><div class="empty-state-title">Page not found</div><div class="empty-state-desc">The page "${escapeHtml(hash)}" isn't a known route.</div><button class="btn btn-primary mt-3" onclick="navigate('dashboard')">Go to Dashboard</button></div>`;
    if (bar) { bar.style.width = '0'; bar.classList.remove('active'); }
    return;
  }

  // Disabled route — render "Coming soon" empty state
  if (route.enabled === false) {
    content.innerHTML = `<div class="empty-state"><div class="empty-state-icon">🚧</div><div class="empty-state-title">Coming soon</div><div class="empty-state-desc">${escapeHtml(route.title)} is not yet available.</div><button class="btn btn-primary mt-3" onclick="navigate('dashboard')">Go to Dashboard</button></div>`;
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
      content.innerHTML = `<div class="empty-state"><div class="empty-state-icon">🔍</div><div class="empty-state-title">Page not found</div><div class="empty-state-desc">The page "${escapeHtml(hash)}" doesn't have a render function</div></div>`;
      if (bar) { bar.style.width = '0'; bar.classList.remove('active'); }
    }
  } catch (err) {
    content.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠</div><div class="empty-state-title">Failed to load</div><div class="empty-state-desc">${escapeHtml(err.message)}</div><button class="btn btn-primary mt-3" onclick="navigate('dashboard')">Go to Dashboard</button></div>`;
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
  navigate(window.location.hash.slice(1) || 'dashboard');
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