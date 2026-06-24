async function renderContacts() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">📇 CRM — Contacts</h1>
        <p class="page-subtitle">Your resident, faculty & professional contacts — safe behind localhost</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="renderContactForm()">➕ Add Contact</button>
        <button class="btn" onclick="renderContacts()">🔄 Refresh</button>
      </div>
    </div>
    <div style="margin-bottom:16px">
      <input type="text" id="crmSearch" placeholder="🔍 Search by name, email, phone, EZ-ID..." 
             style="width:100%;padding:10px 14px;border:1px solid var(--border);border-radius:8px;
                    background:var(--surface);color:var(--text);font-size:14px"
             oninput="filterContacts()">
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px" id="crmFilters"></div>
    <div id="crmTable"></div>
  `;
  await loadContacts();
}

let allContacts = [];

async function loadContacts() {
  try {
    const data = await api.getContacts();
    allContacts = data.contacts || [];
    renderFilters();
    renderTable(allContacts);
  } catch (err) {
    document.getElementById('crmTable').innerHTML = 
      `<div class="empty-state"><div class="empty-state-icon">⚠</div><div class="empty-state-title">Error loading contacts</div><div class="empty-state-desc">${escapeHtml(err.message)}</div></div>`;
  }
}

function renderFilters() {
  const cats = {};
  allContacts.forEach(c => {
    const cat = c.category || 'Uncategorized';
    cats[cat] = (cats[cat] || 0) + 1;
  });
  const container = document.getElementById('crmFilters');
  let html = `<button class="tag" style="cursor:pointer;padding:4px 12px" onclick="filterByCategory('')">All (${allContacts.length})</button>`;
  Object.entries(cats).sort().forEach(([cat, count]) => {
    html += `<button class="tag" style="cursor:pointer;padding:4px 12px" onclick="filterByCategory('${escapeHtml(cat)}')">${escapeHtml(cat)} (${count})</button>`;
  });
  container.innerHTML = html;
  container.dataset.activeFilter = '';
}

function filterByCategory(cat) {
  document.getElementById('crmFilters').dataset.activeFilter = cat;
  document.querySelectorAll('#crmFilters .tag').forEach(el => el.style.borderColor = '');
  if (cat) event.target.style.borderColor = 'var(--accent)';
  filterContacts();
}

function filterContacts() {
  const q = (document.getElementById('crmSearch').value || '').toLowerCase();
  const activeCat = document.getElementById('crmFilters').dataset.activeFilter || '';
  let filtered = allContacts;
  if (activeCat) filtered = filtered.filter(c => (c.category || 'Uncategorized') === activeCat);
  if (q) {
    filtered = filtered.filter(c => 
      `${c.firstName||''} ${c.lastName||''}`.toLowerCase().includes(q) ||
      (c.email||'').toLowerCase().includes(q) ||
      (c.mobile||'').includes(q) ||
      (c.ezid||'').includes(q) ||
      (c.address||'').toLowerCase().includes(q)
    );
  }
  renderTable(filtered);
}

function renderTable(contacts) {
  const container = document.getElementById('crmTable');
  if (!contacts.length) {
    container.innerHTML = '<div class="empty-state" style="padding:40px"><div class="empty-state-title">No contacts found</div></div>';
    return;
  }
  let html = `<div style="font-size:12px;color:var(--text-muted);margin-bottom:8px">${contacts.length} contact${contacts.length!==1?'s':''}</div>`;
  contacts.forEach(c => {
    const name = `${escapeHtml(c.firstName||'')} ${escapeHtml(c.lastName||'')}`.trim() || 'Unknown';
    const cat = escapeHtml(c.category || 'Uncategorized');
    const badgeColor = cat === 'Resident' ? '#6c5ce7' : cat === 'Faculty' ? '#0984e3' : cat === 'Staff' ? '#00b894' : '#636e72';
    html += `
      <div class="card" style="margin-bottom:8px;cursor:pointer" onclick="showContactDetail('${c.id}')">
        <div style="display:flex;justify-content:space-between;align-items:start">
          <div>
            <div style="font-weight:600;font-size:15px">${name}</div>
            <div style="font-size:12px;color:var(--text-muted);margin-top:4px">
              ${c.email ? `📧 ${escapeHtml(c.email)}` : ''}
              ${c.email && c.mobile ? ' · ' : ''}
              ${c.mobile ? `📱 ${escapeHtml(c.mobile)}` : ''}
            </div>
            <div style="font-size:11px;color:var(--text-muted);margin-top:2px">
              ${c.pgy ? `📋 ${escapeHtml(c.pgy)}` : ''}
              ${c.pgy && (c.graduationYear||c.birthday) ? ' · ' : ''}
              ${c.graduationYear ? `🎓 ${escapeHtml(c.graduationYear)}` : ''}
              ${c.birthday ? ` 🎂 ${escapeHtml(c.birthday)}` : ''}
            </div>
          </div>
          <span class="tag" style="background:${badgeColor}20;color:${badgeColor};border:1px solid ${badgeColor}40;flex-shrink:0">${cat}</span>
        </div>
      </div>
    `;
  });
  container.innerHTML = html;
}

function showContactDetail(id) {
  const c = allContacts.find(x => x.id === id);
  if (!c) return;
  const name = `${escapeHtml(c.firstName||'')} ${escapeHtml(c.lastName||'')}`.trim() || 'Unknown';
  const fields = [
    ['Category', c.category],
    ['PGY', c.pgy],
    ['Address', c.address],
    ['Mobile', c.mobile],
    ['Pager', c.pager],
    ['EZ-ID', c.ezid],
    ['NPI', c.npi],
    ['Proximity', c.proximity],
    ['Birthday', c.birthday],
    ['Program Start', c.programStart],
    ['Urology Start', c.urologyStart],
    ['Graduation Year', c.graduationYear],
    ['Parking Chip', c.parkingChip],
    ['Email', c.email],
  ];
  let body = '<div style="display:grid;grid-template-columns:120px 1fr;gap:6px 12px;font-size:13px">';
  fields.forEach(([label, val]) => {
    if (val) {
      if (label === 'Email') {
        body += `<div style="color:var(--text-muted);font-weight:500">${label}</div><div><a href="mailto:${escapeHtml(val)}" style="color:var(--accent)">${escapeHtml(val)}</a></div>`;
      } else {
        body += `<div style="color:var(--text-muted);font-weight:500">${label}</div><div>${escapeHtml(val)}</div>`;
      }
    }
  });
  body += '</div>';
  const footer = `
    <button class="btn" onclick="composeEmail('${escapeHtml(c.email || '')}')">📧 Send Email</button>
    <button class="btn" onclick="editContact('${c.id}')">✏️ Edit</button>
    <button class="btn" style="border-color:var(--red)" onclick="deleteContact('${c.id}')">🗑 Delete</button>
    <button class="btn" onclick="closeModal()">Close</button>
  `;
  showModal(name, body, footer);
}

function renderContactForm(editId) {
  const c = editId ? allContacts.find(x => x.id === editId) : null;
  const title = c ? '✏️ Edit Contact' : '➕ Add Contact';
  const val = (f) => c ? escapeHtml(c[f] || '') : '';
  const body = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
      <div><label style="font-size:11px;color:var(--text-muted)">First Name</label><input id="fname" value="${val('firstName')}" style="width:100%"></div>
      <div><label style="font-size:11px;color:var(--text-muted)">Last Name</label><input id="lname" value="${val('lastName')}" style="width:100%"></div>
      <div><label style="font-size:11px;color:var(--text-muted)">Category</label>
        <select id="cat" style="width:100%">
          <option value="Resident" ${val('category')==='Resident'?'selected':''}>Resident</option>
          <option value="Faculty" ${val('category')==='Faculty'?'selected':''}>Faculty</option>
          <option value="Staff" ${val('category')==='Staff'?'selected':''}>Staff</option>
          <option value="Vendor" ${val('category')==='Vendor'?'selected':''}>Vendor</option>
          <option value="AI/Tech" ${val('category')==='AI/Tech'?'selected':''}>AI/Tech</option>
          <option value="Personal" ${val('category')==='Personal'?'selected':''}>Personal</option>
          <option value="Other" ${val('category')==='Other'?'selected':''}>Other</option>
        </select>
      </div>
      <div><label style="font-size:11px;color:var(--text-muted)">PGY Level</label><input id="pgy" value="${val('pgy')}" style="width:100%" placeholder="e.g. PG-4"></div>
      <div style="grid-column:1/-1"><label style="font-size:11px;color:var(--text-muted)">Address</label><input id="addr" value="${val('address')}" style="width:100%"></div>
      <div><label style="font-size:11px;color:var(--text-muted)">Mobile</label><input id="mobile" value="${val('mobile')}" style="width:100%"></div>
      <div><label style="font-size:11px;color:var(--text-muted)">Pager</label><input id="pager" value="${val('pager')}" style="width:100%"></div>
      <div><label style="font-size:11px;color:var(--text-muted)">Email</label><input id="email" value="${val('email')}" style="width:100%"></div>
      <div><label style="font-size:11px;color:var(--text-muted)">EZ-ID</label><input id="ezid" value="${val('ezid')}" style="width:100%"></div>
      <div><label style="font-size:11px;color:var(--text-muted)">NPI</label><input id="npi" value="${val('npi')}" style="width:100%"></div>
      <div><label style="font-size:11px;color:var(--text-muted)">Proximity</label><input id="prox" value="${val('proximity')}" style="width:100%"></div>
      <div><label style="font-size:11px;color:var(--text-muted)">Birthday</label><input id="bday" value="${val('birthday')}" style="width:100%" placeholder="e.g. 2/26"></div>
      <div><label style="font-size:11px;color:var(--text-muted)">Program Start</label><input id="progStart" value="${val('programStart')}" style="width:100%"></div>
      <div><label style="font-size:11px;color:var(--text-muted)">Urology Start Year</label><input id="uroStart" value="${val('urologyStart')}" style="width:100%"></div>
      <div><label style="font-size:11px;color:var(--text-muted)">Graduation Year</label><input id="gradYear" value="${val('graduationYear')}" style="width:100%"></div>
      <div><label style="font-size:11px;color:var(--text-muted)">Parking Chip #</label><input id="parking" value="${val('parkingChip')}" style="width:100%"></div>
    </div>
  `;
  const footer = `
    <button class="btn" onclick="saveContact('${editId || ''}')">💾 Save</button>
    <button class="btn" onclick="closeModal()">Cancel</button>
  `;
  showModal(title, body, footer);
}

