/**
 * People Page - CRM Contact Directory
 * Full CRUD, search, filter, and GME tracking for residents
 */

let peopleState = {
  contacts: [],
  filteredContacts: [],
  searchQuery: '',
  categoryFilter: 'all',
  loading: false,
  selectedContact: null,
  gmeSummary: null,
  viewMode: 'grid' // 'grid' or 'table'
};

const CATEGORY_OPTIONS = [
  { value: 'Faculty', label: 'Faculty', color: 'purple' },
  { value: 'Resident', label: 'Resident', color: 'green' },
  { value: 'Nurse Practitioner', label: 'Nurse Practitioner', color: 'blue' },
  { value: 'Physician Assistant', label: 'Physician Assistant', color: 'yellow' },
  { value: 'Staff', label: 'Staff', color: 'pink' },
  { value: 'Medical Student', label: 'Medical Student', color: 'accent' }
];

const ROLE_OPTIONS = [
  'Attending',
  'Resident',
  'Nurse Practitioner',
  'Physician Assistant',
  'Staff',
  'Medical Student',
  'Administrator',
  'Other'
];

const PGY_OPTIONS = ['PGY-1', 'PGY-2', 'PGY-3', 'PGY-4', 'PGY-5', 'PGY-6', 'Chief'];

// ─── Main Render ───────────────────────────────────────────────────────────

async function renderPeople() {
  const container = document.getElementById('pageContent');
  container.innerHTML = `
    <div class="people-page">
      <div class="page-header">
        <div class="page-header-left">
          <h1 class="page-title">People</h1>
          <p class="page-subtitle">Contact directory with GME tracking</p>
        </div>
        <div class="page-header-right">
          <div class="btn-group">
            <button class="btn btn-ghost ${peopleState.viewMode === 'grid' ? 'active' : ''}" onclick="setPeopleViewMode('grid')" title="Grid view">⊞</button>
            <button class="btn btn-ghost ${peopleState.viewMode === 'table' ? 'active' : ''}" onclick="setPeopleViewMode('table')" title="Table view">☰</button>
          </div>
          <button class="btn btn-primary" onclick="openContactModal()">
            <span>+</span> Add Contact
          </button>
        </div>
      </div>

      <div class="people-toolbar">
        <div class="people-search">
          <span class="search-icon">🔍</span>
          <input 
            type="text" 
            class="form-input" 
            placeholder="Search by name, email, phone..."
            value="${escapeHtml(peopleState.searchQuery)}"
            oninput="handlePeopleSearch(this.value)"
          >
        </div>
        <div class="people-filters">
          <select class="form-select" onchange="handleCategoryFilter(this.value)">
            <option value="all" ${peopleState.categoryFilter === 'all' ? 'selected' : ''}>All Categories</option>
            ${CATEGORY_OPTIONS.map(cat => `
              <option value="${cat.value}" ${peopleState.categoryFilter === cat.value ? 'selected' : ''}>${cat.label}</option>
            `).join('')}
          </select>
          ${peopleState.categoryFilter === 'Resident' ? `
            <button class="btn btn-ghost" onclick="showGmeSummary()">
              💰 GME Summary
            </button>
          ` : ''}
        </div>
      </div>

      <div id="peopleContent" class="people-content">
        <div class="loading"><div class="loading-spinner"></div><span>Loading contacts...</span></div>
      </div>
    </div>
  `;

  await loadContacts();
}

// ─── Data Loading ──────────────────────────────────────────────────────────

