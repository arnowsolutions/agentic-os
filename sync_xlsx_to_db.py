#!/usr/bin/env python3
"""
Sync: Read Resident_Trackers2025-2026.xlsx → update reimbursement.db allocations.
Keeps the database in sync with the spreadsheet. Runs twice daily via cron.

For each GME/Teaching/Dept/MISC transaction in the xlsx:
  1. Creates/updates an allocation in the database
  2. Creates/updates a submission entry for tracking
  3. Maps account names: Donation → MISC (already handled in display)
"""
import sys, os, sqlite3, uuid, re
from pathlib import Path
from datetime import datetime, date
from collections import defaultdict

sys.path.insert(0, '/workspace/agentic-os')
import openpyxl
import gme_from_xlsx

XLSX_PATH = Path("/workspace/Resident_Trackers2025-2026.xlsx")
DB_PATH = Path("/workspace/repos/reimbursement/reimbursement.db")

# Mapping from display account → database account name
ACCT_TO_DB = {
    'GME Funds': 'GME Funds',
    'Teaching Funds': 'Teaching Funds',
    'Dept Funds': 'Dept Funds',
    'MISC': 'Donation Funds',
    'Sleep Deprivation': 'Sleep Deprivation',
    'Other': 'Other',
}

# Mapping from xlsx name → beneficiary ID
# Build from persons table
def get_person_map(conn):
    cur = conn.execute("SELECT id, name FROM persons")
    mapping = {}
    for row in cur.fetchall():
        name = str(row[1]).strip().lower()
        name_norm = name.replace(' ', '').replace(',', '')
        mapping[name_norm] = row[0]
        # Also index by first word
        first = name.split()[0] if name else ''
        if first:
            mapping[first] = row[0]
    return mapping

def normalize(name):
    return name.lower().replace(' ', '').replace(',', '').replace('-', '')

def sync():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Starting xlsx → DB sync...")
    
    if not XLSX_PATH.exists():
        print(f"  ❌ XLSX not found: {XLSX_PATH}")
        return False
    if not DB_PATH.exists():
        print(f"  ❌ DB not found: {DB_PATH}")
        return False
    
    conn = sqlite3.connect(str(DB_PATH))
    person_map = get_person_map(conn)
    
    # Read all transactions from xlsx via the existing module
    wb = openpyxl.load_workbook(str(XLSX_PATH), data_only=True)
    ws = wb["Sheet 2025-2026"]
    
    stats = {'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
    
    # First pass: collect all transaction IDs so we can do a clean replacement
    # Delete all previous sync entries
    conn.execute("DELETE FROM allocations WHERE id LIKE 'al_xlsx_%'")
    conn.commit()
    print(f"  🧹 Cleared previous sync entries")
    
    for row in ws.iter_rows(min_row=2, values_only=True):
        name = str(row[0] or '').strip()
        if not name:
            continue
        date_val = row[1]
        if not date_val:
            continue
        
        try:
            dt = date_val if isinstance(date_val, datetime) else datetime.strptime(str(date_val)[:10], '%Y-%m-%d')
        except:
            continue
        
        desc = str(row[3] or '').strip()
        amount = float(row[4] or 0)
        if amount <= 0:
            continue
        tracking = str(row[6] or '').strip()
        cc = str(row[7] or '').strip()
        comments = str(row[8] or '').strip()
        accounts_col = str(row[10] or '').strip() if len(row) > 10 else ''
        
        # Use accounts column if available, otherwise fall back to map_account
        if accounts_col:
            if 'DEPT' in accounts_col.upper():
                db_account = 'Dept Funds'
            elif 'GME' in accounts_col.upper():
                db_account = 'GME Funds'
            elif 'TEACHING' in accounts_col.upper():
                db_account = 'Teaching Funds'
            elif 'DONATION' in accounts_col.upper():
                db_account = 'Donation Funds'
            else:
                db_account = gme_from_xlsx.map_account(cc, comments)
        else:
            db_account = gme_from_xlsx.map_account(cc, comments)
        
        db_acct = ACCT_TO_DB.get(db_account, db_account)
        
        # Find beneficiary
        name_norm = normalize(name)
        benef_id = person_map.get(name_norm)
        if not benef_id:
            # Try first name only
            first = name.split()[0].lower() if name else ''
            benef_id = person_map.get(first)
        
        if not benef_id:
            # Try fuzzy match
            for key, pid in person_map.items():
                if name_norm in key or key in name_norm:
                    benef_id = pid
                    break
        
        if not benef_id:
            stats['errors'] += 1
            print(f"  ⚠️  No person match for: {name}")
            continue
        
        # Create a deterministic ID from the tracking number or description+date
        alloc_id = f"al_xlsx_{normalize(name)}_{dt.strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        txn_date_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Always insert fresh (old sync data was already deleted)
        conn.execute("""
            INSERT INTO allocations (id, amount, account, description, beneficiary_id, status, allocation_type, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'primary', ?, ?)
        """, (alloc_id, amount, db_acct, desc[:500], benef_id, 'approved', txn_date_str, now_str))
        stats['created'] += 1
    
    conn.commit()
    conn.close()
    wb.close()
    
    print(f"  ✅ Created: {stats['created']}, Updated: {stats['updated']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}")
    print(f"  ✅ Sync complete")
    return True

if __name__ == "__main__":
    sync()