async function saveContact(editId) {
  const data = {
    firstName: document.getElementById('fname').value,
    lastName: document.getElementById('lname').value,
    category: document.getElementById('cat').value,
    pgy: document.getElementById('pgy').value,
    address: document.getElementById('addr').value,
    mobile: document.getElementById('mobile').value,
    pager: document.getElementById('pager').value,
    email: document.getElementById('email').value,
    ezid: document.getElementById('ezid').value,
    npi: document.getElementById('npi').value,
    proximity: document.getElementById('prox').value,
    birthday: document.getElementById('bday').value,
    programStart: document.getElementById('progStart').value,
    urologyStart: document.getElementById('uroStart').value,
    graduationYear: document.getElementById('gradYear').value,
    parkingChip: document.getElementById('parking').value,
  };
  try {
    if (editId) {
      await api.updateContact(editId, data);
      showToast('Contact updated!', 'success');
    } else {
      await api.addContact(data);
      showToast('Contact added!', 'success');
    }
    closeModal();
    await loadContacts();
  } catch (err) {
    showToast('Error: ' + err.message, 'error');
  }
}

function editContact(id) { closeModal(); renderContactForm(id); }

function composeEmail(email) {
  if (!email) { showToast('No email address for this contact', 'warning'); return; }
  window.open('mailto:' + email, '_blank');
  showToast('Email client opened for ' + email, 'success');
}

async function deleteContact(id) {
  if (!confirm('Delete this contact?')) return;
  try {
    await api.deleteContact(id);
    showToast('Contact deleted', 'success');
    closeModal();
    await loadContacts();
  } catch (err) {
    showToast('Error: ' + err.message, 'error');
  }
}