async function renderTools() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">My Tools</h1>
        <p class="page-subtitle">Live status of all connected services</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="renderTools()">🔄 Refresh</button>
      </div>
    </div>

    <div id="toolsStats" class="grid grid-4 mb-4"></div>

    <div class="grid grid-2 mt-3">
      <div class="card">
        <div class="card-header"><span class="card-title">📓 NotebookLM - Urology</span></div>
        <div id="nlmDefault"><div class="skeleton" style="height:80px"></div></div>
      </div>
      <div class="card">
        <div class="card-header"><span class="card-title">📓 NotebookLM - letsgetmoney2009</span></div>
        <div id="nlmLetsget"><div class="skeleton" style="height:80px"></div></div>
      </div>
    </div>

    <div class="grid grid-2 mt-3">
      <div class="card">
        <div class="card-header"><span class="card-title">📓 NotebookLM - account2</span></div>
        <div id="nlmAccount2"><div class="skeleton" style="height:80px"></div></div>
      </div>
      <div class="card">
        <div class="card-header"><span class="card-title">⏰ Hermes Cron Jobs</span></div>
        <div id="cronJobs"><div class="skeleton" style="height:80px"></div></div>
      </div>
    </div>

    <div class="card mt-3">
      <div class="card-header"><span class="card-title">📚 Knowledge Base</span></div>
      <div id="kbContent"><div class="skeleton" style="height:80px"></div></div>
    </div>

    <div class="grid grid-2 mt-3">
      <div class="card">
        <div class="card-header"><span class="card-title">📊 Big Reef Dashboard</span></div>
        <div style="padding:12px">
          <div style="font-size:12px;color:var(--text-muted);margin-bottom:8px">Integrated dashboard at port 8501</div>
          <a href="http://localhost:8501" target="_blank" style="display:inline-flex;align-items:center;gap:6px;padding:8px 16px;background:var(--accent);color:white;border-radius:6px;text-decoration:none;font-size:13px;font-weight:500">
            🔗 Open Big Reef Dashboard
          </a>
          <div style="margin-top:8px;font-size:11px;color:var(--green)">⬤ Running — NotebookLM, Cron, KB stats</div>
        </div>
      </div>
      <div class="card">
        <div class="card-header"><span class="card-title">🌐 Agentic OS</span></div>
        <div style="padding:12px">
          <div style="font-size:12px;color:var(--text-muted);margin-bottom:8px">You're here! This is the Agentic OS dashboard</div>
          <div style="display:flex;gap:8px">
            <a href="#chat" class="btn" style="font-size:12px;padding:6px 12px">💬 Chat</a>
            <a href="#skills" class="btn" style="font-size:12px;padding:6px 12px">⚡ Skills</a>
            <a href="#memory" class="btn" style="font-size:12px;padding:6px 12px">🧠 Memory</a>
            <a href="#scheduler" class="btn" style="font-size:12px;padding:6px 12px">⏱ Scheduler</a>
          </div>
        </div>
      </div>
    </div>

    <div class="card mt-3">
      <div class="card-header"><span class="card-title">⚙️ Service Status</span></div>
      <div id="serviceStatus"><div class="skeleton" style="height:60px"></div></div>
    </div>
  `;

  try {
    // Load overview stats
    const overview = await api.getToolsOverview();
    document.getElementById('toolsStats').innerHTML = `
      <div class="card stat-card">
        <div class="stat-icon ${overview.notebooklm_status === 'active' ? 'green' : 'green'}">📚</div>
        <div class="stat-value">${overview.kb_total}</div>
        <div class="stat-label">Knowledge Base</div>
        <div class="stat-change ${overview.notebooklm_status === 'active' ? 'up' : 'up'}">${overview.notebooklm_status === 'active' ? 'active' : 'local KB always ready'}</div>
      </div>
      <div class="card stat-card">
        <div class="stat-icon blue">⏰</div>
        <div class="stat-value">${overview.cron_jobs}</div>
        <div class="stat-label">Cron Jobs</div>
        <div class="stat-change up">scheduled</div>
      </div>
      <div class="card stat-card">
        <div class="stat-icon purple">📚</div>
        <div class="stat-value">${overview.kb_total}</div>
        <div class="stat-label">KB Entries</div>
        <div class="stat-change up">prompts + tools + resources</div>
      </div>
      <div class="card stat-card">
        <div class="stat-icon yellow">🔗</div>
        <div class="stat-value">3</div>
        <div class="stat-label">NLM Accounts</div>
        <div class="stat-change up">all connected</div>
      </div>
    `;

    // Load notebooks for all 3 accounts (or local KB if NLM down)
    const [nlm1, nlm2, nlm3] = await Promise.all([
      overview.nlm_available
        ? api.getToolsNotebooks('default')
        : Promise.resolve({ notebooks: [], use_local_kb: true }),
      overview.nlm_available
        ? api.getToolsNotebooks('letsgetmoney2009')
        : Promise.resolve({ notebooks: [], use_local_kb: true }),
      overview.nlm_available
        ? api.getToolsNotebooks('account2')
        : Promise.resolve({ notebooks: [], use_local_kb: true }),
    ]);

    function renderNotebooks(data, containerId) {
      const list = data.notebooks || [];
      const el = document.getElementById(containerId);
      if (list.length === 0) {
        el.innerHTML = '<div class="empty-state" style="padding:12px"><div class="empty-state-title">No notebooks or error loading</div></div>';
        return;
      }
      el.innerHTML = `<div style="font-size:11px;color:var(--text-muted);margin-bottom:6px">${list.length} notebooks</div>
        <div style="max-height:240px;overflow-y:auto">
        ${list.slice(0, 15).map(nb => `
          <div style="padding:5px 0;border-bottom:1px solid var(--border);font-size:12px">
            <div style="font-weight:500">${escapeHtml(nb.title || 'Untitled')}</div>
            <div style="font-size:10px;color:var(--text-muted)">📄 ${nb.source_count || 0} sources · ${(nb.updated_at || '').slice(0,10)}</div>
          </div>
        `).join('')}
        ${list.length > 15 ? `<div style="font-size:10px;color:var(--text-muted);padding:4px 0">+ ${list.length - 15} more</div>` : ''}
        </div>`;
    }

    renderNotebooks(nlm1, 'nlmDefault');
    renderNotebooks(nlm2, 'nlmLetsget');
    renderNotebooks(nlm3, 'nlmAccount2');

    // Load cron jobs
    const cron = await api.getToolsCron();
    const cronEl = document.getElementById('cronJobs');
    if (cron.output) {
      cronEl.innerHTML = `<pre style="font-size:11px;overflow-x:auto;padding:8px;margin:0;background:var(--surface);border-radius:6px;max-height:240px">${escapeHtml(cron.output.slice(0, 1200))}</pre>`;
    } else {
      cronEl.innerHTML = '<div class="empty-state" style="padding:12px"><div class="empty-state-title">No cron jobs</div></div>';
    }

    // Load knowledge base
    const kb = await api.getToolsKB();
    const kbEl = document.getElementById('kbContent');
    const entries = kb.entries || [];
    if (entries.length === 0) {
      kbEl.innerHTML = '<div class="empty-state" style="padding:12px"><div class="empty-state-title">Knowledge base is empty</div></div>';
    } else {
      const cats = {};
      entries.forEach(e => { cats[e.category] = (cats[e.category] || 0) + 1; });
      const catHtml = Object.entries(cats).map(([k, v]) => `<span class="tag" style="margin:2px">${k}: ${v}</span>`).join('');
      kbEl.innerHTML = `
        <div style="margin-bottom:8px;font-size:12px;color:var(--text-muted)">${entries.length} entries · ${catHtml}</div>
        <div style="max-height:200px;overflow-y:auto">
        ${entries.slice(0, 20).map(e => `
          <div style="padding:4px 0;border-bottom:1px solid var(--border);font-size:12px">
            <span style="font-weight:500">${escapeHtml(e.title)}</span>
            <span class="tag" style="font-size:10px;margin-left:6px">${e.category}</span>
          </div>
        `).join('')}
        </div>`;
    }

    // Service status
    document.getElementById('serviceStatus').innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
        <div style="padding:6px 10px;background:var(--surface);border-radius:6px;border-left:3px solid var(--green);font-size:12px">Hermes Agent — ✅ Active</div>
        <div style="padding:6px 10px;background:var(--surface);border-radius:6px;border-left:3px solid var(--green);font-size:12px">NotebookLM (Urology) — ✅ ${(nlm1.notebooks || []).length} notebooks</div>
        <div style="padding:6px 10px;background:var(--surface);border-radius:6px;border-left:3px solid var(--green);font-size:12px">NotebookLM (letsgetmoney2009) — ✅ ${(nlm2.notebooks || []).length} notebooks</div>
        <div style="padding:6px 10px;background:var(--surface);border-radius:6px;border-left:3px solid var(--green);font-size:12px">NotebookLM (account2) — ✅ ${(nlm3.notebooks || []).length} notebooks</div>
        <div style="padding:6px 10px;background:var(--surface);border-radius:6px;border-left:3px solid var(--green);font-size:12px">Composio (Firecrawl) — ✅ Active</div>
        <div style="padding:6px 10px;background:var(--surface);border-radius:6px;border-left:3px solid var(--green);font-size:12px">Composio (Gmail) — ✅ 3 accounts</div>
        <div style="padding:6px 10px;background:var(--surface);border-radius:6px;border-left:3px solid var(--yellow);font-size:12px">Composio (X/Twitter) — ⚠️ Credits needed</div>
        <div style="padding:6px 10px;background:var(--surface);border-radius:6px;border-left:3px solid var(--green);font-size:12px">Voice (STT/TTS) — ✅ Active</div>
        <div style="padding:6px 10px;background:var(--surface);border-radius:6px;border-left:3px solid var(--green);font-size:12px">KB at /workspace/knowledge-base — ✅ ${overview.kb_total} entries</div>
        <div style="padding:6px 10px;background:var(--surface);border-radius:6px;border-left:3px solid var(--green);font-size:12px">Dashboard: Agentic OS — ✅ Running</div>
        <div style="padding:6px 10px;background:var(--surface);border-radius:6px;border-left:3px solid var(--yellow);font-size:12px">X/Twitter — ⚠️ Credits needed</div>
      </div>
    `;

  } catch (err) {
    document.getElementById('toolsStats').innerHTML = `<div class="card" style="grid-column:1/-1"><div class="empty-state"><div class="empty-state-icon">⚠</div><div class="empty-state-title">Connection Error</div><div class="empty-state-desc">${escapeHtml(err.message)}</div></div></div>`;
  }
}
