/* ═══════════════════════════════════════════════════════════════════════
   Task List — full-page workspace for Shareef's to-do list.
   Backed by /api/brain/tasks-data (file: /workspace/task-list.json).
   Checkbox = PATCH by id (never rewrites the whole file).
   Layout: summary band → group chips → grouped rows, urgency-ordered.
   ═══════════════════════════════════════════════════════════════════ */

const TL_CATEGORIES = ['admin', 'scheduling', 'education', 'onboarding', 'finance', 'facilities', 'marketing', 'events', 'other'];
const TL_PRI = { high: 0, medium: 1, low: 2 };
// Map our due-date tones onto the platform's existing .badge variants.
const TL_BADGE = { overdue: 'danger', today: 'warning', soon: 'accent', future: 'info', done: 'success' };

let tlTasks = [];
let tlFilter = 'open';        // open | overdue | today | week | done | all
let tlCategory = null;        // null = every category
let tlQuery = '';
let tlLoading = false;

/* ── date helpers ─────────────────────────────────────────────────── */

function tlToday() { const d = new Date(); d.setHours(0, 0, 0, 0); return d; }

function tlDaysUntil(dateStr) {
  if (!dateStr) return null;
  const d = new Date(dateStr + 'T00:00:00');
  if (isNaN(d)) return null;
  return Math.round((d - tlToday()) / 86400000);
}

/** Human due-date chip: wording + severity class. */
function tlDue(dateStr, isDone) {
  const n = tlDaysUntil(dateStr);
  if (n === null) return null;
  const d = new Date(dateStr + 'T00:00:00');
  const short = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  if (isDone) return { label: short, tone: 'done', exact: dateStr };
  if (n < 0) return { label: `${short} · ${Math.abs(n)}d late`, tone: 'overdue', exact: dateStr };
  if (n === 0) return { label: `${short} · today`, tone: 'today', exact: dateStr };
  if (n === 1) return { label: `${short} · tomorrow`, tone: 'soon', exact: dateStr };
  if (n <= 7) return { label: `${short} · ${n}d`, tone: 'soon', exact: dateStr };
  return { label: short, tone: 'future', exact: dateStr };
}

function tlLongDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
}

/* ── data ─────────────────────────────────────────────────────────── */

async function tlFetch() {
  const r = await fetch('/api/brain/tasks-data', { headers: { Accept: 'application/json' } });
  if (!r.ok) throw new Error('HTTP ' + r.status);
  const j = await r.json();
  return Array.isArray(j.tasks) ? j.tasks : [];
}