async function loadContacts() {
  const content = document.getElementById('peopleContent');
  peopleState.loading = true;

  try {
    const [contactsRes, gmeRes] = await Promise.all([
      api.getContacts(),
      api.getGmeSummary().catch(() => null)
    ]);

    peopleState.contacts = contactsRes.contacts || [];
    peopleState.gmeSummary = gmeRes;
    applyPeopleFilters();
  } catch (err) {
    content.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">⚠️</div>
        <div class="empty-state-title">Failed to load contacts</div>
        <div class="empty-state-desc">${escapeHtml(err.message)}</div>
        <button class="btn btn-primary mt-3" onclick="loadContacts()">Retry</button>
      </div>
    `;
    peopleState.loading = false;
    return;
  }

  peopleState.loading = false;
  renderPeopleContent();
}

// ─── Filtering & Search ────────────────────────────────────────────────────

function handlePeopleSearch(query) {
  peopleState.searchQuery = query.toLowerCase();
  applyPeopleFilters();
  renderPeopleContent();
}

function handleCategoryFilter(category) {
  peopleState.categoryFilter = category;
  applyPeopleFilters();
  renderPeopleContent();
}

function applyPeopleFilters() {
  let filtered = peopleState.contacts;

  // Category filter
  if (peopleState.categoryFilter !== 'all') {
    filtered = filtered.filter(c => c.category === peopleState.categoryFilter);
  }

  // Search filter
  if (peopleState.searchQuery) {
    const q = peopleState.searchQuery;
    filtered = filtered.filter(c => {
      const fullName = `${c.firstName || ''} ${c.lastName || ''}`.toLowerCase();
      const email = (c.email || '').toLowerCase();
      const phone = (c.phone || '').toLowerCase();
      const role = (c.role || '').toLowerCase();
      return fullName.includes(q) || email.includes(q) || phone.includes(q) || role.includes(q);
    });
  }

  peopleState.filteredContacts = filtered;
}

function setPeopleViewMode(mode) {
  peopleState.viewMode = mode;
  renderPeople();
}

// ─── Content Rendering ─────────────────────────────────────────────────────

function renderPeopleContent() {
  const content = document.getElementById('peopleContent');

  if (peopleState.contacts.length === 0) {
    content.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">👥</div>
        <div class="empty-state-title">No contacts yet</div>
        <div class="empty-state-desc">Add your first contact to get started with the directory.</div>
        <button class="btn btn-primary mt-3" onclick="openContactModal()">Add Contact</button>
      </div>
    `;
    return;
  }

  if (peopleState.filteredContacts.length === 0) {
    content.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">🔍</div>
        <div class="empty-state-title">No matches found</div>
        <div class="empty-state-desc">Try adjusting your search or filter criteria.</div>
        <button class="btn btn-ghost mt-3" onclick="clearPeopleFilters()">Clear Filters</button>
      </div>
    `;
    return;
  }

  if (peopleState.viewMode === 'table') {
    content.innerHTML = renderPeopleTable();
  } else {
    content.innerHTML = renderPeopleGrid();
  }
}

function renderPeopleGrid() {
  return `
    <div class="people-grid">
      ${peopleState.filteredContacts.map(contact => `
        <div class="people-card" onclick="viewContactDetail('${contact.id}')">
          <div class="people-card-header">
            <div class="people-avatar">${getContactInitials(contact)}</div>
            <div class="people-card-actions" onclick="event.stopPropagation()">
              <button class="btn btn-xs btn-ghost" onclick="editContact('${contact.id}')" title="Edit">✏️</button>
              <button class="btn btn-xs btn-ghost" onclick="deleteContact('${contact.id}')" title="Delete">🗑️</button>
            </div>
          </div>
          <div class="people-card-body">
            <h3 class="people-name">${escapeHtml(contact.firstName || '')} ${escapeHtml(contact.lastName || '')}</h3>
            <div class="people-meta">
              <span class="badge badge-${getCategoryColor(contact.category)}">${escapeHtml(contact.category || 'Unknown')}</span>
              ${contact.pgy ? `<span class="badge badge-accent">${escapeHtml(contact.pgy)}</span>` : ''}
            </div>
            ${contact.role ? `<p class="people-role">${escapeHtml(contact.role)}</p>` : ''}
            ${contact.email ? `<p class="people-contact">📧 ${escapeHtml(contact.email)}</p>` : ''}
            ${contact.phone ? `<p class="people-contact">📱 ${escapeHtml(formatPhone(contact.phone))}</p>` : ''}
            ${contact.category === 'Resident' && contact.reimbursements ? renderGmeMini(contact) : ''}
          </div>
        </div>
      `).join('')}
    </div>
    <div class="people-stats">
      Showing ${peopleState.filteredContacts.length} of ${peopleState.contacts.length} contacts
    </div>
  `;
}

function renderPeopleTable() {
  return `
    <div class="table-wrapper">
      <table class="people-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Category</th>
            <th>Role</th>
            <th>Contact</th>
            ${peopleState.categoryFilter === 'Resident' ? '<th>GME Status</th>' : ''}
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${peopleState.filteredContacts.map(contact => `
            <tr onclick="viewContactDetail('${contact.id}')" style="cursor: pointer;">
              <td>
                <div class="people-table-name">
                  <div class="people-avatar-small">${getContactInitials(contact)}</div>
                  <span>${escapeHtml(contact.firstName || '')} ${escapeHtml(contact.lastName || '')}</span>
                </div>
              </td>
              <td><span class="badge badge-${getCategoryColor(contact.category)}">${escapeHtml(contact.category || 'Unknown')}</span></td>
              <td>${escapeHtml(contact.role || '-')}</td>
              <td>
                ${contact.email ? `<div class="people-contact-small">${escapeHtml(contact.email)}</div>` : ''}
                ${contact.phone ? `<div class="people-contact-small">${escapeHtml(formatPhone(contact.phone))}</div>` : ''}
              </td>
              ${peopleState.categoryFilter === 'Resident' ? `<td>${renderGmeStatusCell(contact)}</td>` : ''}
              <td>
                <div class="btn-group" onclick="event.stopPropagation()">
                  <button class="btn btn-xs btn-ghost" onclick="editContact('${contact.id}')" title="Edit">✏️</button>
                  <button class="btn btn-xs btn-ghost" onclick="deleteContact('${contact.id}')" title="Delete">🗑️</button>
                </div>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
    <div class="people-stats">
      Showing ${peopleState.filteredContacts.length} of ${peopleState.contacts.length} contacts
    </div>
  `;
}

function renderGmeMini(contact) {
  const reims = contact.reimbursements || [];
  const totalUsed = reims.reduce((sum, r) => sum + (r.amount || 0), 0);
  const remaining = 1250 - totalUsed;
  const percentUsed = Math.min((totalUsed / 1250) * 100, 100);

  return `
    <div class="people-gme-mini">
      <div class="people-gme-header">
        <span>💰 GME</span>
        <span class="people-gme-remaining ${remaining < 200 ? 'low' : ''}">$${remaining.toFixed(0)} left</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill ${percentUsed > 80 ? 'warning' : ''}" style="width: ${percentUsed}%"></div>
      </div>
    </div>
  `;
}

function renderGmeStatusCell(contact) {
  const reims = contact.reimbursements || [];
  const totalUsed = reims.reduce((sum, r) => sum + (r.amount || 0), 0);
  const remaining = 1250 - totalUsed;
  const percentUsed = Math.min((totalUsed / 1250) * 100, 100);

  return `
    <div class="people-gme-cell">
      <div class="people-gme-bar">
        <div class="people-gme-progress ${percentUsed > 80 ? 'warning' : ''}" style="width: ${percentUsed}%"></div>
      </div>
      <span class="people-gme-text ${remaining < 200 ? 'low' : ''}">$${remaining.toFixed(0)} left</span>
    </div>
  `;
}

// ─── Helper Functions ──────────────────────────────────────────────────────

function getContactInitials(contact) {
  const first = (contact.firstName || '').charAt(0).toUpperCase();
  const last = (contact.lastName || '').charAt(0).toUpperCase();
  return first + last || '??';
}

function getCategoryColor(category) {
  const cat = CATEGORY_OPTIONS.find(c => c.value === category);
  return cat ? cat.color : 'accent';
}

function formatPhone(phone) {
  if (!phone) return '';
  const digits = phone.replace(/\D/g, '');
  if (digits.length === 10) {
    return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
  }
  return phone;
}

function clearPeopleFilters() {
  peopleState.searchQuery = '';
  peopleState.categoryFilter = 'all';
  renderPeople();
}

// ─── Modal Forms ───────────────────────────────────────────────────────────

function openContactModal(contactId = null) {
  const isEdit = !!contactId;
  const contact = isEdit ? peopleState.contacts.find(c => c.id === contactId) : {};

  const title = isEdit ? 'Edit Contact' : 'Add Contact';
  const bodyHtml = `
    <form id="contactForm" class="people-form">
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">First Name *</label>
          <input type="text" class="form-input" name="firstName" value="${escapeHtml(contact.firstName || '')}" required>
        </div>
        <div class="form-group">
          <label class="form-label">Last Name *</label>
          <input type="text" class="form-input" name="lastName" value="${escapeHtml(contact.lastName || '')}" required>
        </div>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Category *</label>
          <select class="form-select" name="category" required onchange="togglePgyField(this.value)">
            ${CATEGORY_OPTIONS.map(cat => `
              <option value="${cat.value}" ${(contact.category || '') === cat.value ? 'selected' : ''}>${cat.label}</option>
            `).join('')}
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Role</label>
          <select class="form-select" name="role">
            <option value="">Select role...</option>
            ${ROLE_OPTIONS.map(role => `
              <option value="${role}" ${(contact.role || '') === role ? 'selected' : ''}>${role}</option>
            `).join('')}
          </select>
        </div>
      </div>

      <div class="form-row" id="pgyRow" style="display: ${(contact.category || '') === 'Resident' ? 'grid' : 'none'};">
        <div class="form-group">
          <label class="form-label">PGY Level</label>
          <select class="form-select" name="pgy">
            <option value="">Select PGY...</option>
            ${PGY_OPTIONS.map(pgy => `
              <option value="${pgy}" ${(contact.pgy || '') === pgy ? 'selected' : ''}>${pgy}</option>
            `).join('')}
          </select>
        </div>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Email</label>
          <input type="email" class="form-input" name="email" value="${escapeHtml(contact.email || '')}">
        </div>
        <div class="form-group">
          <label class="form-label">Phone</label>
          <input type="tel" class="form-input" name="phone" value="${escapeHtml(contact.phone || '')}" placeholder="(555) 123-4567">
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Notes</label>
        <textarea class="form-textarea" name="notes" rows="3">${escapeHtml(contact.notes || '')}</textarea>
      </div>
    </form>
  `;

  const footerHtml = `
    <button class="btn btn-ghost" onclick="closeModal()">Cancel</button>
    <button class="btn btn-primary" onclick="saveContact('${contactId || ''}')">
      ${isEdit ? 'Save Changes' : 'Add Contact'}
    </button>
  `;

  showModal(title, bodyHtml, footerHtml);
}

function togglePgyField(category) {
  const pgyRow = document.getElementById('pgyRow');
  if (pgyRow) {
    pgyRow.style.display = category === 'Resident' ? 'grid' : 'none';
  }
}

async function saveContact(contactId) {
  const form = document.getElementById('contactForm');
  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  const formData = new FormData(form);
  const data = {
    firstName: formData.get('firstName').trim(),
    lastName: formData.get('lastName').trim(),
    category: formData.get('category'),
    role: formData.get('role'),
    pgy: formData.get('pgy') || undefined,
    email: formData.get('email').trim() || undefined,
    phone: formData.get('phone').trim() || undefined,
    notes: formData.get('notes').trim() || undefined
  };

  try {
    if (contactId) {
      await api.updateContact(contactId, data);
      showToast('Contact updated successfully', 'success');
    } else {
      await api.addContact(data);
      showToast('Contact added successfully', 'success');
    }
    closeModal();
    await loadContacts();
  } catch (err) {
    showToast(err.message || 'Failed to save contact', 'error');
  }
}

async function editContact(contactId) {
  openContactModal(contactId);
}

async function deleteContact(contactId) {
  const contact = peopleState.contacts.find(c => c.id === contactId);
  const name = contact ? `${contact.firstName} ${contact.lastName}` : 'this contact';

  if (!confirm(`Are you sure you want to delete ${name}?`)) {
    return;
  }

  try {
    await api.deleteContact(contactId);
    showToast('Contact deleted', 'success');
    await loadContacts();
  } catch (err) {
    showToast(err.message || 'Failed to delete contact', 'error');
  }
}

// ─── Contact Detail View ───────────────────────────────────────────────────

async function viewContactDetail(contactId) {
  const contact = peopleState.contacts.find(c => c.id === contactId);
  if (!contact) return;

  const isResident = contact.category === 'Resident';
  let gmeHtml = '';

  if (isResident) {
    try {
      const residentsRes = await api.getGmeResidents();
      const residentData = residentsRes.residents?.find(r => r.id === contactId);
      if (residentData) {
        gmeHtml = renderGmeDetail(residentData);
      }
    } catch (err) {
      console.error('Failed to load GME data:', err);
    }
  }

  const bodyHtml = `
    <div class="people-detail">
      <div class="people-detail-header">
        <div class="people-avatar-large">${getContactInitials(contact)}</div>
        <div class="people-detail-info">
          <h2>${escapeHtml(contact.firstName || '')} ${escapeHtml(contact.lastName || '')}</h2>
          <div class="people-detail-meta">
            <span class="badge badge-${getCategoryColor(contact.category)}">${escapeHtml(contact.category || 'Unknown')}</span>
            ${contact.pgy ? `<span class="badge badge-accent">${escapeHtml(contact.pgy)}</span>` : ''}
            ${contact.role ? `<span class="badge badge-info">${escapeHtml(contact.role)}</span>` : ''}
          </div>
        </div>
      </div>

      <div class="people-detail-section">
        <h4>Contact Information</h4>
        <div class="people-detail-grid">
          ${contact.email ? `
            <div class="people-detail-item">
              <span class="people-detail-label">Email</span>
              <a href="mailto:${escapeHtml(contact.email)}" class="people-detail-value">${escapeHtml(contact.email)}</a>
            </div>
          ` : ''}
          ${contact.phone ? `
            <div class="people-detail-item">
              <span class="people-detail-label">Phone</span>
              <a href="tel:${escapeHtml(contact.phone)}" class="people-detail-value">${escapeHtml(formatPhone(contact.phone))}</a>
            </div>
          ` : ''}
        </div>
      </div>

      ${contact.notes ? `
        <div class="people-detail-section">
          <h4>Notes</h4>
          <p class="people-notes">${escapeHtml(contact.notes)}</p>
        </div>
      ` : ''}

      ${gmeHtml}
    </div>
  `;

  const footerHtml = `
    <button class="btn btn-danger" onclick="deleteContact('${contact.id}'); closeModal();">Delete</button>
    <div style="flex: 1;"></div>
    <button class="btn btn-ghost" onclick="closeModal()">Close</button>
    <button class="btn btn-primary" onclick="closeModal(); editContact('${contact.id}');">Edit</button>
  `;

  showModal('Contact Details', bodyHtml, footerHtml);
}

function renderGmeDetail(resident) {
  const totalUsed = resident.total_used || 0;
  const remaining = 1250 - totalUsed;
  const percentUsed = Math.min((totalUsed / 1250) * 100, 100);
  const reimbursements = resident.reimbursements || [];

  return `
    <div class="people-detail-section">
      <h4>💰 GME Reimbursement</h4>
      <div class="people-gme-summary">
        <div class="people-gme-stat">
          <span class="people-gme-stat-value">$${totalUsed.toFixed(2)}</span>
          <span class="people-gme-stat-label">Used</span>
        </div>
        <div class="people-gme-stat">
          <span class="people-gme-stat-value ${remaining < 200 ? 'low' : ''}">$${remaining.toFixed(2)}</span>
          <span class="people-gme-stat-label">Remaining</span>
        </div>
        <div class="people-gme-stat">
          <span class="people-gme-stat-value">$1,250</span>
          <span class="people-gme-stat-label">Annual Limit</span>
        </div>
      </div>
      <div class="progress-bar" style="margin: 16px 0;">
        <div class="progress-fill ${percentUsed > 80 ? 'warning' : ''}" style="width: ${percentUsed}%"></div>
      </div>

      ${reimbursements.length > 0 ? `
        <h5 style="margin-top: 20px;">Reimbursement History</h5>
        <div class="people-reimbursements">
          ${reimbursements.map(r => `
            <div class="people-reimbursement-item">
              <div class="people-reimbursement-main">
                <span class="people-reimbursement-date">${escapeHtml(r.date)}</span>
                <span class="people-reimbursement-category">${escapeHtml(r.category)}</span>
              </div>
              <span class="people-reimbursement-amount">$${(r.amount || 0).toFixed(2)}</span>
            </div>
          `).join('')}
        </div>
      ` : '<p class="text-muted text-sm">No reimbursements recorded yet.</p>'}
    </div>
  `;
}

// ─── GME Summary Modal ─────────────────────────────────────────────────────

async function showGmeSummary() {
  try {
    const summary = await api.getGmeSummary();
    const residents = await api.getGmeResidents();

    const bodyHtml = `
      <div class="people-gme-full">
        <div class="people-gme-cards">
          <div class="stat-card">
            <div class="stat-icon green">💰</div>
            <div class="stat-value">$${(summary.total_pool || 0).toLocaleString()}</div>
            <div class="stat-label">Total Pool</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon purple">💸</div>
            <div class="stat-value">$${(summary.total_used || 0).toLocaleString()}</div>
            <div class="stat-label">Total Used</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon blue">📊</div>
            <div class="stat-value">$${(summary.total_remaining || 0).toLocaleString()}</div>
            <div class="stat-label">Remaining</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon yellow">👥</div>
            <div class="stat-value">${summary.residents_with_funds || 0}/${summary.total_residents || 0}</div>
            <div class="stat-label">With Funds</div>
          </div>
        </div>

        <h4 style="margin-top: 24px; margin-bottom: 16px;">Resident Breakdown</h4>
        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>PGY</th>
                <th>Used</th>
                <th>Remaining</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${residents.residents?.map(r => {
                const remaining = 1250 - (r.total_used || 0);
                const percentUsed = Math.min((r.total_used || 0) / 1250 * 100, 100);
                const statusClass = remaining < 200 ? 'badge-danger' : percentUsed > 80 ? 'badge-warning' : 'badge-success';
                const statusText = remaining < 200 ? 'Low' : percentUsed > 80 ? 'High' : 'Good';
                return `
                  <tr>
                    <td>${escapeHtml(r.firstName)} ${escapeHtml(r.lastName)}</td>
                    <td>${escapeHtml(r.pgy || '-')}</td>
                    <td>$${(r.total_used || 0).toFixed(2)}</td>
                    <td>$${remaining.toFixed(2)}</td>
                    <td><span class="badge ${statusClass}">${statusText}</span></td>
                  </tr>
                `;
              }).join('') || '<tr><td colspan="5" class="text-muted">No residents found</td></tr>'}
            </tbody>
          </table>
        </div>
      </div>
    `;

    showModal('GME Summary', bodyHtml, '<button class="btn btn-ghost" onclick="closeModal()">Close</button>');
  } catch (err) {
    showToast('Failed to load GME summary', 'error');
  }
}
