// CSS.escape polyfill
if (!CSS.escape) {
  CSS.escape = function(s) { return s.replace(/[^a-zA-Z0-9-]/g, '\\$&'); };
}

async function renderEmailGroups() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">📧 Email Groups</h1>
        <p class="page-subtitle">Manage Grand Rounds & Resident Conference recipients — pulls from CRM</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="renderEmailGroups()">🔄 Refresh</button>
      </div>
    </div>
    <div id="emailGroupsContent" style="display:flex;flex-wrap:wrap;gap:24px">Loading CRM contacts...</div>
  `;
  await loadEmailGroups();
}

let crmContacts = [];
let savedGroups = {};

async function loadEmailGroups() {
  try {
    const [crm, groups] = await Promise.all([
      api.get('/api/crm/contacts'),
      api.get('/api/crm/email-groups')
    ]);
    crmContacts = (crm.contacts || []).filter(c => !c.archived);
    savedGroups = groups;
    renderAllGroups();
  } catch (err) {
    document.getElementById('emailGroupsContent').innerHTML =
      `<div class="empty-state"><div class="empty-state-icon">⚠</div><div class="empty-state-title">Error</div><div class="empty-state-desc">${escapeHtml(err.message)}</div></div>`;
  }
}

function renderAllGroups() {
  // Build category -> contacts map
  const byCategory = {};
  for (const c of crmContacts) {
    const cat = c.category || 'Uncategorized';
    if (!byCategory[cat]) byCategory[cat] = [];
    byCategory[cat].push(c);
  }

  const container = document.getElementById('emailGroupsContent');
  let html = '';

  for (const [key, group] of Object.entries(savedGroups)) {
    const savedEmails = new Set((group.emails || []).map(e => e.toLowerCase()));
    const modeColor = group.test_mode ? '#f59e0b' : '#10b981';
    const modeLabel = group.test_mode ? '🧪 TEST MODE' : '🚀 LIVE';

    html += `
      <div style="flex:1;min-width:420px;max-width:600px;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
          <h3 style="margin:0;font-size:16px">${escapeHtml(group.label)}</h3>
          <span style="background:${modeColor};color:#fff;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600">${modeLabel}</span>
        </div>

        <div style="margin-bottom:12px">
          <label style="display:block;font-size:12px;color:var(--text-secondary);margin-bottom:6px">Select from CRM (by category):</label>`;

    // Category checkboxes
    for (const [cat, contacts] of Object.entries(byCategory).sort()) {
      const catChecked = contacts.every(c => savedEmails.has((c.email || '').toLowerCase()));
      html += `
          <div style="margin-bottom:8px">
            <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:13px;font-weight:600;padding:4px 0">
              <input type="checkbox" ${catChecked ? 'checked' : ''}
                onchange="toggleCategory('${key}', '${escapeHtml(cat)}', this.checked)"
                class="cat-check-${key}">
              ${escapeHtml(cat)} (${contacts.length})
            </label>
            <div style="padding-left:20px;display:flex;flex-wrap:wrap;gap:4px">`;
      for (const c of contacts) {
        const email = c.email || '';
        const name = [c.firstName, c.lastName].filter(Boolean).join(' ') || email;
        const checked = savedEmails.has(email.toLowerCase());
        if (!email) continue;
        html += `
              <label style="display:flex;align-items:center;gap:4px;font-size:11px;cursor:pointer;padding:2px 6px;border:1px solid var(--border);border-radius:4px;background:${checked ? 'var(--accent-dim)' : 'transparent'}">
                <input type="checkbox" ${checked ? 'checked' : ''}
                  onchange="toggleContact('${key}', '${escapeHtml(email)}', this.checked)"
                  class="contact-check-${key} contact-${escapeHtml(cat)}-${key}">
                <span title="${escapeHtml(email)}">${escapeHtml(name)}</span>
              </label>`;
      }
      html += `</div></div>`;
    }

    // Manual emails
    const manualEmails = (group.emails || []).filter(e => !crmContacts.some(c => (c.email || '').toLowerCase() === e.toLowerCase()));
    html += `
        </div>

        <div style="margin-bottom:12px">
          <label style="display:block;font-size:12px;color:var(--text-secondary);margin-bottom:4px">
            Manual emails (not in CRM — will be auto-added on save)
          </label>
          <textarea id="manual-${key}" rows="3" style="width:100%;padding:10px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text);font-size:13px;font-family:monospace;resize:vertical"
            placeholder="one@email.com, two@email.com">${escapeHtml(manualEmails.join('\n'))}</textarea>
        </div>

        <div style="display:flex;gap:12px;align-items:center;margin-bottom:12px">
          <label style="display:flex;align-items:center;gap:8px;font-size:13px;cursor:pointer">
            <input type="checkbox" id="testmode-${key}" ${group.test_mode ? 'checked' : ''} onchange="toggleTestMode('${key}', this.checked)">
            Test mode
          </label>
          <input type="email" id="testemail-${key}" value="${escapeHtml(group.test_email || '')}"
                 placeholder="Test email" style="flex:1;padding:6px 10px;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--text);font-size:12px"
                 ${!group.test_mode ? 'disabled' : ''}>
        </div>

        <div style="margin-bottom:12px">
          <label style="display:block;font-size:12px;color:var(--text-secondary);margin-bottom:4px">
            📋 Attendance tracking link (included in invites)
          </label>
          <input type="url" id="attendance-${key}" value="${escapeHtml(group.attendance_link || '')}"
                 placeholder="https://forms.gle/..." style="width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--text);font-size:12px">
        </div>

        <button class="btn" style="width:100%" onclick="saveGroup('${key}')">💾 Save Group</button>
        <div id="status-${key}" style="margin-top:8px;font-size:12px"></div>
      </div>`;
  }

  container.innerHTML = html;
}

function toggleCategory(key, cat, checked) {
  // Find all contacts in this category
  const selector = `.contact-${CSS.escape(cat)}-${key}`;
  document.querySelectorAll(selector).forEach(cb => {
    cb.checked = checked;
  });
}

function toggleContact(key, email, checked) {
  if (!checked) {
    // Find and uncheck the parent category checkbox
    const el = event.target;
    const catClass = Array.from(el.classList).find(c => c.startsWith('contact-') && c.endsWith(`-${key}`) && c !== `contact-check-${key}`);
    if (catClass) {
      const catName = catClass.replace(/^contact-/, '').replace(new RegExp(`-${CSS.escape(key)}$`), '');
      const catCB = document.querySelector(`.cat-check-${CSS.escape(key)}`);
      if (catCB && catCB.getAttribute('onchange') && catCB.getAttribute('onchange').includes(`'${catName}'`)) {
        catCB.checked = false;
      }
    }
  }
}

function collectCheckedEmails(key) {
  const emails = [];
  document.querySelectorAll(`.contact-check-${CSS.escape(key)}:checked`).forEach(cb => {
    // Extract email from the onchange attribute
    const m = cb.getAttribute('onchange').match(/toggleContact\('[^']*',\s*'([^']+)'/);
    if (m) emails.push(m[1]);
  });
  return emails;
}

function toggleTestMode(key, checked) {
  const emailInput = document.getElementById('testemail-' + key);
  if (emailInput) emailInput.disabled = !checked;
}

async function saveGroup(key) {
  const status = document.getElementById('status-' + key);
  status.innerHTML = '<span style="color:var(--accent)">Saving...</span>';
  try {
    // Collect checked CRM emails
    const checkedEmails = collectCheckedEmails(key);

    // Collect manual emails
    const manualRaw = document.getElementById('manual-' + key).value
      .split(/[\n,;]+/)
      .map(e => e.trim())
      .filter(e => e && e.includes('@'));

    const allEmails = [...new Set([...checkedEmails, ...manualRaw])];
    const testMode = document.getElementById('testmode-' + key).checked;
    const testEmail = document.getElementById('testemail-' + key).value.trim();
    const attendanceLink = document.getElementById('attendance-' + key).value.trim();

    // Auto-add new emails to CRM
    const newEmails = manualRaw.filter(e => !crmContacts.some(c => (c.email || '').toLowerCase() === e.toLowerCase()));
    for (const email of newEmails) {
      try {
        await api.post('/api/crm/contacts', { email, category: 'Auto-added' });
      } catch (e) {
        console.warn('Could not auto-add to CRM:', email, e);
      }
    }
    if (newEmails.length) {
      status.innerHTML = `<span style="color:var(--accent)">✅ Added ${newEmails.length} new contact(s) to CRM. Saving group...</span>`;
    }

    await api.put('/api/crm/email-groups/' + key, {
      emails: allEmails,
      test_mode: testMode,
      test_email: testEmail || null,
      attendance_link: attendanceLink || null
    });

    status.innerHTML = '<span style="color:#10b981">✅ Saved</span>';
    setTimeout(() => { status.innerHTML = ''; }, 3000);
  } catch (err) {
    status.innerHTML = `<span style="color:#ef4444">❌ ${escapeHtml(err.message)}</span>`;
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
