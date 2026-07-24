# Reimbursement & Infor Requests — Tip Sheet

## 📋 Two Audiences

### Section A: For Residents (What You Need to Know)
### Section B: For Shareef (Internal Workflow)

---

## SECTION A — FOR RESIDENTS

### Your GME Education Fund

You have **$1,250 per academic year** (July 1 – June 30) in GME education funds. These are managed by the House Staff Office.

**What counts toward GME:**
- Conference registration & travel
- Board preparation materials
- Educational equipment
- Books & subscriptions
- Step/compliance exam fees

**What comes from other funds (Dept/Teaching/MISC):**
- Wellness events & meals
- Department social activities
- Items that exceed the $1,250 GME cap

### How to Submit

1. **Keep your receipt** — scan or save the original
2. **Know what account it goes to** — if it's education/conference-related, it's likely GME. If not sure, ask Shareef
3. **Send to Shareef** (sfrasier@montefiore.org) with:
   - Receipt/invoice
   - What it was for
   - Date of purchase
4. Shareef will process through the appropriate cost center

### Common Questions

| Question | Answer |
|----------|--------|
| How much GME money do I have left? | Check your email from Shareef or ask him directly |
| Can I use GME for X? | If it's education-related (conference, board prep, books, exam fees), yes. Meals/social — probably Dept funds |
| What if I go over $1,250? | Once GME is exhausted, remaining costs go to Dept or Teaching funds if eligible |
| How long does reimbursement take? | Varies — ask Shareef for timeline |
| I lost my receipt | Contact the vendor for a duplicate |

---

## SECTION B — INTERNAL WORKFLOW (Shareef)

### System Architecture

```
Resident_Trackers2025-2026.xlsx  ← SOURCE OF TRUTH for all financial data
        │
        ▼  (sync_xlsx_to_db.py, every 6am & 6pm ET)
        │
reimbursement.db  →  send-report.py  →  Email + PDF to resident
                  →  Dashboard API   →  Reimbursement Dashboard
```

**Key Files:**
- `/workspace/Resident_Trackers2025-2026.xlsx` — Edit here for data corrections
- `/workspace/agentic-os/sync_xlsx_to_db.py` — Syncs xlsx → DB (runs twice daily)
- `/workspace/agentic-os/send-report.py` — Generates and emails PDF to residents
- `/workspace/repos/reimbursement/reimbursement.db` — SQLite database

### Account Mapping

| Cost Center Contains | Display Name | Notes |
|---------------------|--------------|-------|
| `GME` or code `10039` | GME Funds | $1,250 cap per resident per AY |
| `Dept` | Dept Funds | No cap |
| `Teaching` or code `130095` | Teaching Funds | No cap |
| `Donation` or code `100305095019` | **MISC** | Never display as "Donation" — user's rule |
| `Sleep` | Sleep Deprivation | Rare |

### Sending a Reimbursement Email

```bash
cd /workspace/agentic-os && PYTHONPATH="/workspace" \
  python3 send-report.py --resident "Full Name" --email recipient@montefiore.org
```

**Flags:**
- `--resident "Name"` — resident's full name (fuzzy matched)
- `--email "email"` — where to send (default: sfrasier@montefiore.org)
- Always test to yourself first before sending to the resident

**What the email includes:**
- GME remaining balance with progress bar
- Per-account breakdown (GME, Dept, Teaching, etc.)
- Full transaction table sorted by date
- Matching PDF attachment

### Handling the GME Cap ($1,250)

- **If a resident is over $1,250** in GME charges, check if any items can be reclassified to Dept or Teaching funds
- Common fix: conference travel coded as GME but should be Dept → edit the xlsx cost center
- Sync after editing: `python3 /workspace/agentic-os/sync_xlsx_to_db.py`

### Correcting Data (Step by Step)

1. Open the xlsx: `openpyxl.load_workbook('/workspace/Resident_Trackers2025-2026.xlsx')`
2. Edit the cost center column (col 8) and accounts column (col 11)
3. Update the Summary sheet totals
4. Save
5. Re-run sync: `python3 /workspace/agentic-os/sync_xlsx_to_db.py`
6. Re-send the email to verify

### Split Cost Centers

If a line item has GME + another fund (e.g. "$582 Teaching / $190 GME"):
- **ALWAYS split** into two rows in the DB
- The `gme_from_xlsx.py` parser handles this, but double-check if the amounts look inflated

### Infor Requests

To be developed — placeholder for equipment/supply ordering workflow.

### Deadlines & Reminders

- **Onboard new interns:** Send them the reimbursement intro email within 2 weeks of start
- **End of AY (June 30):** Remind residents of remaining balances before they expire
- **After conferences:** Check for pending receipts within 30 days
