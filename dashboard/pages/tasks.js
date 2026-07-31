/* ═══════════════════════════════════════════════════════════════════════
   Tasks — Full Task List Dashboard
   Loads from /workspace/task-list.json via API, toggle status inline.
   ═══════════════════════════════════════════════════════════════════ */

async function renderTasks() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">Tasks</div>
        <div class="page-subtitle">Your task list — toggle to mark done, filter by status</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-primary btn-sm" onclick="showAddTaskModal()">+ New Task</button>
        <button class="btn btn-ghost btn-sm" onclick="renderTasks()">🔄 Refresh</button>
      </div>
    </div>
    <div class="flex gap-3" style="margin-bottom:16px;flex-wrap:wrap">
      <div class="btn-group">
        <button class="filter-btn filter-btn-all active" data-filter="all" onclick="setTaskFilter('all')">All</button>
        <button class="filter-btn" data-filter="pending" onclick="setTaskFilter('pending')">Pending</button>
        <button class="filter-btn" data-filter="completed" onclick="setTaskFilter('completed')">Done</button>
      </div>
      <div class="btn-group">
        <button class="filter-btn sort-btn active" data-sort="priority" onclick="setTaskSort('priority')">By Priority</button>
        <button class="sort-btn" data-sort="due" onclick="setTaskSort('due')">By Due Date</button>
        <button class="sort-btn" data-sort="category" onclick="setTaskSort('category')">By Category</button>
      </div>
    </div>
    <div id="taskStats" class="grid grid-4 mb-4"></div>
    <div id="taskList" class="task-list"></div>
  `;

  window._taskFilter = 'all';
  window._taskSort = 'priority';
  await loadAndRenderTasks();
}

async function loadAndRenderTasks() {
  try {
    const res = await fetch('/api/brain/tasks-data');
    const data = await res.json();
    const tasks = data.tasks || [];

    // Stats
    const total = tasks.length;
    const pending = tasks.filter(t => t.status === 'pending').length;
    const done = tasks.filter(t => t.status === 'completed').length;
    const highUrgent = tasks.filter(t => t.status === 'pending' && t.priority === 'high').length;

    document.getElementById('taskStats').innerHTML = `
      <div class="stat-card">
        <div class="stat-icon" style="color:var(--accent)">📋</div>
        <div class="stat-value">${total}</div>
        <div class="stat-label">Total Tasks</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="color:var(--yellow)">⏳</div>
        <div class="stat-value">${pending}</div>
        <div class="stat-label">Pending</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="color:var(--green)">✅</div>
        <div class="stat-value">${done}</div>
        <div class="stat-label">Completed</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="color:var(--red)">🔴</div>
        <div class="stat-value">${highUrgent}</div>
        <div class="stat-label">High Priority</div>
      </div>
    `;

    renderTaskList(tasks);
  } catch (err) {
    document.getElementById('taskList').innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">⚠</div>
        <div class="empty-state-title">Failed to load tasks</div>
        <div class="empty-state-desc">${err.message}</div>
      </div>`;
  }
}

function renderTaskList(tasks) {
  const filter = window._taskFilter || 'all';
  const sort = window._taskSort || 'priority';

  let filtered = tasks;
  if (filter === 'pending') filtered = tasks.filter(t => t.status === 'pending');
  else if (filter === 'completed') filtered = tasks.filter(t => t.status === 'completed');

  // Sort
  const priorityOrder = { high: 0, medium: 1, low: 2 };
  if (sort === 'priority') {
    filtered.sort((a, b) => {
      const pa = priorityOrder[a.priority] ?? 1;
      const pb = priorityOrder[b.priority] ?? 1;
      if (pa !== pb) return pa - pb;
      if (a.status !== b.status) return a.status === 'pending' ? -1 : 1;
      return 0;
    });
  } else if (sort === 'due') {
    filtered.sort((a, b) => {
      if (!a.due_date) return 1;
      if (!b.due_date) return -1;
      return a.due_date.localeCompare(b.due_date);
    });
  } else if (sort === 'category') {
    filtered.sort((a, b) => (a.category || '').localeCompare(b.category || ''));
  }

  const list = document.getElementById('taskList');
  if (filtered.length === 0) {
    list.innerHTML = `<div class="empty-state"><div class="empty-state-icon">🎯</div><div class="empty-state-title">${
      filter === 'completed' ? 'No completed tasks' : filter === 'pending' ? 'Nothing pending! 🎉' : 'No tasks yet'
    }</div><div class="empty-state-desc">${
      filter === 'all' ? 'Your task list is empty — click "+ New Task" to add one' : 'Try changing the filter'
    }</div></div>`;
    return;
  }

  list.innerHTML = filtered.map(t => {
    const isDone = t.status === 'completed';
    const priColor = t.priority === 'high' ? 'var(--red)' : t.priority === 'medium' ? 'var(--yellow)' : 'var(--text-muted)';
    const cat = t.category || 'other';
    const due = t.due_date ? `<span class="task-due ${isOverdue(t.due_date) && !isDone ? 'overdue' : ''}">📅 ${t.due_date}</span>` : '';

    return `
      <div class="task-item ${isDone ? 'task-done' : ''}" data-task-id="${escapeHtml(t.id)}">
        <button class="task-toggle" onclick="toggleTaskStatus('${escapeHtml(t.id)}')" title="${isDone ? 'Mark pending' : 'Mark done'}">
          ${isDone ? '✅' : '⬜'}
        </button>
        <div class="task-body">
          <div class="task-content">${escapeHtml(t.content)}</div>
          <div class="task-meta">
            <span class="task-priority" style="color:${priColor}">● ${t.priority}</span>
            <span class="task-category">🏷 ${cat}</span>
            ${due}
          </div>
        </div>
        <div class="task-actions">
          <button class="btn btn-ghost btn-xs" onclick="deleteTask('${escapeHtml(t.id)}')" title="Delete">✕</button>
        </div>
      </div>`;
  }).join('');
}

