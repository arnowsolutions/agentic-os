/* ═══════════════════════════════════════════════════════════════════════
   Calendar Page — Professional Redesign
   Smart categorization, color-coded events, clean typography.
   ═══════════════════════════════════════════════════════════════════ */

// ─── Category Detection ──────────────────────────────────────
const CATEGORIES = {
  grand_rounds:   { label: 'Grand Rounds',   color: '#10b981', keywords: ['grand rounds', 'gr:', '👶', '🎓'] },
  conference:     { label: 'Conference',     color: '#3b82f6', keywords: ['sasp', '📋', 'conference', 'monday'] },
  vacation:       { label: 'Vacation',       color: '#f59e0b', keywords: ['vacation', 'sankin vacation', 'sankin - vacation'] },
  meeting:        { label: 'Meeting',        color: '#8b5cf6', keywords: ['pec meeting', 'town hall', 'committee'] },
  academic:       { label: 'Academic',       color: '#ec4899', keywords: ['sub-intern', 'rotation', 'rotations'] },
  admin:          { label: 'Admin & Deadlines', color: '#6b7280', keywords: ['onboard', 'workday', 'eras', 'match', 'acgme', 'interview', 'applications', 'deadline', 'submit', 'register', 'enroll', 'pay', 'pick', 'review', 'send', 'complete', 'schedule', 'create', 'prepare', 'virtual', 'graduation', 'orientation', 'exit', 'update ads', 'update website', 'ise', 'smart goals', 'semi-annual'] },
};

function detectCategory(summary) {
  const s = (summary || '').toLowerCase();
  for (const [key, cat] of Object.entries(CATEGORIES)) {
    for (const kw of cat.keywords) {
      if (s.includes(kw)) return key;
    }
  }
  return 'other';
}

// ─── Date Formatting ─────────────────────────────────────────
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

function fmtDate(iso) {
  if (!iso) return '—';
  const d = iso.slice(0,10);
  const [y, m, day] = d.split('-');
  return `${MONTHS[parseInt(m)-1]} ${parseInt(day)}`;
}

function fmtDateRange(startISO, endISO) {
  const s = startISO?.slice(0,10) || '';
  let e = endISO?.slice(0,10) || '';
  if (!e || e === s) return fmtDate(startISO);
  // All-day Google events have exclusive end → subtract 1 day
  const endDate = new Date(e + 'T12:00:00');
  endDate.setDate(endDate.getDate() - 1);
  e = endDate.toISOString().slice(0,10);
  if (e === s) return fmtDate(startISO);
  const [sy, sm] = s.split('-');
  const [ey, em] = e.split('-');
  if (sy === ey && sm === em) {
    return `${MONTHS[parseInt(sm)-1]} ${parseInt(s.slice(8,10))} – ${parseInt(e.slice(8,10))}, ${sy}`;
  }
  if (sy === ey) {
    return `${MONTHS[parseInt(sm)-1]} ${parseInt(s.slice(8,10))} – ${MONTHS[parseInt(em)-1]} ${parseInt(e.slice(8,10))}, ${sy}`;
  }
  return `${fmtDate(startISO)} – ${fmtDate(e)}`;
}

function fmtTime(iso) {
  if (!iso || iso.length <= 10) return null; // all-day event
  const d = new Date(iso);
  return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
}

