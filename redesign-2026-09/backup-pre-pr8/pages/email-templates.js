/* Email Templates Dashboard Page */
async function renderEmailTemplates() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div>
        <h2 class="page-section-title">📋 Email Templates</h2>
        <p class="text-muted">Pre-built email templates for quick sending — use with "Send the {template name} to {contact}"</p>
      </div>
      <button class="btn btn-primary" onclick="showCreateTemplateModal()">
        <span class="btn-icon">+</span> New Template
      </button>
    </div>
    <div id="templatesGrid" class="grid-2 gap-4 mt-3">
      <div class="loading"><div class="loading-spinner"></div><span>Loading templates...</span></div>
    </div>

    <!-- Create/Edit Modal -->
    <div id="templateModal" class="modal-overlay" style="display:none" onclick="if(event.target===this)closeTemplateModal()">
      <div class="modal modal-lg">
        <div class="modal-header">
          <span class="modal-title" id="templateModalTitle">New Template</span>
          <button class="modal-close" onclick="closeTemplateModal()">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">Template Name (slug — used in voice commands)</label>
            <input type="text" class="form-input" id="tmplName" placeholder="e.g. rotation-reminder" />
          </div>
          <div class="form-group">
            <label class="form-label">Display Title</label>
            <input type="text" class="form-input" id="tmplTitle" placeholder="e.g. Rotation Reminder" />
          </div>
          <div class="form-group">
            <label class="form-label">Subject Line</label>
            <input type="text" class="form-input" id="tmplSubject" placeholder="e.g. Upcoming Rotation — {resident_name}" />
          </div>
          <div class="form-group">
            <label class="form-label">Body</label>
            <textarea class="form-input form-textarea" id="tmplBody" rows="10" placeholder="Use {firstName}, {lastName}, {date} as placeholders..."></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">Tone</label>
            <select class="form-input" id="tmplTone">
              <option value="professional">Professional</option>
              <option value="casual">Casual</option>
              <option value="urgent">Urgent</option>
              <option value="quick note">Quick Note</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" onclick="closeTemplateModal()">Cancel</button>
          <button class="btn btn-primary" id="saveTemplateBtn" onclick="saveTemplate()">Save Template</button>
        </div>
      </div>
    </div>

    <!-- Send Modal -->
    <div id="sendModal" class="modal-overlay" style="display:none" onclick="if(event.target===this)closeSendModal()">
      <div class="modal modal-lg">
        <div class="modal-header">
          <span class="modal-title" id="sendModalTitle">Send Template</span>
          <button class="modal-close" onclick="closeSendModal()">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">Contact</label>
            <select class="form-input" id="sendContact">
              <option value="">Loading contacts...</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Account Label</label>
            <select class="form-input" id="sendAccount">
              <option value="default">Default</option>
              <option value="gmail">Gmail</option>
              <option value="outlook">Outlook</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Subject <span id="sendSubjectPreview" class="text-muted" style="font-weight:400;font-size:13px"></span></label>
            <input type="text" class="form-input" id="sendSubject" placeholder="Email subject" />
          </div>
          <div class="form-group">
            <label class="form-label">Body</label>
            <textarea class="form-input form-textarea" id="sendBody" rows="10"></textarea>
          </div>
          <div class="flex gap-2">
            <button class="btn btn-secondary" onclick="previewSendTemplate()">👁 Preview</button>
            <span class="text-muted" style="font-size:13px;align-self:center">Preview replaces {firstName}, {lastName}, {date} with contact data</span>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" onclick="closeSendModal()">Cancel</button>
          <button class="btn btn-primary" id="sendBtn" onclick="executeSend()">✉ Send Email</button>
        </div>
      </div>
    </div>

    <style>
      .template-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px;
        transition: box-shadow 0.2s, transform 0.2s;
        cursor: default;
      }
      .template-card:hover {
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        transform: translateY(-2px);
      }
      .template-card .tmpl-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 10px;
      }
      .template-card .tmpl-name {
        font-weight: 600;
        font-size: 16px;
      }
      .template-card .tmpl-tone {
        display: inline-block;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 20px;
        background: var(--bg-card-alt);
        color: var(--text-muted);
        text-transform: capitalize;
      }
      .template-card .tmpl-subject {
        font-size: 13px;
        color: var(--text-muted);
        margin-bottom: 8px;
        font-family: monospace;
      }
      .template-card .tmpl-body {
        font-size: 13px;
        line-height: 1.5;
        color: var(--text);
        max-height: 80px;
        overflow: hidden;
        margin-bottom: 12px;
        white-space: pre-wrap;
        opacity: 0.85;
      }
      .template-card .tmpl-actions {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }
      .template-card .tmpl-actions .btn {
        font-size: 12px;
        padding: 6px 12px;
      }
      .grid-2 { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 16px; }
      .modal-lg { max-width: 640px; }
      .form-textarea { resize: vertical; min-height: 120px; font-family: monospace; font-size: 13px; }
    </style>
  `;

  await loadTemplates();
  await loadContactsForSend();
}

async function loadTemplates() {
  try {
    const data = await api.getEmailTemplates();
    const grid = document.getElementById('templatesGrid');
    const templates = data.templates || [];

    if (templates.length === 0) {
      grid.innerHTML = `<div class="empty-state"><div class="empty-state-icon">📋</div><div class="empty-state-title">No templates yet</div><div class="empty-state-desc">Create your first template to get started</div></div>`;
      return;
    }

    grid.innerHTML = templates.map(t => {
      const toneColor = t.tone === 'urgent' ? 'var(--red)' : t.tone === 'casual' ? 'var(--green)' : 'var(--text-muted)';
      return `
        <div class="template-card">
          <div class="tmpl-header">
            <span class="tmpl-name">${escapeHtml(t.title)}</span>
            <span class="tmpl-tone" style="border-left:3px solid ${toneColor};padding-left:8px">${escapeHtml(t.tone)}</span>
          </div>
          <div class="tmpl-subject">📧 ${escapeHtml(t.subject)}</div>
          <div class="tmpl-body">${escapeHtml(t.body)}</div>
          <div class="tmpl-actions">
            <button class="btn btn-primary btn-sm" onclick="openSendModal('${escapeHtml(t.name)}')">✉ Send to...</button>
            <button class="btn btn-secondary btn-sm" onclick="editTemplate('${escapeHtml(t.name)}')">✏ Edit</button>
            <button class="btn btn-danger btn-sm" onclick="deleteTemplate('${escapeHtml(t.name)}')">🗑 Delete</button>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    document.getElementById('templatesGrid').innerHTML =
      `<div class="empty-state"><div class="empty-state-icon">⚠</div><div class="empty-state-title">Failed to load</div><div class="empty-state-desc">${escapeHtml(err.message)}</div></div>`;
  }
}

