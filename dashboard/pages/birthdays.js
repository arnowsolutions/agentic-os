/**
 * Birthday Emails — Agentic OS
 *
 * Shows upcoming birthdays from the live CRM, lets you preview the
 * LLM-generated card for any person, and run the send (test or live).
 *
 * API: /api/birthday/*
 */
async function renderBirthdays(target) {
  const content = target || document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">Birthday Emails</div>
        <div class="page-subtitle">Live CRM birthdays · AI-generated cards · automated sends</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderBirthdays()">⟳ Refresh</button>
        <button class="btn btn-ghost" onclick="bdRunToday(true)">Dry run</button>
        <button class="btn btn-primary" onclick="bdHandoffAll()">Build Outlook handoffs</button>
      </div>
    </div>

    <div class="bd-notice">
      <strong>Delivery note:</strong> Montefiore's mail filter quarantines the automated Gmail sender,
      so mail addressed to <code>@montefiore.org</code> is silently dropped (verified 2026-09-16 — plain,
      HTML and image variants all failed to arrive). <strong>Send in Outlook</strong> builds a pre-filled
      Outlook compose window; open it and press Send from your own mailbox. Direct email still works as
      designed if IT ever allowlists the sender.
    </div>

    <div class="bd-wrap">
      <div class="bd-col">
        <div class="bd-card">
          <div class="bd-card-head">
            <span>Today</span>
            <span id="bdMode" class="bd-pill">—</span>
          </div>
          <div id="bdToday" class="bd-body"><div class="loading"><div class="loading-spinner"></div><span>Reading CRM…</span></div></div>
        </div>

        <div class="bd-card" style="margin-top:16px;">
          <div class="bd-card-head"><span>Upcoming</span>
            <select id="bdDays" class="bd-select" onchange="bdLoad()">
              <option value="30">30 days</option>
              <option value="60" selected>60 days</option>
              <option value="120">120 days</option>
              <option value="365">12 months</option>
            </select>
          </div>
          <div id="bdUpcoming" class="bd-body"><div class="loading"><div class="loading-spinner"></div><span>Loading…</span></div></div>
        </div>

        <div class="bd-card" style="margin-top:16px;">
          <div class="bd-card-head"><span>Send history</span>
            <button class="btn btn-ghost bd-mini" onclick="bdLoadLog()">⟳</button>
          </div>
          <div id="bdLog" class="bd-body"><div class="bd-muted">No sends yet.</div></div>
        </div>
      </div>

      <div class="bd-col">
        <div class="bd-card">
          <div class="bd-card-head"><span>Card preview</span>
            <button class="btn btn-ghost bd-mini" id="bdRegenBtn" onclick="bdPreview(null, true)">↻ New artwork</button>
          </div>
          <div class="bd-body">
            <div class="bd-row">
              <input id="bdPerson" class="bd-input" placeholder="person — email or name" onkeydown="if(event.key==='Enter')bdPreview()">
              <button class="btn btn-primary bd-mini" onclick="bdPreview()">Preview</button>
            </div>
            <div id="bdPreviewBox" class="bd-preview-empty">Pick a person to generate their card.</div>
          </div>
        </div>

        <div class="bd-card" style="margin-top:16px;">
          <div class="bd-card-head"><span>Settings</span>
            <button class="btn btn-ghost bd-mini" onclick="bdSaveSettings()">Save</button>
          </div>
          <div class="bd-body" id="bdSettings"><div class="loading"><div class="loading-spinner"></div><span>Loading…</span></div></div>
        </div>

        <div class="bd-card" style="margin-top:16px;">
          <div class="bd-card-head"><span>Run output</span></div>
          <div class="bd-body"><pre id="bdOutput" class="bd-out">—</pre></div>
        </div>
      </div>
    </div>

    <style>
      .bd-wrap { display:grid; grid-template-columns:1fr 1fr; gap:16px; align-items:start; }
      @media (max-width:1100px){ .bd-wrap { grid-template-columns:1fr; } }
      .bd-card { background:var(--bg-card,#1a1a2e); border:1px solid var(--border,#2a2a3a); border-radius:12px; overflow:hidden; }
      .bd-card-head { display:flex; justify-content:space-between; align-items:center; padding:12px 16px;
                      border-bottom:1px solid var(--border,#2a2a3a); font-size:12px; font-weight:600;
                      text-transform:uppercase; letter-spacing:.6px; color:#94a3b8; }
      .bd-body { padding:14px 16px; }
      .bd-pill { font-size:10px; font-weight:700; padding:3px 9px; border-radius:999px;
                 background:rgba(0,184,148,.15); color:#00b894; text-transform:uppercase; letter-spacing:.5px; }
      .bd-pill.live { background:rgba(214,48,49,.15); color:#ff7675; }
      .bd-row { display:flex; gap:8px; }
      .bd-input,.bd-select { flex:1; background:#0f0f1e; border:1px solid #2a2a3a; color:#e8eaee;
                             border-radius:8px; padding:9px 11px; font-size:13px; font-family:inherit; }
      .bd-mini { font-size:11px !important; padding:7px 12px !important; }
      .bd-tbl { width:100%; border-collapse:collapse; }
      .bd-tbl th { text-align:left; font-size:10px; text-transform:uppercase; letter-spacing:.6px;
                   color:#7b8194; padding:6px 8px; border-bottom:1px solid #2a2a3a; }
      .bd-tbl td { padding:8px; font-size:12.5px; border-bottom:1px solid rgba(42,42,58,.55); color:#cbd5e1; }
      .bd-name { color:#f1f5f9; font-weight:600; }
      .bd-d0 { color:#ffd479; font-weight:700; }
      .bd-badge { font-size:10px; padding:2px 7px; border-radius:5px; background:rgba(0,184,148,.14); color:#00b894; }
      .bd-badge.pending { background:rgba(148,163,184,.14); color:#94a3b8; }
      .bd-muted { color:#7b8194; font-size:12.5px; }
      .bd-notice { background:rgba(232,199,122,.08); border:1px solid rgba(232,199,122,.25);
                   border-left:3px solid #e8c77a; color:#cbd5e1; font-size:12.5px; line-height:1.6;
                   padding:12px 14px; border-radius:8px; margin-bottom:16px; }
      .bd-notice code { background:rgba(255,255,255,.06); padding:1px 5px; border-radius:4px; color:#e8c77a; }
      .bd-preview-empty { margin-top:12px; padding:34px 12px; text-align:center; color:#7b8194; font-size:12.5px;
                          border:1px dashed #2a2a3a; border-radius:10px; }
      .bd-preview img { width:100%; border-radius:10px; border:1px solid #2a2a3a; display:block; }
      .bd-note { margin-top:10px; font-size:12.5px; color:#cbd5e1; font-style:italic; }
      .bd-out { background:#0f0f1e; border:1px solid #2a2a3a; border-radius:8px; padding:12px;
                font-size:11.5px; color:#a7b0c0; max-height:260px; overflow:auto; white-space:pre-wrap; margin:0; }
      .bd-field { margin-bottom:12px; }
      .bd-field label { display:block; font-size:10.5px; text-transform:uppercase; letter-spacing:.6px;
                        color:#7b8194; margin-bottom:5px; }
      .bd-field textarea { width:100%; background:#0f0f1e; border:1px solid #2a2a3a; color:#e8eaee;
                           border-radius:8px; padding:9px 11px; font-size:12.5px; font-family:inherit; resize:vertical; }
      .bd-check { display:flex; align-items:center; gap:8px; font-size:12.5px; color:#cbd5e1; margin-bottom:10px; }
    </style>
  `;
  bdLoad();
  bdLoadLog();
  bdLoadSettings();
}

async function bdLoad() {
  const days = parseInt(document.getElementById('bdDays')?.value || '60', 10);
  try {
    const [todayRes, upRes] = await Promise.all([
      fetch('/api/birthday/today').then(r => r.json()),
      fetch(`/api/birthday/upcoming?days=${days}`).then(r => r.json()),
    ]);
    bdRenderToday(todayRes);
    bdRenderUpcoming(upRes);
  } catch (e) {
    const el = document.getElementById('bdToday');
    if (el) el.innerHTML = `<div class="bd-muted">CRM read failed: ${escapeHtml(String(e))}</div>`;
  }
}

function bdModePill() { return document.getElementById('bdMode'); }

function bdSetMode(testMode) {
  const el = bdModePill();
  if (!el) return;
  el.textContent = testMode ? 'TEST MODE' : 'LIVE';
  el.className = 'bd-pill' + (testMode ? '' : ' live');
}

function bdRenderToday(res) {
  bdSetMode(res.test_mode !== undefined ? res.test_mode : null);
  const el = document.getElementById('bdToday');
  if (!el) return;
  if (!res.birthdays || !res.birthdays.length) {
    el.innerHTML = `<div class="bd-muted">No birthdays on ${escapeHtml(res.date || 'today')}.</div>`;
    return;
  }
  el.innerHTML = res.birthdays.map(p => `
    <div class="bd-row" style="justify-content:space-between; align-items:center; margin-bottom:10px;">
      <div>
        <div class="bd-name">${escapeHtml(p.name)}</div>
        <div class="bd-muted">${escapeHtml(p.category || '')} · ${escapeHtml(p.email || '')}</div>
      </div>
      <div style="display:flex; gap:8px; align-items:center;">
        ${p.already_sent ? '<span class="bd-badge">sent today</span>' : '<span class="bd-badge pending">not sent</span>'}
        <button class="btn btn-ghost bd-mini" onclick="bdPreviewFor('${escapeHtml(p.email || '')}')">Preview</button>
        <button class="btn btn-primary bd-mini" onclick="bdHandoffFor('${escapeHtml(p.email || '')}')">Send in Outlook</button>
      </div>
    </div>`).join('') +
    `<div class="bd-muted" style="margin-top:8px;">CRM source: ${escapeHtml(res.source || 'unknown')} · ${res.contacts_with_birthday || 0} contacts carry a birthday</div>`;
}

function bdRenderUpcoming(res) {
  const el = document.getElementById('bdUpcoming');
  if (!el) return;
  if (!res.birthdays || !res.birthdays.length) {
    el.innerHTML = '<div class="bd-muted">No upcoming birthdays in this window.</div>';
    return;
  }
  el.innerHTML = `
    <table class="bd-tbl">
      <tr><th>Date</th><th>Name</th><th>Role</th><th>When</th><th></th></tr>
      ${res.birthdays.map(b => `
        <tr>
          <td>${escapeHtml(b.turns_on || '')}</td>
          <td class="bd-name">${escapeHtml(b.name)}</td>
          <td class="bd-muted">${escapeHtml(b.category || '')}</td>
          <td class="${b.days_until === 0 ? 'bd-d0' : 'bd-muted'}">${b.days_until === 0 ? 'TODAY' : 'in ' + b.days_until + 'd'}</td>
          <td><button class="btn btn-ghost bd-mini" onclick="bdPreviewFor('${escapeHtml(b.email || '')}')">Card</button>
              <button class="btn btn-primary bd-mini" onclick="bdHandoffFor('${escapeHtml(b.email || '')}')">Outlook</button></td>
        </tr>`).join('')}
    </table>
    <div class="bd-muted" style="margin-top:8px;">${res.count} upcoming · ${res.today_count} today</div>`;
}

async function bdLoadLog() {
  const el = document.getElementById('bdLog');
  if (!el) return;
  try {
    const res = await fetch('/api/birthday/log?limit=25').then(r => r.json());
    if (!res.entries || !res.entries.length) { el.innerHTML = '<div class="bd-muted">No sends yet.</div>'; return; }
    el.innerHTML = `
      <table class="bd-tbl">
        <tr><th>Date</th><th>Person</th><th>Sent to</th><th>Mode</th><th>Status</th></tr>
        ${res.entries.map(e => `
          <tr>
            <td class="bd-muted">${escapeHtml(e.date || '')}</td>
            <td class="bd-name">${escapeHtml(e.name || '')}</td>
            <td class="bd-muted">${escapeHtml(e.sent_to || e.intended_email || '')}</td>
            <td class="bd-muted">${e.test_mode ? 'test' : 'live'}</td>
            <td>${e.status === 'failed'
                  ? '<span class="bd-badge pending" title="' + escapeHtml(e.error || '') + '">failed</span>'
                  : '<span class="bd-badge">' + escapeHtml(e.status || '') + '</span>'}</td>
          </tr>`).join('')}
      </table>`;
  } catch (e) {
    el.innerHTML = `<div class="bd-muted">Log unavailable.</div>`;
  }
}

async function bdLoadSettings() {
  const el = document.getElementById('bdSettings');
  if (!el) return;
  try {
    const s = await fetch('/api/birthday/settings').then(r => r.json());
    bdSetMode(s.test_mode);
    el.innerHTML = `
      <label class="bd-check"><input type="checkbox" id="bdEnabled" ${s.enabled ? 'checked' : ''}> Automation enabled</label>
      <label class="bd-check"><input type="checkbox" id="bdTestMode" ${s.test_mode ? 'checked' : ''}> Test mode (route everything to the test inbox)</label>
      <div class="bd-field"><label>Test recipient</label>
        <input id="bdTestRecip" class="bd-input" value="${escapeHtml(s.test_recipient || '')}"></div>
      <div class="bd-field"><label>Subject template</label>
        <input id="bdSubject" class="bd-input" value="${escapeHtml(s.subject_template || '')}"></div>
      <div class="bd-field"><label>Signature (blank = none)</label>
        <input id="bdSignature" class="bd-input" value="${escapeHtml(s.signature || '')}"></div>
      <div class="bd-field"><label>Footer note (blank = none)</label>
        <input id="bdFooter" class="bd-input" value="${escapeHtml(s.footer_note || '')}"></div>
      <div class="bd-field"><label>CC on every birthday email (comma-separated)</label>
        <input id="bdCc" class="bd-input" value="${escapeHtml((s.cc || []).join(', '))}"
               placeholder="name@montefiore.org, name2@montefiore.org"></div>
      <div class="bd-muted" style="margin:-4px 0 12px 0;">
        CC recipients are used on live sends only — never on test or preview sends.
      </div>
      <div class="bd-field"><label>Card design</label>
        <select id="bdDesign" class="bd-input"><option value="auto">Auto — rotate designs</option></select>
        <div id="bdDesignBlurb" class="bd-muted" style="margin-top:6px;"></div>
      </div>
      <div class="bd-field"><label>Image model (fal.ai) — only used by the AI Artwork design</label>
        <input id="bdModel" class="bd-input" value="${escapeHtml(s.image_model || '')}"></div>
      <div class="bd-field"><label>Image prompt</label>
        <textarea id="bdPrompt" rows="4">${escapeHtml(s.image_prompt || '')}</textarea></div>
      <div class="bd-field"><label>Negative prompt (keeps text out of the artwork)</label>
        <textarea id="bdNeg" rows="3">${escapeHtml(s.negative_prompt || '')}</textarea></div>
      <label class="bd-check"><input type="checkbox" id="bdNoteLlm" ${s.note_source === 'llm' ? 'checked' : ''}> Write the note text with an LLM (default: rotating templates)</label>
      <div class="bd-muted">Last run: ${escapeHtml(s.last_run || 'never')}</div>`;
    bdLoadDesigns(s.design || 'auto');
  } catch (e) {
    el.innerHTML = `<div class="bd-muted">Settings unavailable: ${escapeHtml(String(e))}</div>`;
  }
}

/** Fill the design picker from the API (never a hardcoded list). */
async function bdLoadDesigns(selected) {
  const sel = document.getElementById('bdDesign');
  if (!sel) return;
  try {
    const res = await fetch('/api/birthday/designs').then(r => r.json());
    const opts = ['<option value="auto">Auto — rotate designs</option>'];
    (res.designs || []).forEach(d => {
      const suffix = d.in_rotation ? '' : ' (opt-in)';
      opts.push(`<option value="${escapeHtml(d.key)}">${escapeHtml(d.label)}${suffix}</option>`);
    });
    sel.innerHTML = opts.join('');
    sel.value = selected || 'auto';
    sel.onchange = () => bdShowDesignBlurb(res, sel.value);
    bdShowDesignBlurb(res, sel.value);
  } catch (e) { /* picker stays as-is */ }
}

function bdShowDesignBlurb(res, value) {
  const el = document.getElementById('bdDesignBlurb');
  if (!el) return;
  if (!value || value === 'auto') {
    const n = (res.rotation || []).length;
    el.textContent = `Rotates through ${n} designs — stable per person, varies across the roster.`;
    return;
  }
  const d = (res.designs || []).find(x => x.key === value);
  el.textContent = d ? d.blurb : '';
}

async function bdSaveSettings() {
  const payload = {
    enabled: document.getElementById('bdEnabled')?.checked,
    test_mode: document.getElementById('bdTestMode')?.checked,
    test_recipient: document.getElementById('bdTestRecip')?.value.trim(),
    subject_template: document.getElementById('bdSubject')?.value,
    signature: document.getElementById('bdSignature')?.value,
    footer_note: document.getElementById('bdFooter')?.value,
    cc: (document.getElementById('bdCc')?.value || '')
          .split(',').map(x => x.trim()).filter(Boolean),
    design: document.getElementById('bdDesign')?.value || 'auto',
    image_model: document.getElementById('bdModel')?.value.trim(),
    image_prompt: document.getElementById('bdPrompt')?.value,
    negative_prompt: document.getElementById('bdNeg')?.value,
    note_source: document.getElementById('bdNoteLlm')?.checked ? 'llm' : 'template',
  };
  try {
    const res = await fetch('/api/birthday/settings', {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(r => r.json());
    if (res.success) { bdSetMode(res.settings.test_mode); if (window.showToast) showToast('Birthday settings saved', 'success'); }
    else if (window.showToast) showToast(res.detail || 'Save failed', 'error');
  } catch (e) {
    if (window.showToast) showToast('Save failed: ' + e, 'error');
  }
}

async function bdPreviewFor(ref) {
  const input = document.getElementById('bdPerson');
  if (input) input.value = ref;
  return bdPreview();
}

async function bdPreview(evt, regen) {
  const box = document.getElementById('bdPreviewBox');
  const person = document.getElementById('bdPerson')?.value.trim();
  if (!person) { if (window.showToast) showToast('Enter a person first', 'error'); return; }
  box.innerHTML = `<div class="loading"><div class="loading-spinner"></div><span>Generating card…</span></div>`;
  try {
    const res = await fetch('/api/birthday/preview', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ person, regen_art: !!regen }),
    }).then(r => r.json());
    if (!res.success) { box.innerHTML = `<div class="bd-muted">${escapeHtml(res.detail || 'Preview failed')}</div>`; return; }
    box.innerHTML = `
      <img src="${res.card_url}?t=${Date.now()}" alt="Birthday card for ${escapeHtml(res.person)}">
      <div class="bd-note">“${escapeHtml(res.note || '')}”</div>
      <div class="bd-muted" style="margin-top:6px;">${escapeHtml(res.person)} · ${escapeHtml(res.email || '')}</div>
      <div class="bd-row" style="margin-top:12px;">
        <button class="btn btn-primary bd-mini" onclick="bdHandoffFor('${escapeHtml(res.email || res.person)}')">Send in Outlook</button>
      </div>`;
  } catch (e) {
    box.innerHTML = `<div class="bd-muted">Preview failed: ${escapeHtml(String(e))}</div>`;
  }
}

async function bdSendOne(ref) {
  await bdRun({ person: ref });
}

/**
 * Build the Outlook handoff for one person and open the pre-filled compose
 * window. This is the path that actually reaches @montefiore.org.
 */
async function bdHandoffFor(ref) {
  const out = document.getElementById('bdOutput');
  if (out) out.textContent = `Building Outlook handoff for ${ref}…`;
  try {
    const res = await fetch('/api/birthday/handoff', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ person: ref }),
    }).then(r => r.json());
    if (!res.items || !res.items.length) {
      if (out) out.textContent = `No handoff built for ${ref} (${res.error || 'no match'}).`;
      if (window.showToast) showToast('No match for ' + ref, 'error');
      return;
    }
    const it = res.items[0];
    window.open(it.outlook_link, '_blank', 'noopener');
    if (out) out.textContent = JSON.stringify({ person: it.name, to: it.email,
      subject: it.subject, card: it.card_url,
      next: 'Outlook opened — press Send.' }, null, 2);
    bdLoad(); bdLoadLog();
  } catch (e) {
    if (out) out.textContent = 'Handoff failed: ' + e;
  }
}

/** Build handoffs for everyone with a birthday today. */
async function bdHandoffAll() {
  const out = document.getElementById('bdOutput');
  if (out) out.textContent = 'Building handoffs for today…';
  try {
    const res = await fetch('/api/birthday/handoff', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    }).then(r => r.json());
    if (out) out.textContent = JSON.stringify(res, null, 2);
    if (res.items && res.items.length === 1) {
      window.open(res.items[0].outlook_link, '_blank', 'noopener');
    }
    bdLoad(); bdLoadLog();
  } catch (e) {
    if (out) out.textContent = 'Handoff failed: ' + e;
  }
}

async function bdRunToday(dryRun) {
  await bdRun({ dry_run: !!dryRun });
}

async function bdRun(payload) {
  const out = document.getElementById('bdOutput');
  if (out) out.textContent = 'Running…';
  try {
    const res = await fetch('/api/birthday/send', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(r => r.json());
    if (out) out.textContent = JSON.stringify(res, null, 2);
    bdLoad(); bdLoadLog();
  } catch (e) {
    if (out) out.textContent = 'Run failed: ' + e;
  }
}