async function renderTasks() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">Task List</h1>
        <p class="page-subtitle">Everything on your plate — due dates, detail, and a box to tick off</p>
      </div>
      <div class="btn-group">
        <button class="btn btn-sm" onclick="tlReload()">Refresh</button>
        <button class="btn btn-sm btn-primary" onclick="tlOpenAdd()">New task</button>
      </div>
    </div>
    <div id="tlBody"><div class="loading"><div class="loading-spinner"></div><span>Loading tasks…</span></div></div>
  `;
  tlFilter = 'open'; tlCategory = null; tlQuery = '';
  await tlReload();
}

async function tlReload() {
  if (tlLoading) return;
  tlLoading = true;
  try {
    tlTasks = await tlFetch();
    tlRender();
  } catch (err) {
    const body = document.getElementById('tlBody');
    if (body) body.innerHTML = `<div class="card"><div class="empty-state">
      <div class="empty-state-icon">!</div>
      <div class="empty-state-title">Could not load tasks</div>
      <div class="empty-state-desc">${escapeHtml(err.message)}</div>
      <button class="btn mt-3" onclick="tlReload()">Retry</button></div></div>`;
  } finally {
    tlLoading = false;
  }
}

/* ── filtering + grouping ─────────────────────────────────────────── */

function tlVisible() {
  const q = tlQuery.trim().toLowerCase();
  let list = tlTasks.slice();
  if (tlCategory) list = list.filter(t => (t.category || 'other') === tlCategory);

  const filter = tlFilter;
  if (filter === 'open') list = list.filter(t => t.status !== 'completed');
  else if (filter === 'done') list = list.filter(t => t.status === 'completed');
  else if (filter === 'overdue') list = list.filter(t => t.status !== 'completed' && tlDaysUntil(t.due_date) !== null && tlDaysUntil(t.due_date) < 0);
  else if (filter === 'today') list = list.filter(t => t.status !== 'completed' && tlDaysUntil(t.due_date) === 0);
  else if (filter === 'week') list = list.filter(t => { const n = tlDaysUntil(t.due_date); return t.status !== 'completed' && n !== null && n >= 0 && n <= 7; });

  if (q) list = list.filter(t => (t.content || '').toLowerCase().includes(q) || (t.category || '').toLowerCase().includes(q));

  list.sort((a, b) => {
    const aDone = a.status === 'completed', bDone = b.status === 'completed';
    if (aDone !== bDone) return aDone ? 1 : -1;
    if (aDone && bDone) {
      const ad = a.due_date || '', bd = b.due_date || '';
      if (ad !== bd) return bd.localeCompare(ad);
      return (a.content || '').localeCompare(b.content || '');
    }
    const an = tlDaysUntil(a.due_date), bn = tlDaysUntil(b.due_date);
    if ((an === null) !== (bn === null)) return an === null ? 1 : -1;   // dated first
    if (an !== null && bn !== null && an !== bn) return an - bn;         // soonest first
    return (TL_PRI[a.priority] ?? 1) - (TL_PRI[b.priority] ?? 1);
  });
  return list;
}

/** Bucket label for a row, so the page reads as sections not a flat list. */
function tlBucket(t) {
  if (t.status === 'completed') return 'Completed';
  const n = tlDaysUntil(t.due_date);
  if (n === null) return 'No date set';
  if (n < 0) return 'Overdue';
  if (n === 0) return 'Due today';
  if (n <= 7) return 'Next 7 days';
  if (n <= 31) return 'This month';
  return 'Later';
}
const TL_BUCKET_ORDER = ['Overdue', 'Due today', 'Next 7 days', 'This month', 'Later', 'No date set', 'Completed'];

/* ── render ───────────────────────────────────────────────────────── */

function tlRender() {
  const body = document.getElementById('tlBody');
  if (!body) return;

  const open = tlTasks.filter(t => t.status !== 'completed');
  const done = tlTasks.filter(t => t.status === 'completed');
  const overdue = open.filter(t => { const n = tlDaysUntil(t.due_date); return n !== null && n < 0; });
  const today = open.filter(t => tlDaysUntil(t.due_date) === 0);
  const soon = open.filter(t => { const n = tlDaysUntil(t.due_date); return n !== null && n > 0 && n <= 7; });

  // category tallies (open only) — drives the chips
  const catCounts = {};
  open.forEach(t => { const c = t.category || 'other'; catCounts[c] = (catCounts[c] || 0) + 1; });

  const chip = (key, label, count, extraCls) =>
    `<button class="tl-chip ${tlFilter === key ? 'on' : ''} ${extraCls || ''}" onclick="tlSetFilter('${key}')">` +
    `${escapeHtml(label)}${count !== undefined ? `<span class="tl-chip-n">${count}</span>` : ''}</button>`;

  let html = `
    <div class="tl-summary">
      <button class="tl-stat ${tlFilter === 'open' ? 'on' : ''}" onclick="tlSetFilter('open')">
        <span class="tl-stat-v">${open.length}</span><span class="tl-stat-l">Open</span></button>
      <button class="tl-stat ${overdue.length ? 'danger' : ''} ${tlFilter === 'overdue' ? 'on' : ''}" onclick="tlSetFilter('overdue')">
        <span class="tl-stat-v">${overdue.length}</span><span class="tl-stat-l">Overdue</span></button>
      <button class="tl-stat ${tlFilter === 'today' ? 'on' : ''}" onclick="tlSetFilter('today')">
        <span class="tl-stat-v">${today.length}</span><span class="tl-stat-l">Due today</span></button>
      <button class="tl-stat ${tlFilter === 'week' ? 'on' : ''}" onclick="tlSetFilter('week')">
        <span class="tl-stat-v">${soon.length}</span><span class="tl-stat-l">Next 7 days</span></button>
      <button class="tl-stat ${tlFilter === 'done' ? 'on' : ''}" onclick="tlSetFilter('done')">
        <span class="tl-stat-v">${done.length}</span><span class="tl-stat-l">Completed</span></button>
    </div>

    <div class="tl-toolbar">
      <div class="tl-chips">
        ${chip('all', 'All', tlTasks.length)}
        ${chip('open', 'Open', open.length)}
        ${chip('overdue', 'Overdue', overdue.length)}
        ${chip('today', 'Today', today.length)}
        ${chip('week', 'This week', soon.length)}
        ${chip('done', 'Done', done.length)}
      </div>
      <div class="tl-tools">
        <input id="tlSearch" class="form-input tl-search" type="search" placeholder="Search tasks…"
               value="${escapeHtml(tlQuery)}" oninput="tlSearch(this.value)">
        <select class="form-select tl-select" onchange="tlSetCategory(this.value)">
          <option value="">All categories</option>
          ${TL_CATEGORIES.filter(c => catCounts[c]).map(c =>
            `<option value="${c}" ${tlCategory === c ? 'selected' : ''}>${c} (${catCounts[c]})</option>`).join('')}
        </select>
      </div>
    </div>
    ${tlCategory ? `<div class="tl-scope">Showing only <strong>${escapeHtml(tlCategory)}</strong>
      <button class="tl-scope-x" onclick="tlSetCategory('')">clear</button></div>` : ''}
  `;

  const list = tlVisible();
  if (!list.length) {
    html += `<div class="card"><div class="empty-state">
      <div class="empty-state-title">${tlQuery ? 'No tasks match that search' : tlFilter === 'done' ? 'Nothing completed yet' : tlFilter === 'overdue' ? 'Nothing overdue' : 'Nothing here'}</div>
      <div class="empty-state-desc">${tlQuery || tlCategory ? 'Try clearing the filter above.' : 'You are all caught up.'}</div>
    </div></div>`;
    body.innerHTML = html;
    return;
  }

  // group into buckets, preserving the sort inside each
  const groups = {};
  list.forEach(t => { const b = tlBucket(t); (groups[b] = groups[b] || []).push(t); });

  TL_BUCKET_ORDER.forEach(b => {
    const rows = groups[b];
    if (!rows || !rows.length) return;
    const tone = b === 'Overdue' ? 'overdue' : b === 'Due today' ? 'today' : b === 'Next 7 days' ? 'soon' : b === 'Completed' ? 'done' : 'quiet';
    html += `<section class="tl-group">
      <div class="tl-group-head">
        <span class="tl-group-dot ${tone}"></span>
        <span class="tl-group-label">${escapeHtml(b)}</span>
        <span class="tl-group-count">${rows.length}</span>
      </div>
      <ul class="tl-rows">${rows.map(tlRow).join('')}</ul>
    </section>`;
  });

  body.innerHTML = html;
  const s = document.getElementById('tlSearch');
  if (s && tlQuery) { s.focus(); s.setSelectionRange(s.value.length, s.value.length); }
}

function tlRow(t) {
  const isDone = t.status === 'completed';
  const due = tlDue(t.due_date, isDone);
  const pri = isDone ? null : (t.priority || 'medium');
  const cat = t.category || 'other';
  const n = tlDaysUntil(t.due_date);
  const late = !isDone && n !== null && n < 0;

  return `<li class="tl-row ${isDone ? 'is-done' : ''} ${late ? 'is-late' : ''}">
    <label class="tl-check">
      <input type="checkbox" ${isDone ? 'checked' : ''}
             onchange="tlToggle('${escapeHtml(String(t.id))}', this.checked)">
    </label>
    <div class="tl-main">
      <div class="tl-text">${escapeHtml(t.content || '')}</div>
      <div class="tl-meta">
        ${due ? `<span class="badge badge-${TL_BADGE[due.tone]}" title="${escapeHtml(tlLongDate(due.exact))}">${escapeHtml(due.label)}</span>` : '<span class="tl-none">No due date</span>'}
        <span class="tl-sep">·</span>
        <span class="tl-cat">${escapeHtml(cat)}</span>
        ${pri ? `<span class="tl-sep">·</span><span class="tl-pri tl-pri-${pri}">${escapeHtml(pri)}</span>` : ''}
      </div>
    </div>
    <div class="tl-row-actions">
      <button class="tl-icon-btn" title="Edit" onclick="tlOpenEdit('${escapeHtml(String(t.id))}')">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
             <path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4z"/></svg>
      </button>
      <button class="tl-icon-btn danger" title="Delete" onclick="tlDelete('${escapeHtml(String(t.id))}')">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg>
      </button>
    </div>
  </li>`;
}

/* ── interactions ─────────────────────────────────────────────────── */

function tlSetFilter(k) { tlFilter = k; tlRender(); }
function tlSetCategory(c) { tlCategory = c || null; tlRender(); }

let tlSearchTimer = null;
function tlSearch(v) {
  tlQuery = v;
  clearTimeout(tlSearchTimer);
  tlSearchTimer = setTimeout(tlRender, 180);
}

async function tlToggle(taskId, checked) {
  const t = tlTasks.find(x => String(x.id) === String(taskId));
  if (t) t.status = checked ? 'completed' : 'pending';   // optimistic
  tlRender();
  try {
    const r = await fetch('/api/brain/tasks-data/' + encodeURIComponent(taskId), {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: checked ? 'completed' : 'pending' }),
    });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    if (typeof showToast === 'function') showToast(checked ? 'Marked complete' : 'Reopened', 'success');
    await tlReload();
  } catch (err) {
    if (typeof showToast === 'function') showToast('Could not save — reverted', 'error');
    await tlReload();
  }
}

async function tlDelete(taskId) {
  const t = tlTasks.find(x => String(x.id) === String(taskId));
  const label = t ? t.content.slice(0, 60) : 'this task';
  if (!confirm(`Delete this task?\n\n${label}`)) return;
  try {
    const rest = tlTasks.filter(x => String(x.id) !== String(taskId));
    const r = await fetch('/api/brain/tasks-data', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tasks: rest }),
    });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    if (typeof showToast === 'function') showToast('Task deleted', 'success');
    await tlReload();
  } catch (err) {
    if (typeof showToast === 'function') showToast('Could not delete', 'error');
  }
}

/* ── add / edit modal ─────────────────────────────────────────────── */

function tlModalShell(title, inner, onSave) {
  const c = document.getElementById('modalContainer');
  c.innerHTML = `
    <div class="modal-overlay" onclick="tlCloseModal()">
      <div class="modal" onclick="event.stopPropagation()">
        <div class="modal-header">
          <div class="modal-title">${escapeHtml(title)}</div>
          <button class="modal-close" onclick="tlCloseModal()">✕</button>
        </div>
        <div class="modal-body">${inner}</div>
        <div class="modal-footer">
          <button class="btn" onclick="tlCloseModal()">Cancel</button>
          <button class="btn btn-primary" id="tlSaveBtn">${escapeHtml(onSave)}</button>
        </div>
      </div>
    </div>`;
  setTimeout(() => { const e = document.getElementById('tlContent'); if (e) e.focus(); }, 80);
}

function tlCloseModal() { document.getElementById('modalContainer').innerHTML = ''; }

function tlFormFields(t) {
  t = t || {};
  return `
    <label class="tl-fl">Task</label>
    <textarea id="tlContent" class="modal-input tl-ta" placeholder="What needs to be done?">${escapeHtml(t.content || '')}</textarea>
    <div class="tl-fgrid">
      <div>
        <label class="tl-fl">Due date</label>
        <input type="date" id="tlDue" class="modal-input" value="${escapeHtml(t.due_date || '')}">
      </div>
      <div>
        <label class="tl-fl">Priority</label>
        <select id="tlPri" class="modal-input">
          <option value="high" ${t.priority === 'high' ? 'selected' : ''}>High</option>
          <option value="medium" ${t.priority !== 'high' && t.priority !== 'low' ? 'selected' : ''}>Medium</option>
          <option value="low" ${t.priority === 'low' ? 'selected' : ''}>Low</option>
        </select>
      </div>
      <div>
        <label class="tl-fl">Category</label>
        <select id="tlCat" class="modal-input">
          ${TL_CATEGORIES.map(c => `<option value="${c}" ${(t.category || 'admin') === c ? 'selected' : ''}>${c}</option>`).join('')}
        </select>
      </div>
    </div>`;
}

function tlOpenAdd() {
  tlModalShell('New task', tlFormFields({}), 'Create task');
  document.getElementById('tlSaveBtn').onclick = tlCreate;
}

async function tlCreate() {
  const content = document.getElementById('tlContent').value.trim();
  if (!content) { if (typeof showToast === 'function') showToast('Enter a task description', 'error'); return; }
  const task = {
    id: 'task-' + Date.now() + '-' + Math.random().toString(36).slice(2, 7),
    content,
    status: 'pending',
    priority: document.getElementById('tlPri').value,
    category: document.getElementById('tlCat').value,
  };
  const due = document.getElementById('tlDue').value;
  if (due) task.due_date = due;
  try {
    const r = await fetch('/api/brain/tasks-data', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tasks: tlTasks.concat([task]) }),
    });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    tlCloseModal();
    if (typeof showToast === 'function') showToast('Task created', 'success');
    await tlReload();
  } catch (err) {
    if (typeof showToast === 'function') showToast('Could not create task', 'error');
  }
}

function tlOpenEdit(taskId) {
  const t = tlTasks.find(x => String(x.id) === String(taskId));
  if (!t) return;
  tlModalShell('Edit task', tlFormFields(t), 'Save changes');
  document.getElementById('tlSaveBtn').onclick = () => tlSaveEdit(taskId);
}

async function tlSaveEdit(taskId) {
  const content = document.getElementById('tlContent').value.trim();
  if (!content) { if (typeof showToast === 'function') showToast('Task cannot be empty', 'error'); return; }
  const due = document.getElementById('tlDue').value;
  const patch = {
    content,
    priority: document.getElementById('tlPri').value,
    category: document.getElementById('tlCat').value,
    due_date: due || null,
  };
  try {
    const r = await fetch('/api/brain/tasks-data/' + encodeURIComponent(taskId), {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const local = tlTasks.find(x => String(x.id) === String(taskId));
    if (local) Object.assign(local, patch.status ? {} : {}, patch);
    if (local && !due) delete local.due_date;
    tlCloseModal();
    if (typeof showToast === 'function') showToast('Task updated', 'success');
    await tlReload();
  } catch (err) {
    if (typeof showToast === 'function') showToast('Could not save changes', 'error');
  }
}