async function loadContactsForSend() {
  try {
    const data = await api.getContacts();
    const select = document.getElementById('sendContact');
    const contacts = data.contacts || [];
    select.innerHTML = '<option value="">— Select a contact —</option>'
      + contacts.map(c => `<option value="${escapeHtml(c.id)}">${escapeHtml(c.firstName || '')} ${escapeHtml(c.lastName || '')} (${escapeHtml(c.email || 'no email')})</option>`).join('');
  } catch {
    document.getElementById('sendContact').innerHTML = '<option value="">Contacts unavailable</option>';
  }
}

/* ── Create / Edit Template ── */

let _editTemplateName = null;

function showCreateTemplateModal() {
  _editTemplateName = null;
  document.getElementById('templateModalTitle').textContent = 'New Template';
  document.getElementById('tmplName').value = '';
  document.getElementById('tmplTitle').value = '';
  document.getElementById('tmplSubject').value = '';
  document.getElementById('tmplBody').value = '';
  document.getElementById('tmplTone').value = 'professional';
  document.getElementById('saveTemplateBtn').textContent = 'Save Template';
  document.getElementById('templateModal').style.display = 'flex';
}

async function editTemplate(name) {
  try {
    const data = await api.getEmailTemplates();
    const t = (data.templates || []).find(tm => tm.name === name);
    if (!t) { showToast('Template not found', 'error'); return; }

    _editTemplateName = name;
    document.getElementById('templateModalTitle').textContent = 'Edit Template';
    document.getElementById('tmplName').value = t.name;
    document.getElementById('tmplTitle').value = t.title;
    document.getElementById('tmplSubject').value = t.subject;
    document.getElementById('tmplBody').value = t.body;
    document.getElementById('tmplTone').value = t.tone;
    document.getElementById('saveTemplateBtn').textContent = 'Update Template';
    document.getElementById('templateModal').style.display = 'flex';
  } catch (err) {
    showToast('Failed to load template: ' + err.message, 'error');
  }
}

function closeTemplateModal() {
  document.getElementById('templateModal').style.display = 'none';
}

async function saveTemplate() {
  const name = document.getElementById('tmplName').value.trim();
  const title = document.getElementById('tmplTitle').value.trim();
  const subject = document.getElementById('tmplSubject').value.trim();
  const body = document.getElementById('tmplBody').value.trim();
  const tone = document.getElementById('tmplTone').value;

  if (!name || !title || !subject || !body) {
    showToast('Please fill in all required fields', 'warning');
    return;
  }

  try {
    const data = {
      name: name.replace(/\s+/g, '-').toLowerCase(),
      title,
      subject,
      body,
      tone,
    };

    if (_editTemplateName && _editTemplateName !== data.name) {
      // Delete old, create new
      await api.deleteEmailTemplate(_editTemplateName);
    }

    await api.createEmailTemplate(data);
    closeTemplateModal();
    showToast(`Template "${data.title}" saved`, 'success');
    await loadTemplates();
  } catch (err) {
    showToast('Failed to save template: ' + err.message, 'error');
  }
}

