// ──────────────────────────────────────────────────────────────
// Distribution — full-width recipient manager
// Consolidates all email distribution groups (Faculty, Residents,
// Supervisors, Grand Rounds, ...) into one roomy tab with a
// name search + category + per-person checkbox picker.
// Reads/writes via /api/crm/email-groups.
// ──────────────────────────────────────────────────────────────

// CSS.escape polyfill (matches email-groups.js)
if (!CSS.escape) {
  CSS.escape = function(s) { return s.replace(/[^a-zA-Z0-9-]/g, '\\$&'); };
}

let distContacts = [];      // all non-archived CRM contacts
let distGroups = {};        // saved groups key -> {label, emails, test_mode, test_email, attendance_link}
let distActive = '';        // currently selected group key
let distSearch = '';        // name search filter
let distCat = '';           // category filter

async function renderDistribution() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">Distribution Lists</h1>
        <p class="page-subtitle">Manage every recipient group (faculty, residents, supervisors, conference lists) — full-width, searchable, from the CRM</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="renderDistribution()">↻ Refresh</button>
      </div>
    </div>

    <!-- Group tabs -->
    <div id="distTabs" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px;border-bottom:1px solid var(--border,#334155);padding-bottom:10px">Loading groups...</div>

    <div id="distPanel" style="width:100%">
      <div class="loading"><div class="loading-spinner"></div><span>Loading contacts...</span></div>
    </div>
  `;
  await loadDistribution();
}

async function loadDistribution() {
  try {
    const [crm, groups] = await Promise.all([
      api.get('/api/crm/contacts'),
      api.get('/api/crm/email-groups')
    ]);
    distContacts = (crm.contacts || []).filter(c => !c.archived);
    distGroups = groups || {};
    if (!distActive || !distGroups[distActive]) {
      distActive = Object.keys(distGroups)[0] || '';
    }
    renderDistTabs();
    renderDistPanel();
  } catch (err) {
    const panel = document.getElementById('distPanel');
    if (panel) panel.innerHTML = `<div class="empty-state"><div class="empty-state-icon">!</div><div class="empty-state-title">Error</div><div class="empty-state-desc">${escapeHtml(err.message)}</div></div>`;
  }
}

function renderDistTabs() {
  const tabs = document.getElementById('distTabs');
  if (!tabs) return;
  tabs.innerHTML = Object.keys(distGroups).map(key => {
    const g = distGroups[key];
    const count = (g.emails || []).length;
    const active = key === distActive;
    return `<button
        onclick="distActive='${key}';renderDistTabs();renderDistPanel()"
        style="padding:7px 14px;border-radius:8px;border:1px solid ${active ? 'var(--accent,#60a5fa)' : 'var(--border,#334155)'};background:${active ? 'rgba(96,165,250,0.12)' : 'transparent'};color:${active ? '#93c5fd' : 'var(--muted,#94a3b8)'};font-size:13px;font-weight:600;cursor:pointer">
        ${escapeHtml(g.label || key)} <span style="opacity:.7;font-weight:400">(${count})</span>
      </button>`;
  }).join('');
}

function renderDistPanel() {
  const panel = document.getElementById('distPanel');
  if (!panel) return;
  if (!distGroups[distActive]) {
    panel.innerHTML = `<div class="empty-state"><div class="empty-state-title">No groups</div><div class="empty-state-desc">Create a group in the CRM data or via the API.</div></div>`;
    return;
  }

  const group = distGroups[distActive];
  const savedEmails = new Set((group.emails || []).map(e => e.toLowerCase()));

  // Build category -> contacts map
  const byCategory = {};
  for (const c of distContacts) {
    const cat = c.category || 'Uncategorized';
    if (!byCategory[cat]) byCategory[cat] = [];
    byCategory[cat].push(c);
  }

  const modeColor = group.test_mode ? '#f59e0b' : '#10b981';
  const modeLabel = group.test_mode ? 'TEST MODE' : 'LIVE';

  panel.innerHTML = `
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:16px">
      <div class="card" style="padding:14px 16px"><div style="font-size:12px;color:var(--muted)">Selected</div><div id="distSelectedCount" style="font-size:22px;font-weight:700">${savedEmails.size}</div></div>
      <div class="card" style="padding:14px 16px"><div style="font-size:12px;color:var(--muted)">Contacts in CRM</div><div style="font-size:22px;font-weight:700">${distContacts.length}</div></div>
      <div class="card" style="padding:14px 16px"><div style="font-size:12px;color:var(--muted)">Mode</div><div style="font-size:14px;font-weight:700;color:${group.test_mode ? '#f59e0b' : '#10b981'}">${group.test_mode ? 'Test' : 'Live'}</div></div>
      <div class="card" style="padding:14px 16px"><div style="font-size:12px;color:var(--muted)">Label</div><div style="font-size:13px;font-weight:600">${escapeHtml(group.label || distActive)}</div></div>
    </div>

    <div class="card" style="padding:18px">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:12px">
        <div style="font-size:16px;font-weight:700">${escapeHtml(group.label || 'Recipients')}</div>
        <span style="background:${modeColor};color:#fff;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600">${modeLabel}</span>
      </div>

      <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px">
        <input type="text" id="distSearch" placeholder="⌕ Search by name or email..." value="${escapeHtml(distSearch)}"
          oninput="distSearch=this.value;renderDistContacts()"
          style="flex:1;min-width:220px;padding:9px 12px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text);font-size:13px">
        <select id="distCatSel" onchange="distCat=this.value;renderDistContacts()" style="padding:9px 12px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text);font-size:13px">
          <option value="">All categories</option>
          ${Object.keys(byCategory).sort().map(cat => `<option value="${escapeHtml(cat)}" ${distCat === cat ? 'selected' : ''}>${escapeHtml(cat)} (${byCategory[cat].length})</option>`).join('')}
        </select>
        <button class="btn btn-sm" onclick="selectAllVisible()">✓ Select all shown</button>
        <button class="btn btn-sm" onclick="clearAllVisible()">✕ Clear shown</button>
      </div>

      <label style="display:block;font-size:12px;color:var(--muted);margin-bottom:8px">Pick recipients from the CRM (click or bulk-select):</label>
      <div id="distContactsArea" style="display:flex;flex-direction:column;gap:10px"></div>

      <div style="margin-top:16px;margin-bottom:12px">
        <label style="display:block;font-size:12px;color:var(--muted);margin-bottom:4px">+ Manual emails (not in CRM — auto-added on save)</label>
        <textarea id="distManual" rows="3" style="width:100%;padding:10px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text);font-size:13px;font-family:monospace;resize:vertical" placeholder="one@email.com, two@email.com"></textarea>
      </div>

      <div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin-bottom:16px">
        <label style="display:flex;align-items:center;gap:8px;font-size:13px;cursor:pointer">
          <input type="checkbox" id="distTestMode" ${group.test_mode ? 'checked' : ''} onchange="document.getElementById('distTestEmail').disabled = !this.checked"> Test mode
        </label>
        <input type="email" id="distTestEmail" value="${escapeHtml(group.test_email || 'sfrasier@montefiore.org')}" placeholder="Test email" style="flex:1;max-width:260px;padding:8px 10px;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--text);font-size:12px" ${!group.test_mode ? 'disabled' : ''}>
        <label style="display:flex;align-items:center;gap:8px;font-size:13px;min-width:200px">
          Attendance link
          <input type="url" id="distAttendance" value="${escapeHtml(group.attendance_link || '')}" placeholder="https://forms.gle/..." style="flex:1;min-width:180px;padding:8px 10px;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--text);font-size:12px">
        </label>
      </div>

      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
        <button class="btn" style="background:#f59e0b;color:#0f172a;border:none;font-weight:700" onclick="saveDistGroup()">Save Group</button>
        <span id="distStatus" style="font-size:12px"></span>
      </div>
    </div>
  `;
  renderDistContacts();
  document.getElementById('distManual').value = (group.emails || []).filter(e => !distContacts.some(c => (c.email||'').toLowerCase() === e.toLowerCase())).join('\n');
}

function renderDistContacts() {
  const area = document.getElementById('distContactsArea');
  if (!area) return;
  const group = distGroups[distActive];
  const savedEmails = new Set((group.emails || []).map(e => e.toLowerCase()));

  // Filter contacts by search + category
  let contacts = distContacts;
  const q = (distSearch || '').toLowerCase();
  if (q) {
    contacts = contacts.filter(c =>
      `${c.firstName||''} ${c.lastName||''}`.toLowerCase().includes(q) ||
      (c.email||'').toLowerCase().includes(q));
  }
  if (distCat) {
    contacts = contacts.filter(c => (c.category || 'Uncategorized') === distCat);
  }

  if (!contacts.length) {
    area.innerHTML = `<div class="empty-state" style="padding:24px"><div class="empty-state-title">No matching contacts</div></div>`;
    return;
  }

  // Optional: group by category with a header row when not filtering by category
  const cats = {};
  for (const c of contacts) {
    const cat = c.category || 'Uncategorized';
    if (!cats[cat]) cats[cat] = [];
    cats[cat].push(c);
  }

  let html = '';
  for (const [cat, list] of Object.entries(cats).sort()) {
    if (distCat && distCat !== cat) continue;
    const catChecked = list.every(c => savedEmails.has((c.email||'').toLowerCase()));
    const catCount = list.length;
    html += `<div>
      <label style="display:flex;align-items:center;gap:8px;font-size:13px;font-weight:700;color:var(--text);padding:6px 0;border-bottom:1px solid var(--border);margin-bottom:8px;cursor:pointer">
        <input type="checkbox" ${catChecked ? 'checked' : ''} onchange="toggleDistCategory('${escapeHtml(cat)}', this.checked)"> ${escapeHtml(cat)} <span style="color:var(--muted);font-weight:400">(${catCount})</span>
      </label>
      <div style="display:flex;flex-wrap:wrap;gap:6px;padding:0 4px 8px 4px">
        ${list.map(c => {
          const email = c.email || '';
          const name = [c.firstName, c.lastName].filter(Boolean).join(' ') || email;
          const checked = savedEmails.has(email.toLowerCase());
          return `<label style="display:flex;align-items:center;gap:5px;font-size:12px;cursor:pointer;padding:4px 9px;border:1px solid var(--border);border-radius:6px;background:${checked ? 'rgba(96,165,250,0.12)' : 'transparent'};transition:all .15s">
            <input type="checkbox" data-dist-email="${escapeHtml(email)}" ${checked ? 'checked' : ''} onchange="toggleDistContact('${escapeHtml(email)}', this.checked)"> ${escapeHtml(name)}
          </label>`;
        }).join('')}
      </div>
    </div>`;
  }
  area.innerHTML = html;

  // Update selected count
  const countEl = document.getElementById('distSelectedCount');
  if (countEl) countEl.textContent = distGroups[distActive]?.emails?.length || 0;
}

function findDistGroup() {
  if (!distGroups[distActive]) return { emails: [] };
  return distGroups[distActive];
}

function toggleDistCategory(cat, checked) {
  const group = findDistGroup();
  const emails = new Set((group.emails || []).map(e => e.toLowerCase()));
  let changed = false;
  for (const c of distContacts) {
    if ((c.category || 'Uncategorized') !== cat) continue;
    const email = (c.email || '').trim().toLowerCase();
    if (!email) continue;
    if (checked && !emails.has(email)) { emails.add(email); changed = true; }
    if (!checked && emails.has(email)) { emails.delete(email); changed = true; }
  }
  if (changed) {
    group.emails = Array.from(emails);
    // sync checkboxes
    document.querySelectorAll(`[data-dist-email]`).forEach(cb => {
      cb.checked = emails.has((cb.dataset.distEmail || '').toLowerCase());
    });
    updateDistCount();
  }
}

function toggleDistContact(email, checked) {
  const group = findDistGroup();
  const emails = new Set((group.emails || []).map(e => e.toLowerCase()));
  const key = (email || '').trim().toLowerCase();
  if (checked) emails.add(key);
  else emails.delete(key);
  group.emails = Array.from(emails);
  updateDistCount();
  // If this was a category-level change, the category checkbox state is derived; re-render categories lazy
}

function selectAllVisible() {
  const all = distContacts.filter(c => {
    const cat = c.category || 'Uncategorized';
    if (distCat && distCat !== cat) return false;
    if (distSearch) {
      const q = distSearch.toLowerCase();
      if (!`${c.firstName||''} ${c.lastName||''}`.toLowerCase().includes(q) && !(c.email||'').toLowerCase().includes(q)) return false;
    }
    return c.email;
  });
  const group = findDistGroup();
  const emails = new Set((group.emails || []).map(e => e.toLowerCase()));
  all.forEach(c => emails.add((c.email || '').toLowerCase()));
  group.emails = Array.from(emails);
  document.querySelectorAll(`[data-dist-email]`).forEach(cb => { cb.checked = true; });
  updateDistCount();
}

function clearAllVisible() {
  const group = findDistGroup();
  const emails = new Set((group.emails || []).map(e => e.toLowerCase()));
  const q = distSearch;
  const cat = distCat;
  for (const c of distContacts) {
    if (cat && cat !== (c.category||'Uncategorized')) continue;
    if (q) {
      const ql = q.toLowerCase();
      if (!`${c.firstName||''} ${c.lastName||''}`.toLowerCase().includes(ql) && !(c.email||'').toLowerCase().includes(ql)) continue;
    }
    const e = (c.email||'').toLowerCase();
    if (e) emails.delete(e);
  }
  group.emails = Array.from(emails);
  document.querySelectorAll(`[data-dist-email]`).forEach(cb => { cb.checked = false; });
  updateDistCount();
}

function updateDistCount() {
  const countEl = document.getElementById('distSelectedCount');
  if (countEl) countEl.textContent = distGroups[distActive]?.emails?.length || 0;
}

async function saveDistGroup() {
  const status = document.getElementById('distStatus');
  const key = distActive;
  status.innerHTML = '<span style="color:var(--accent)">Saving...</span>';
  try {
    const group = distGroups[key];
    // Manual emails
    const manualRaw = document.getElementById('distManual').value
      .split(/[\n,;]+/).map(e => e.trim()).filter(e => e && e.includes('@'));
    const allEmails = [...new Set([...(group.emails||[]), ...manualRaw.map(e => e.toLowerCase())])];
    const testMode = document.getElementById('distTestMode').checked;
    const testEmail = document.getElementById('distTestEmail').value.trim();
    const attendanceLink = document.getElementById('distAttendance').value.trim();

    // Auto-add manual emails to CRM (best-effort)
    for (const email of manualRaw) {
      if (!distContacts.some(c => (c.email||'').toLowerCase() === email.toLowerCase())) {
        try { await api.post('/api/crm/contacts', { email, category: 'Auto-added' }); } catch(e) {}
      }
    }

    await api.put('/api/crm/email-groups/' + encodeURIComponent(key), {
      emails: allEmails,
      test_mode: testMode,
      test_email: testEmail || null,
      attendance_link: attendanceLink || null
    });
    status.innerHTML = '<span style="color:#10b981">✓ Saved</span>';
    setTimeout(() => { status.innerHTML = ''; }, 3000);
    // Reload to reflect authoritative group data
    await loadDistribution();
  } catch (err) {
    status.innerHTML = `<span style="color:#ef4444">✕ ${escapeHtml(err.message)}</span>`;
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\"/g,'&quot;');
}