function isOverdue(dateStr) {
  if (!dateStr) return false;
  const d = new Date(dateStr);
  const now = new Date();
  return d < now;
}

function setTaskFilter(filter) {
  window._taskFilter = filter;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.toggle('active', b.dataset.filter === filter));
  loadAndRenderTasks();
}

function setTaskSort(sort) {
  window._taskSort = sort;
  document.querySelectorAll('.sort-btn').forEach(b => b.classList.toggle('active', b.dataset.sort === sort));
  loadAndRenderTasks();
}

async function toggleTaskStatus(taskId) {
  try {
    const res = await fetch('/api/brain/tasks-data');
    const data = await res.json();
    const tasks = data.tasks || [];
    const task = tasks.find(t => t.id === taskId);
    if (!task) throw new Error('Task not found');
    const newStatus = task.status === 'completed' ? 'pending' : 'completed';
    const patchRes = await fetch(`/api/brain/tasks-data/${encodeURIComponent(taskId)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus }),
    });
    if (!patchRes.ok) throw new Error('Failed to toggle');
    await loadAndRenderTasks();
  } catch (err) {
    showToast('Failed to update task', 'error');
  }
}

async function deleteTask(taskId) {
  if (!confirm('Delete this task?')) return;
  try {
    const res = await fetch('/api/brain/tasks-data');
    const data = await res.json();
    const tasks = (data.tasks || []).filter(t => t.id !== taskId);
    await fetch('/api/brain/tasks-data', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tasks }),
    });
    await loadAndRenderTasks();
    showToast('Task deleted', 'success');
  } catch (err) {
    showToast('Failed to delete task', 'error');
  }
}

/* ─── Add Task Modal ──────────────────────────────────────────── */

function showAddTaskModal() {
  const container = document.getElementById('modalContainer');
  container.innerHTML = `
    <div class="modal-overlay" onclick="closeAddTaskModal()">
      <div class="modal" onclick="event.stopPropagation()">
        <div class="modal-header">
          <div class="modal-title">New Task</div>
          <button class="modal-close" onclick="closeAddTaskModal()">✕</button>
        </div>
        <div class="modal-body">
          <label style="display:block;margin-bottom:6px;font-size:13px;color:var(--text-muted)">Task description</label>
          <textarea id="newTaskContent" class="modal-input" style="width:100%;min-height:80px;resize:vertical;padding:10px 12px" placeholder="What needs to be done?"></textarea>

          <div class="flex gap-3" style="margin-top:14px">
            <div style="flex:1">
              <label style="display:block;margin-bottom:4px;font-size:12px;color:var(--text-muted)">Priority</label>
              <select id="newTaskPriority" class="modal-input" style="width:100%">
                <option value="high">High</option>
                <option value="medium" selected>Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            <div style="flex:1">
              <label style="display:block;margin-bottom:4px;font-size:12px;color:var(--text-muted)">Category</label>
              <select id="newTaskCategory" class="modal-input" style="width:100%">
                <option value="admin">Admin</option>
                <option value="scheduling">Scheduling</option>
                <option value="education">Education</option>
                <option value="onboarding">Onboarding</option>
                <option value="finance">Finance</option>
                <option value="facilities">Facilities</option>
                <option value="marketing">Marketing</option>
                <option value="events">Events</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div style="flex:1">
              <label style="display:block;margin-bottom:4px;font-size:12px;color:var(--text-muted)">Due date</label>
              <input type="date" id="newTaskDue" class="modal-input" style="width:100%">
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" onclick="closeAddTaskModal()">Cancel</button>
          <button class="btn btn-primary" onclick="createNewTask()">Create Task</button>
        </div>
      </div>
    </div>
  `;

  // Focus the textarea
  setTimeout(() => document.getElementById('newTaskContent').focus(), 100);
}

function closeAddTaskModal() {
  document.getElementById('modalContainer').innerHTML = '';
}

async function createNewTask() {
  const content = document.getElementById('newTaskContent').value.trim();
  if (!content) {
    showToast('Please enter a task description', 'error');
    return;
  }

  const priority = document.getElementById('newTaskPriority').value;
  const category = document.getElementById('newTaskCategory').value;
  const due = document.getElementById('newTaskDue').value;

  const id = 'task-' + Date.now() + '-' + Math.random().toString(36).slice(2, 8);

  try {
    const res = await fetch('/api/brain/tasks-data');
    const data = await res.json();
    const tasks = data.tasks || [];

    const newTask = { id, content, status: 'pending', priority, category };
    if (due) newTask.due_date = due;

    tasks.push(newTask);

    await fetch('/api/brain/tasks-data', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tasks }),
    });

    closeAddTaskModal();
    await loadAndRenderTasks();
    showToast('Task created', 'success');
  } catch (err) {
    showToast('Failed to create task: ' + err.message, 'error');
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