async function deleteTemplate(name) {
  if (!confirm(`Delete template "${name}"?`)) return;
  try {
    await api.deleteEmailTemplate(name);
    showToast('Template deleted', 'success');
    await loadTemplates();
  } catch (err) {
    showToast('Failed to delete: ' + err.message, 'error');
  }
}

/* ── Send Template ── */

let _sendTemplateData = null;

async function openSendModal(templateName) {
  try {
    const data = await api.getEmailTemplates();
    const t = (data.templates || []).find(tm => tm.name === templateName);
    if (!t) { showToast('Template not found', 'error'); return; }

    _sendTemplateData = t;
    document.getElementById('sendModalTitle').textContent = `Send: ${t.title}`;
    document.getElementById('sendSubject').value = t.subject;
    document.getElementById('sendBody').value = t.body;
    document.getElementById('sendSubjectPreview').textContent = '';
    document.getElementById('sendModal').style.display = 'flex';
    await loadContactsForSend();
  } catch (err) {
    showToast('Failed to load template: ' + err.message, 'error');
  }
}

function closeSendModal() {
  document.getElementById('sendModal').style.display = 'none';
  _sendTemplateData = null;
}

function previewSendTemplate() {
  const contactSelect = document.getElementById('sendContact');
  const contactId = contactSelect.value;
  const subjectField = document.getElementById('sendSubject');
  const bodyField = document.getElementById('sendBody');

  if (!contactId) {
    showToast('Select a contact first to preview', 'warning');
    return;
  }

  // Load contacts from the select options to find selected contact's display name/email
  const selectedOption = contactSelect.options[contactSelect.selectedIndex];
  const contactLabel = selectedOption ? selectedOption.text : '';

  // Simple replacements using contact data if available from the label
  // For a proper preview, we'd need the full contact object
  let previewSubject = subjectField.value
    .replace(/\{firstName\}/g, contactLabel.split('(')[0].trim().split(' ')[0] || 'Contact')
    .replace(/\{lastName\}/g, contactLabel.split('(')[0].trim().split(' ').slice(1).join(' ') || '')
    .replace(/\{date\}/g, new Date().toLocaleDateString())
    .replace(/\{resident_name\}/g, contactLabel.split('(')[0].trim() || 'Resident')
    .replace(/\{conference_name\}/g, 'Conference')
    .replace(/\{deadline_name\}/g, 'Deadline')
    .replace(/\{subject\}/g, 'Topic');

  let previewBody = bodyField.value
    .replace(/\{firstName\}/g, contactLabel.split('(')[0].trim().split(' ')[0] || 'Contact')
    .replace(/\{lastName\}/g, contactLabel.split('(')[0].trim().split(' ').slice(1).join(' ') || '')
    .replace(/\{date\}/g, new Date().toLocaleDateString())
    .replace(/\{resident_name\}/g, contactLabel.split('(')[0].trim() || 'Resident')
    .replace(/\{conference_name\}/g, 'Conference')
    .replace(/\{deadline_name\}/g, 'Deadline')
    .replace(/\{subject\}/g, 'Topic');

  subjectField.value = previewSubject;
  bodyField.value = previewBody;
  document.getElementById('sendSubjectPreview').textContent = '(preview — edit if needed)';
}

async function executeSend() {
  const contactSelect = document.getElementById('sendContact');
  const contactId = contactSelect.value;
  const account = document.getElementById('sendAccount').value;
  const subject = document.getElementById('sendSubject').value.trim();
  const body = document.getElementById('sendBody').value.trim();

  if (!contactId) { showToast('Please select a contact', 'warning'); return; }
  if (!subject || !body) { showToast('Subject and body are required', 'warning'); return; }

  // Get contact email
  let contactEmail = '';
  let contactName = '';
  try {
    const data = await api.getContacts();
    const contact = (data.contacts || []).find(c => c.id === contactId);
    if (contact) {
      contactEmail = contact.email || '';
      contactName = `${contact.firstName || ''} ${contact.lastName || ''}`.trim();
    }
  } catch {}

  if (!contactEmail) { showToast('Contact has no email address', 'error'); return; }

  const btn = document.getElementById('sendBtn');
  btn.disabled = true;
  btn.textContent = '⏳ Sending...';

  try {
    const result = await api.sendEmail({
      account_label: account,
      to_email: contactEmail,
      subject,
      body,
    });
    if (result.success) {
      showToast(`Email sent to ${contactName} (${contactEmail})`, 'success');
      closeSendModal();
    } else {
      showToast('Failed to send: ' + (result.error || 'Unknown error'), 'error');
    }
  } catch (err) {
    showToast('Failed to send: ' + err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '✉ Send Email';
  }
}
