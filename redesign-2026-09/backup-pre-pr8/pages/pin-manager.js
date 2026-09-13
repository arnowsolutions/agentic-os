class VapiPinManager {
    constructor() {
        this.users = [];
        this.filtered = [];
        this.searchQuery = '';
        // Don't auto-init — called lazily from renderPinManager()
    }

    async init() {
        await this.loadUsers();
        this.render();
    }

    async loadUsers() {
        try {
            const res = await fetch('/api/vapi/pins');
            const data = await res.json();
            this.users = data.users || [];
            this.filtered = [...this.users];
        } catch (e) {
            this.users = [];
            this.filtered = [];
        }
    }

    filter(query) {
        this.searchQuery = query.toLowerCase();
        if (!query) {
            this.filtered = [...this.users];
        } else {
            this.filtered = this.users.filter(u =>
                u.name.toLowerCase().includes(this.searchQuery) ||
                u.role.toLowerCase().includes(this.searchQuery) ||
                u.pin.includes(this.searchQuery)
            );
        }
        this.renderTable();
    }

    async resetPin(uid, currentName) {
        const newPin = prompt(`Enter new 4-digit PIN for ${currentName}:`, '');
        if (!newPin) return;
        if (!/^\d{4}$/.test(newPin)) {
            alert('PIN must be exactly 4 digits.');
            return;
        }
        if (!confirm(`Set PIN for ${currentName} to ${newPin}?`)) return;

        try {
            const res = await fetch('/api/vapi/pins/reset', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({uid, new_pin: newPin})
            });
            const data = await res.json();
            if (data.success) {
                await this.loadUsers();
                this.filter(this.searchQuery);
                showToast(`PIN changed for ${data.name}`, 'success');
            } else {
                alert(data.error || 'Failed to reset PIN');
            }
        } catch (e) {
            alert('Error: ' + e.message);
        }
    }

    render() {
        const content = document.getElementById('pageContent');
        content.innerHTML = `
            <div class="page">
                <div class="page-header">
                    <h1><i class="fas fa-key"></i> Voice PIN Manager</h1>
                    <p class="page-subtitle">View and reset PINs for the Vapi voice assistant (${this.users.length} users)</p>
                </div>
                <div class="card">
                    <div class="card-body">
                        <div style="margin-bottom:16px">
                            <input type="text" id="pin-search" placeholder="Search by name, role, or PIN..." 
                                   style="width:100%;padding:10px 14px;border:1px solid #334;border-radius:6px;background:#1a1a2e;color:#eee;font-size:14px">
                        </div>
                        <div style="overflow-x:auto">
                            <table class="table" id="pin-table">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>Role</th>
                                        <th>PIN</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="pin-tbody"></tbody>
                            </table>
                        </div>
                        <div id="pin-count" style="margin-top:12px;font-size:12px;color:#888"></div>
                    </div>
                </div>
                <div class="card" style="margin-top:16px">
                    <div class="card-header"><h3>ℹ️ How PINs Work</h3></div>
                    <div class="card-body" style="font-size:13px;color:#aaa;line-height:1.6">
                        <p>Default PINs are the <strong>last 4 digits of the person's phone number</strong> on file in the CRM.
                        For contacts without a phone number, a default of 1234 is used (or ezId digits if available).</p>
                        <p>After changing a PIN here, you must <strong>re-deploy the assistant</strong> for the embedded prompt to update:</p>
                        <code style="display:block;padding:8px 12px;background:#111;border-radius:4px;margin:8px 0">
                            python3 /workspace/agentic-os/deploy_vapi_v4.py
                        </code>
                        <p>The server is at port 8090. The PIN database is at <code>agentic-os/data/user_pins.json</code>.</p>
                    </div>
                </div>
            </div>
        `;

        document.getElementById('pin-search').addEventListener('input', (e) => {
            this.filter(e.target.value);
        });

        this.renderTable();
    }

    renderTable() {
        const tbody = document.getElementById('pin-tbody');
        if (!tbody) return;

        if (this.filtered.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#666;padding:24px">No users found</td></tr>';
            document.getElementById('pin-count').textContent = '0 results';
            return;
        }

        tbody.innerHTML = this.filtered.map(u => `
            <tr>
                <td><strong>${this.escapeHtml(u.name)}</strong></td>
                <td><span class="badge badge-${this.roleBadge(u.role)}">${u.role || '—'}</span></td>
                <td><code style="font-size:16px;letter-spacing:2px">${u.pin}</code></td>
                <td>
                    <button class="btn btn-sm btn-warning" onclick="pinManager.resetPin('${u.uid}', '${this.escapeHtml(u.name)}')">
                        <i class="fas fa-edit"></i> Reset PIN
                    </button>
                </td>
            </tr>
        `).join('');
        document.getElementById('pin-count').textContent = `${this.filtered.length} of ${this.users.length} users`;
    }

    roleBadge(role) {
        const m = {'faculty': 'primary', 'resident': 'info', 'administrator': 'warning', 'staff': 'secondary', 'nurse': 'success'};
        return m[role.toLowerCase()] || 'secondary';
    }

    escapeHtml(s) {
        const d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
    }
}

// Lazy singleton — created on first navigation to #pin-manager
let _pinManagerInstance = null;

async function renderPinManager() {
    if (!_pinManagerInstance) {
        _pinManagerInstance = new VapiPinManager();
        await _pinManagerInstance.init();
    } else {
        // Re-render if already navigated away and back
        _pinManagerInstance.render();
    }
}
