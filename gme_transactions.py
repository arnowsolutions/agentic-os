#!/usr/bin/env python3
"""
GME transaction queries against the reimbursement SQLite database.

Provides approved submissions grouped by resident name for inclusion in
GME PDF reports and Telegram summaries.
"""

import os
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any, Optional

DEFAULT_DB_PATH = Path("/workspace/repos/reimbursement/reimbursement.db")


def _get_db_path() -> Path:
    """Allow environment override for test / alternate deployments."""
    env = os.environ.get("REIMBURSEMENT_DB")
    return Path(env) if env else DEFAULT_DB_PATH


def transactions_by_resident(
    status: str = "complete",
    account_filter: Optional[str] = "GME",
    db_path: Optional[Path] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Return approved submissions grouped by resident name.

    Each transaction contains: id, target_name, date, description, amount,
    final_account, status, submitted_at.

    Args:
        status: submission status to treat as approved (default 'complete').
        account_filter: if provided, only submissions whose final_account
            contains this substring are included (case-insensitive).
            Pass None/'' to disable account filtering.
        db_path: alternate SQLite database path.
    """
    path = db_path or _get_db_path()
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = """
        SELECT
            s.id,
            s.target_name AS resident_name,
            s.date,
            s.description,
            s.amount,
            s.final_account,
            s.status,
            s.submitted_at
        FROM submissions s
        WHERE s.status = ?
          AND s.deleted_at IS NULL
    """
    params: List[Any] = [status]

    if account_filter:
        query += " AND LOWER(s.final_account) LIKE LOWER(?)"
        params.append(f"%{account_filter}%")

    query += " ORDER BY s.target_name, s.date, s.submitted_at"

    cur.execute(query, params)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["resident_name"]].append(row)

    return dict(grouped)


def transaction_summary(grouped: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Return aggregate counts and totals for a grouped transaction list."""
    total_count = sum(len(items) for items in grouped.values())
    total_amount = sum(
        item.get("amount", 0) or 0
        for items in grouped.values()
        for item in items
    )
    return {
        "resident_count": len(grouped),
        "transaction_count": total_count,
        "total_amount": total_amount,
    }


if __name__ == "__main__":
    import json

    grouped = transactions_by_resident()
    print(json.dumps({
        "summary": transaction_summary(grouped),
        "residents": {
            name: [
                {
                    "date": t["date"],
                    "description": t["description"],
                    "amount": t["amount"],
                    "final_account": t["final_account"],
                }
                for t in txs
            ]
            for name, txs in grouped.items()
        },
    }, indent=2, default=str))
