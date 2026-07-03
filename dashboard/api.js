const api = {
  async get(path) {
    const r = await fetch(path);
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || `Request failed: ${r.status}`); }
    return r.json();
  },
  async post(path, body = {}, controller) {
    const opts = { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
    if (controller) opts.signal = controller.signal;
    const r = await fetch(path, opts);
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || `Request failed: ${r.status}`); }
    return r.json();
  },
  async put(path, body = {}) {
    const r = await fetch(path, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || `Request failed: ${r.status}`); }
    return r.json();
  },
  async patch(path, body = {}) {
    const r = await fetch(path, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || `Request failed: ${r.status}`); }
    return r.json();
  },
  async del(path) {
    const r = await fetch(path, { method: 'DELETE' });
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || `Request failed: ${r.status}`); }
    return r.json();
  },
  getStatus: () => api.get('/api/status'),
  getHealthFull: () => api.get('/api/health/full'),
  processSwap: (dryRun = true) => api.post(`/api/swap/process?dry_run=${dryRun}`),
  getBrain: () => api.get('/api/brain'),
  getBrainFile: (name) => api.get(`/api/brain/${encodeURIComponent(name)}`),
  updateBrainFile: (name, content) => api.put(`/api/brain/${encodeURIComponent(name)}`, { content }),
  getSkills: () => api.get('/api/skills'),
  getSkill: (name) => api.get(`/api/skills/${encodeURIComponent(name)}`),
  runSkill: (name, input = '', agent = 'auto') => api.post(`/api/skills/${encodeURIComponent(name)}/run`, { input, agent }),
  getSkillEval: (name) => api.get(`/api/skills/${encodeURIComponent(name)}/eval`),
  getJobs: () => api.get('/api/scheduler/jobs'),
  createJob: (job) => api.post('/api/scheduler/jobs', job),
  deleteJob: (id) => api.del(`/api/scheduler/jobs/${encodeURIComponent(id)}`),
  getAudit: (limit = 100) => api.get(`/api/audit?limit=${limit}`),
  getCost: () => api.get('/api/cost'),
  recordCost: (data) => api.post('/api/cost/record', data),
  getPlugins: () => api.get('/api/plugins'),
  installPlugin: (name) => api.post('/api/plugins/install', { name }),
  getBackups: () => api.get('/api/backups'),
  createBackup: () => api.post('/api/backup'),
  restoreBackup: (file) => api.post('/api/backup/restore', { file }),
  getPrompts: () => api.get('/api/prompts'),
  getSettings: () => api.get('/api/settings'),
  updateSettings: (settings) => api.put('/api/settings', { settings }),
  getStandards: () => api.get('/api/standards'),
  discoverStandards: () => api.post('/api/standards/discover'),
  chat: (agent, message, controller) => api.post('/api/chat', { agent, message }, controller),
  getChatHistory: () => api.get('/api/chat/history'),
  // Kanban
  getKanbanBoard: (status) => api.get(status ? `/api/kanban/board?status=${encodeURIComponent(status)}` : '/api/kanban/board'),
  getKanbanTask: (id) => api.get(`/api/kanban/tasks/${encodeURIComponent(id)}`),
  createKanbanTask: (data) => api.post('/api/kanban/tasks', data),
  updateKanbanTask: (id, data) => api.patch(`/api/kanban/tasks/${encodeURIComponent(id)}`, data),
  completeKanbanTask: (id, summary) => api.post(`/api/kanban/tasks/${encodeURIComponent(id)}/complete`, { summary }),
  blockKanbanTask: (id, reason) => api.post(`/api/kanban/tasks/${encodeURIComponent(id)}/block`, { reason }),
  unblockKanbanTask: (id) => api.post(`/api/kanban/tasks/${encodeURIComponent(id)}/unblock`, {}),
  addKanbanComment: (id, message) => api.post(`/api/kanban/tasks/${encodeURIComponent(id)}/comments`, { message }),
  linkKanbanTasks: (parentId, childId) => api.post('/api/kanban/links', { parent_id: parentId, child_id: childId }),
  unlinkKanbanTasks: (parentId, childId) => api.del(`/api/kanban/links?parent_id=${encodeURIComponent(parentId)}&child_id=${encodeURIComponent(childId)}`),
  dispatchKanban: () => api.post('/api/kanban/dispatch', {}),
  specifyKanbanTask: (id) => api.post(`/api/kanban/tasks/${encodeURIComponent(id)}/specify`, {}),
  decomposeKanbanTask: (id) => api.post(`/api/kanban/tasks/${encodeURIComponent(id)}/decompose`, {}),
  deleteKanbanTask: (id) => api.del(`/api/kanban/tasks/${encodeURIComponent(id)}`),
  // Goals
  getGoals: () => api.get('/api/goals'),
  createGoal: (data) => api.post('/api/goals', data),
  updateGoal: (id, data) => api.put(`/api/goals/${encodeURIComponent(id)}`, data),
  deleteGoal: (id) => api.del(`/api/goals/${encodeURIComponent(id)}`),
  // Journal
  getJournalEntries: () => api.get('/api/journal/entries'),
  getJournalEntry: (date) => api.get(`/api/journal/entries/${encodeURIComponent(date)}`),
  saveJournalEntry: (date, content) => api.put(`/api/journal/entries/${encodeURIComponent(date)}`, { content }),
  searchJournal: (query) => api.get(`/api/journal/search?q=${encodeURIComponent(query)}`),
  // Agent Health
  getAgentHealth: () => api.get('/api/agents/health'),
  getAgentStats: (name) => api.get(`/api/agents/${encodeURIComponent(name)}/stats`),
  refreshAgentHealth: () => api.post('/api/agents/health/refresh', {}),
  // Smart Router
  suggestRouter: (task) => api.post('/api/router/suggest', { task }),
  routeTask: (task, agent) => api.post('/api/router/route', { task, agent }),
  getRouterConfig: () => api.get('/api/router/config'),
  // Learning Analytics - with normalization for canonical contract
  getSkillAnalytics: async () => {
    const data = await api.get('/api/analytics/skills');
    // Normalize to canonical shape: { skills: [{ name, score, evals, best, ... }] }
    const skills = (data.skills || []).map(s => ({
      name: s.name || 'unknown',
      score: typeof s.score === 'number' ? s.score : (typeof s.avg_score === 'number' ? s.avg_score / 100 : 0),
      evals: typeof s.evals === 'number' ? s.evals : (typeof s.total_runs === 'number' ? s.total_runs : 0),
      best: typeof s.best === 'number' ? s.best : (typeof s.last_score === 'number' ? s.last_score / 100 : 0),
      // Pass through any extra fields
      ...s
    }));
    return { skills, error: data.error };
  },
  getTrendAnalytics: async () => {
    const data = await api.get('/api/analytics/trends');
    // Normalize to canonical shape: { trends: { skillName: [scores...], ... } }
    let trends = {};
    if (Array.isArray(data.trends)) {
      // Convert array to map
      data.trends.forEach(t => {
        if (t.name) {
          trends[t.name] = t.scores || [];
        }
      });
    } else if (data.trends && typeof data.trends === 'object') {
      trends = data.trends;
    }
    return { trends, error: data.error };
  },
  // Session Replay - with normalization for canonical contract
  listSessions: async () => {
    const data = await api.get('/api/sessions/list');
    // Normalize sessions to have a renderable date field
    const sessions = (data.sessions || []).map(s => ({
      ...s,
      date: s.date || s.modified || new Date().toISOString()
    }));
    return { sessions, error: data.error };
  },
  getSessionReplay: async (id) => {
    const data = await api.get(`/api/sessions/${encodeURIComponent(id)}/replay`);
    // Normalize messages to objects with role/content/timestamp
    let messages = [];
    if (Array.isArray(data.messages)) {
      messages = data.messages.map(m => {
        if (typeof m === 'string') {
          // Parse string messages like "user: ..." or "assistant: ..."
          const match = m.match(/^(user|assistant|human|ai):\s*(.+)$/i);
          if (match) {
            return {
              role: match[1].toLowerCase() === 'human' ? 'user' : match[1].toLowerCase(),
              content: match[2],
              timestamp: data.timestamp || new Date().toISOString()
            };
          }
          return { role: 'unknown', content: m, timestamp: data.timestamp || new Date().toISOString() };
        }
        return {
          role: m.role || 'unknown',
          content: m.content || m.message || String(m),
          timestamp: m.timestamp || data.timestamp || new Date().toISOString()
        };
      });
    }
    return {
      session: data.session || { id, created_at: data.timestamp },
      messages,
      error: data.error
    };
  },
  // Tools Integration
  getToolsOverview: () => api.get('/api/tools/overview'),
  getToolsNotebooks: (profile = 'default') => api.get(`/api/tools/notebooks?profile=${encodeURIComponent(profile)}`),
  refreshToolsNotebooks: () => api.post('/api/tools/notebooks/refresh', {}),
  getToolsCron: () => api.get('/api/tools/cron'),
  getToolsKB: () => api.get('/api/tools/kb'),
  getTelegramSessions: () => api.get('/api/tools/telegram'),
  // CRM
  getContacts: () => api.get('/api/crm/contacts'),
  addContact: (data) => api.post('/api/crm/contacts', data),
  updateContact: (id, data) => api.put(`/api/crm/contacts/${encodeURIComponent(id)}`, data),
  deleteContact: (id) => api.del(`/api/crm/contacts/${encodeURIComponent(id)}`),
  getCrmAccessLog: () => api.get('/api/crm/access-log'),
  clearCrmAccessLog: () => api.post('/api/crm/access-log/clear?confirm=true', {}),
  // On Call Schedule
  getOncallNow: () => api.get('/api/oncall/now'),
  getOncallByDate: (date) => api.get(`/api/oncall/date?date=${encodeURIComponent(date)}`),
  getOncallByWeek: (start) => api.get(`/api/oncall/week?start=${encodeURIComponent(start)}`),
  getOncallSchedule: () => api.get('/api/oncall/schedule'),
  searchOncall: (date) => api.get(`/api/oncall/search?date=${encodeURIComponent(date)}`),
  // GME Tracker
  getGmeSummary: (ay) => api.get(`/api/crm/gme/summary${ay ? `?ay=${encodeURIComponent(ay)}` : ''}`),
  getGmeResidents: (ay) => api.get(`/api/crm/gme/residents${ay ? `?ay=${encodeURIComponent(ay)}` : ''}`),
  addReimbursement: (data) => api.post('/api/crm/gme/reimbursement', data),
  // Email
  sendEmail: (data) => api.post('/api/email/send', data),
  getEmailTemplates: () => api.get('/api/email/templates'),
  createEmailTemplate: (data) => api.post('/api/email/templates', data),
  deleteEmailTemplate: (name) => api.del(`/api/email/templates/${encodeURIComponent(name)}`),
  scheduleEmail: (data) => api.post('/api/email/schedule', data),
  // Drive Sync
  syncDrive: () => api.post('/api/drive/sync'),
  getDriveSyncStatus: () => api.get('/api/drive/sync/status'),
  // Voice Data Health
  getVapiDataHealth: () => api.get('/api/vapi/data-health'),
  // Reports
  getReportTypes: () => api.get('/api/reports/types'),
  generateReport: (data) => api.post('/api/reports/generate', data),
  // Selftest
  selfTest: () => api.get('/api/selftest'),
  // Auth
  login:          (email, password)           => api.post('/api/auth/login',           { email, password }),
  logout:         ()                          => api.post('/api/auth/logout',           {}),
  getMe:          ()                          => api.get('/api/auth/me'),
  changePassword: (current_password, new_password) => api.post('/api/auth/change-password', { current_password, new_password }),
  // Images → PDF
  imagesToPdf:    (formData)                  => fetch('/api/pdf/images2pdf', { method: 'POST', body: formData }),
};