// ─── Deduplication ───────────────────────────────────────────
function dedupe(events) {
  const seen = new Set();
  return events.filter(e => {
    const key = `${e.summary}|${e.start?.date || e.start?.dateTime}|${e.end?.date || e.end?.dateTime}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

// ─── Color helpers ───────────────────────────────────────────
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1,3), 16);
  const g = parseInt(hex.slice(3,5), 16);
  const b = parseInt(hex.slice(5,7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

// ─── Main Render ─────────────────────────────────────────────
// Past events are archived server-side as their dates pass; this page shows the
// upcoming list by default and the archive behind the "Archived" tab.
let calMode = 'upcoming';
window._calArchMonth = null;
window._calArchQuery = '';
window._calActiveCat = 'all';

async function renderCalendar() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">Calendar of Events</h1>
        <p class="page-subtitle">Vacation, call schedule, conferences, and department deadlines</p>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost btn-sm" onclick="calRerender()">Refresh</button>
      </div>
    </div>
    <div id="calFilterBar" style="margin-bottom:12px"></div>
    <div id="calArchiveNote" style="margin:0 0 16px;font-size:0.75rem;color:var(--text-muted)"></div>
    <div id="todoPanel" class="todo-panel collapsed">
      <div class="todo-header" onclick="toggleTodoPanel()">
        <span class="todo-header-title">Tasks</span>
        <span class="todo-header-count" id="todoCount">—</span>
        <span class="todo-header-toggle">▸</span>
      </div>
      <div class="todo-body">
        <div class="todo-input-row">
          <input class="form-input todo-input" id="todoNewInput" placeholder="Add a task..." onkeydown="if(event.key==='Enter')addTodo()">
          <button class="btn btn-primary btn-sm" onclick="addTodo()">Add</button>
        </div>
        <div id="todoList"><div class="loading" style="padding:12px"><div class="loading-spinner"></div></div></div>
      </div>
    </div>
    <div id="calendarContent">
      <div class="loading"><div class="loading-spinner"></div></div>
    </div>
  `;

  try {
    const res = await fetch('/api/calendar/events?days=365&include_todos=true');
    const data = await res.json();
    stampPage(data);
    let events = (data.events || []).map(e => ({
      ...e,
      category: detectCategory(e.summary),
      summary: cleanSummary(e.summary),
    }));

    // Load todos from response or fetch directly via proxy-safe endpoint
    if (data.todos) {
      if (Array.isArray(data.todos)) {
        window._todoItems = data.todos;
        renderTodoList();
      }
      // If kanban format, fetch the real task list
      else if (data.todos.columns) {
        await fetchTodosFromCrm();
      }
    } else {
      await fetchTodosFromCrm();
    }

    // Dedupe
    events = dedupe(events);

    if (events.length === 0) {
      document.getElementById('calendarContent').innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">—</div>
          <div class="empty-state-title">No upcoming events</div>
          <div class="empty-state-desc">No calendar events found for the next year.</div>
        </div>`;
      return;
    }

    // Category counts
    const catCounts = {};
    events.forEach(e => { catCounts[e.category] = (catCounts[e.category] || 0) + 1; });

    // Build filter bar
    const allCats = ['all', ...Object.keys(CATEGORIES)];
    let filterHtml = '<div class="tabs" style="flex-wrap:wrap" id="calFilterTabs">';
    filterHtml += `<button class="tab active" data-cat="all" onclick="calFilter('all')">All <span style="opacity:0.5;margin-left:4px;font-size:0.7em">${events.length}</span></button>`;
    for (const cat of allCats) {
      if (cat === 'all' || !catCounts[cat]) continue;
      const c = CATEGORIES[cat];
      filterHtml += `<button class="tab" data-cat="${cat}" onclick="calFilter('${cat}')" style="--cat-color:${c.color}">${c.label} <span style="opacity:0.5;margin-left:4px;font-size:0.7em">${catCounts[cat]}</span></button>`;
    }
    filterHtml += '</div>';

    // Store events for filtering
    window._calCatTabsHtml = filterHtml;
    window._calArchivedCount = data.archived_count || 0;
    window._calEvents = events;
    window._calActiveCat = 'all';
    calMode = 'upcoming';

    renderCalToolbar();
    renderCalArchiveNote(data);
    if (data.archived_this_read) {
      showToast(`${data.archived_this_read} finished event${data.archived_this_read !== 1 ? 's' : ''} moved to the archive`, 'success');
    }

    renderCalGrid(events);

  } catch (err) {
    document.getElementById('calendarContent').innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">—</div>
        <div class="empty-state-title">Failed to load calendar</div>
        <div class="empty-state-desc">${err.message}</div>
      </div>`;
  }
}

// ─── Clean summary ───────────────────────────────────────────
function cleanSummary(s) {
  return (s || 'Untitled Event')
    .replace(/^[📋👶🎓📞🏖📌📊🔔⚠️💼🎯📝📄📈📉📅📧📤💰🩺🔍🔑⚙️✈️🔄🚀👤💻🔷🖼️🎬🎨🗂🤖🧠🧭🌐🏥📡◉🔗💬📁⏱💾📐🔌📇🎤📌🩺]\s*/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

// ─── Render Calendar Grid ────────────────────────────────────
function renderCalGrid(events, activeCat = 'all') {
  const filtered = activeCat === 'all' ? events : events.filter(e => e.category === activeCat);

  if (filtered.length === 0) {
    document.getElementById('calendarContent').innerHTML = `
      <div class="empty-state">
        <div class="empty-state-title">No events in this category</div>
      </div>`;
    return;
  }

  // Group by month
  const months = {};
  filtered.forEach(ev => {
    const start = ev.start?.date || ev.start?.dateTime?.slice(0,10) || 'unknown';
    const mk = start.slice(0, 7);
    if (!months[mk]) months[mk] = [];
    months[mk].push(ev);
  });

  const sortedMonths = Object.keys(months).sort();

  let html = '';
  sortedMonths.forEach(mk => {
    const [y, m] = mk.split('-');
    const monthName = new Date(parseInt(y), parseInt(m)-1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    const monthEvents = months[mk];

    // Group events by category within this month
    const byCat = {};
    monthEvents.forEach(e => {
      if (!byCat[e.category]) byCat[e.category] = [];
      byCat[e.category].push(e);
    });

    html += `<div class="cal-month">
      <div class="cal-month-header" onclick="this.parentElement.classList.toggle('collapsed')">
        <span class="cal-month-name">${monthName}</span>
        <span class="cal-month-count">${monthEvents.length} event${monthEvents.length !== 1 ? 's' : ''}</span>
      </div>
      <div class="cal-month-body">`;

    // Render category sections
    const catOrder = Object.keys(CATEGORIES);
    for (const cat of catOrder) {
      const catEvents = byCat[cat];
      if (!catEvents || catEvents.length === 0) continue;
      const catDef = CATEGORIES[cat];
      html += `<div class="cal-cat-section">
        <div class="cal-cat-label" style="color:${catDef.color}">${catDef.label}</div>`;

      catEvents.forEach(ev => {
        const start = ev.start?.date || ev.start?.dateTime?.slice(0,10) || '';
        const end = ev.end?.date || ev.end?.dateTime?.slice(0,10) || '';
        const summary = ev.summary;
        const desc = (ev.description || '').trim();
        const time = fmtTime(ev.start?.dateTime || ev.start?.date);
        const isMultiDay = end && end !== start;

        html += `<div class="cal-event" style="--event-color:${catDef.color};--event-bg:${hexToRgba(catDef.color, 0.06)}">
          <div class="cal-event-indicator" style="background:${catDef.color}"></div>
          <div class="cal-event-body">
            <div class="cal-event-title">${escapeHtml(summary)}</div>
            <div class="cal-event-meta">
              <span class="cal-event-date">${fmtDateRange(ev.start?.date || ev.start?.dateTime, ev.end?.date || ev.end?.dateTime)}</span>
              ${time ? `<span class="cal-event-time">${time}</span>` : ''}
              ${isMultiDay ? `<span class="cal-event-days">Multi-day</span>` : ''}
            </div>
            ${desc ? `<div class="cal-event-desc">${escapeHtml(desc)}</div>` : ''}
          </div>
        </div>`;
      });

      html += `</div>`;
    }

    // Uncategorized
    const otherEvents = byCat['other'];
    if (otherEvents && otherEvents.length > 0) {
      html += `<div class="cal-cat-section">
        <div class="cal-cat-label" style="color:#6b7280">Other</div>`;
      otherEvents.forEach(ev => {
        html += `<div class="cal-event" style="--event-color:#6b7280;--event-bg:rgba(107,114,128,0.06)">
          <div class="cal-event-indicator" style="background:#6b7280"></div>
          <div class="cal-event-body">
            <div class="cal-event-title">${escapeHtml(ev.summary)}</div>
            <div class="cal-event-meta">
              <span class="cal-event-date">${fmtDateRange(ev.start?.date || ev.start?.dateTime, ev.end?.date || ev.end?.dateTime)}</span>
            </div>
            ${ev.description ? `<div class="cal-event-desc">${escapeHtml(ev.description)}</div>` : ''}
          </div>
        </div>`;
      });
      html += `</div>`;
    }

    html += `</div></div>`;
  });

  document.getElementById('calendarContent').innerHTML = html;
}

// ─── Archive / mode switch ───────────────────────────────────
function calModeTabsHtml() {
  const n = window._calArchivedCount || 0;
  return `<div class="tabs" id="calModeTabs">
    <button class="tab ${calMode === 'upcoming' ? 'active' : ''}" onclick="calSetMode('upcoming')">Upcoming</button>
    <button class="tab ${calMode === 'archived' ? 'active' : ''}" onclick="calSetMode('archived')">Archived <span style="opacity:0.5;margin-left:4px;font-size:0.7em">${n}</span></button>
  </div>`;
}

function renderCalToolbar() {
  const bar = document.getElementById('calFilterBar');
  if (!bar) return;
  bar.innerHTML = calModeTabsHtml() + (calMode === 'upcoming' ? (window._calCatTabsHtml || '') : '');
}

function renderCalArchiveNote(data) {
  const el = document.getElementById('calArchiveNote');
  if (!el) return;
  const n = data.archived_count || 0;
  el.innerHTML = n
    ? `Finished events are archived automatically as their dates pass — <a href="#calendar" onclick="calSetMode('archived');return false;" style="color:inherit;text-decoration:underline">${n} in the archive</a>.`
    : 'Finished events are archived automatically as their dates pass.';
}

async function calSetMode(mode) {
  calMode = mode;
  const note = document.getElementById('calArchiveNote');
  if (mode === 'archived') {
    if (note) note.innerHTML = '';
    await renderArchivedView();
  } else {
    renderCalToolbar();
    renderCalArchiveNote({ archived_count: window._calArchivedCount });
    renderCalGrid(window._calEvents || [], window._calActiveCat || 'all');
  }
}

function calRerender() {
  if (calMode === 'archived') renderArchivedView();
  else renderCalendar();
}

async function renderArchivedView() {
  const bar = document.getElementById('calFilterBar');
  const content = document.getElementById('calendarContent');
  const params = new URLSearchParams();
  if (window._calArchMonth) params.set('month', window._calArchMonth);
  if (window._calArchQuery) params.set('q', window._calArchQuery);

  let data;
  try {
    data = await fetch('/api/calendar/archived?' + params.toString()).then(r => r.json());
  } catch (err) {
    content.innerHTML = `<div class="empty-state"><div class="empty-state-title">Failed to load archive</div>
      <div class="empty-state-desc">${escapeHtml(err.message)}</div></div>`;
    return;
  }

  window._calArchivedCount = data.total || 0;

  let monthChips = `<button class="tab ${!window._calArchMonth ? 'active' : ''}" onclick="calArchMonth(null)">All months</button>`;
  (data.months || []).forEach(m => {
    const [y, mm] = m.month.split('-');
    const label = new Date(parseInt(y), parseInt(mm) - 1).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    monthChips += `<button class="tab ${window._calArchMonth === m.month ? 'active' : ''}" onclick="calArchMonth('${m.month}')">${label} <span style="opacity:0.5;margin-left:4px;font-size:0.7em">${m.count}</span></button>`;
  });

  bar.innerHTML = calModeTabsHtml() + `
    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:10px">
      <input class="form-input" id="calArchSearch" style="max-width:260px" placeholder="Search archived events..."
             value="${escapeHtml(window._calArchQuery)}"
             onkeydown="if(event.key==='Enter')calArchSearch(this.value)">
      <button class="btn btn-ghost btn-sm" onclick="calArchSearch(document.getElementById('calArchSearch').value)">Search</button>
      ${window._calArchQuery ? `<button class="btn btn-ghost btn-sm" onclick="calArchSearch('')">Clear</button>` : ''}
    </div>
    <div class="tabs" style="flex-wrap:wrap;margin-top:8px">${monthChips}</div>`;

  const events = data.events || [];
  if (events.length === 0) {
    content.innerHTML = `<div class="empty-state">
      <div class="empty-state-icon">—</div>
      <div class="empty-state-title">Nothing archived yet</div>
      <div class="empty-state-desc">${window._calArchQuery || window._calArchMonth
        ? 'No archived events match this filter.'
        : 'Events land here automatically once their dates have passed.'}</div>
    </div>`;
    return;
  }

  // Group by month, newest first, collapsed by default
  const months = {};
  events.forEach(ev => {
    const start = ev.start?.date || ev.start?.dateTime?.slice(0, 10) || 'unknown';
    const mk = start.slice(0, 7);
    if (!months[mk]) months[mk] = [];
    months[mk].push(ev);
  });

  let html = `<div style="font-size:0.72rem;color:var(--text-muted);margin-bottom:12px">
    ${data.count} archived event${data.count !== 1 ? 's' : ''}${window._calArchQuery || window._calArchMonth ? ' (filtered)' : ''} of ${data.total} — kept for reference.
  </div>`;

  Object.keys(months).sort().reverse().forEach(mk => {
    const [y, m] = mk.split('-');
    const monthName = new Date(parseInt(y), parseInt(m) - 1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    const monthEvents = months[mk].sort((a, b) => (b.start?.date || b.start?.dateTime || '').localeCompare(a.start?.date || a.start?.dateTime || ''));

    html += `<div class="cal-month collapsed">
      <div class="cal-month-header" onclick="this.parentElement.classList.toggle('collapsed')">
        <span class="cal-month-name">${monthName}</span>
        <span class="cal-month-count">${monthEvents.length} archived event${monthEvents.length !== 1 ? 's' : ''}</span>
      </div>
      <div class="cal-month-body">`;

    monthEvents.forEach(ev => {
      const cat = detectCategory(ev.summary);
      const catDef = CATEGORIES[cat] || { label: 'Other', color: '#6b7280' };
      const start = ev.start?.date || ev.start?.dateTime?.slice(0, 10) || '';
      const end = ev.end?.date || ev.end?.dateTime?.slice(0, 10) || '';
      const isMultiDay = end && end !== start;
      html += `<div class="cal-event" style="--event-color:${catDef.color};--event-bg:${hexToRgba(catDef.color, 0.06)}">
        <div class="cal-event-indicator" style="background:${catDef.color}"></div>
        <div class="cal-event-body">
          <div class="cal-event-title">${escapeHtml(cleanSummary(ev.summary))}</div>
          <div class="cal-event-meta">
            <span class="cal-event-date">${fmtDateRange(ev.start?.date || ev.start?.dateTime, ev.end?.date || ev.end?.dateTime)}</span>
            ${isMultiDay ? `<span class="cal-event-days">Multi-day</span>` : ''}
            <span class="cal-event-days" style="opacity:0.7">Archived</span>
          </div>
          ${ev.description ? `<div class="cal-event-desc">${escapeHtml((ev.description || '').trim())}</div>` : ''}
          <div style="margin-top:8px">
            <button class="btn btn-ghost btn-sm" onclick="calRestore('${ev.archive_key}')" title="Put this event back in the Upcoming list">Restore to list</button>
          </div>
        </div>
      </div>`;
    });

    html += `</div></div>`;
  });

  content.innerHTML = html;
}

function calArchSearch(v) {
  window._calArchQuery = (v || '').trim();
  renderArchivedView();
}

function calArchMonth(m) {
  window._calArchMonth = m;
  renderArchivedView();
}

async function calRestore(key) {
  if (!key) return;
  try {
    const res = await fetch('/api/calendar/archive/restore', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keys: [key] })
    });
    const out = await res.json();
    if (!out.ok) throw new Error(out.detail || 'restore failed');
    showToast('Event restored to the Upcoming list', 'success');
    await renderCalendar();
    await calSetMode('archived');
  } catch (err) {
    showToast('Restore failed: ' + err.message, 'error');
  }
}

// ─── Filter ──────────────────────────────────────────────────
function calFilter(cat) {
  window._calActiveCat = cat;
  // Update tabs
  document.querySelectorAll('#calFilterTabs .tab').forEach(t => t.classList.remove('active'));
  const tab = document.querySelector(`#calFilterTabs .tab[data-cat="${cat}"]`);
  if (tab) tab.classList.add('active');
  // Re-render
  renderCalGrid(window._calEvents || [], cat);
}

// ─── Escape ──────────────────────────────────────────────────
function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ═════════════════════════════════════════════════════════════════
//  TODO PANEL — reads /workspace/task-list.json via /api/crm/tasks (proxy-safe)
// ═════════════════════════════════════════════════════════════════

async function fetchTodosFromCrm() {
  try {
    const tasks = await fetch('/api/crm/tasks').then(r => r.json()).catch(() => []);
    window._todoItems = Array.isArray(tasks) ? tasks : [];
    renderTodoList();
  } catch {
    document.getElementById('todoList').innerHTML = '<div style="padding:12px;color:var(--text-muted);font-size:0.8rem">Could not load tasks</div>';
  }
}

async function loadTodos() {
  fetchTodosFromCrm();
}

function renderTodoList() {
  const items = window._todoItems || [];
  const container = document.getElementById('todoList');
  const countEl = document.getElementById('todoCount');
  // Helper functions — MUST be declared before use (TDZ-safe)
  const getStatus = (t) => t.status || t._status || 'pending';
  const isHighPriority = (t) => (t.content || t.title || '').includes('HIGH PRIORITY') || t.priority === 'high';
  const getContent = (t) => t.content || t.title || 'Untitled';

  const pending = items.filter(i => getStatus(i) !== 'completed' && getStatus(i) !== 'done');
  countEl.textContent = pending.length;

  if (items.length === 0) {
    container.innerHTML = '<div style="padding:12px;color:var(--text-muted);font-size:0.8rem">No tasks yet</div>';
    return;
  }

  const highPriorityItems = pending.filter(t => isHighPriority(t));
  const normalPending = pending.filter(t => !isHighPriority(t));
  const doneItems = items.filter(i => getStatus(i) === 'completed' || getStatus(i) === 'done');

  let html = '';

  if (highPriorityItems.length > 0) {
    html += '<div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.05em;color:var(--red);padding:8px 12px 4px">High Priority</div>';
    highPriorityItems.forEach(g => { html += todoItemHTML(g, false); });
  }

  normalPending.forEach(g => { html += todoItemHTML(g, false); });

  if (doneItems.length > 0) {
    html += `<div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.05em;color:var(--text-muted);padding:8px 12px 4px;margin-top:4px;border-top:1px solid var(--border)">Done (${doneItems.length})</div>`;
    doneItems.slice(0, 10).forEach(g => { html += todoItemHTML(g, true); });
  }
  container.innerHTML = html;
}

function todoItemHTML(t, done) {
  const raw = t.content || t.title || 'Untitled';
  const text = raw.replace(/^🔴\s*HIGH PRIORITY\s*[—–-]\s*/, '');
  const isHighPrio = raw.includes('HIGH PRIORITY') || t.priority === 'high';
  const tidyTitle = t.content && !t.title ? t.content : (t.title || t.content || 'Untitled');
  const displayText = tidyTitle.replace(/^🔴\s*HIGH PRIORITY\s*[—–-]\s*/, '');
  return `<div class="todo-item ${done ? 'done' : ''} ${isHighPrio && !done ? 'high-priority' : ''}">
    <button class="todo-check" onclick="toggleTodo('${t.id}', ${!done})" title="${done ? 'Undo' : 'Mark done'}">${done ? '&#8630;' : '&#9675;'}</button>
    <span class="todo-text">${escapeHtml(text)}</span>
    <button class="todo-del" onclick="deleteTodo('${t.id}')" title="Delete">&times;</button>
  </div>`;
}

async function addTodo() {
  const input = document.getElementById('todoNewInput');
  const content = input.value.trim();
  if (!content) return;
  input.value = '';
  try {
    await fetch('/api/crm/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, status: 'pending' })
    });
    await loadTodos();
  } catch (err) {
    alert('Failed to add task: ' + err.message);
  }
}

async function toggleTodo(id, complete) {
  try {
    await fetch(`/api/crm/tasks/${encodeURIComponent(id)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: complete ? 'completed' : 'pending' })
    });
    await loadTodos();
  } catch (err) {
    alert('Failed to update: ' + err.message);
  }
}

async function deleteTodo(id) {
  try {
    await fetch(`/api/crm/tasks/${encodeURIComponent(id)}`, { method: 'DELETE' });
    await loadTodos();
  } catch (err) {
    alert('Failed to delete: ' + err.message);
  }
}

function toggleTodoPanel() {
  const panel = document.getElementById('todoPanel');
  panel.classList.toggle('collapsed');
  const toggle = panel.querySelector('.todo-header-toggle');
  toggle.textContent = panel.classList.contains('collapsed') ? '▸' : '▾';
}
