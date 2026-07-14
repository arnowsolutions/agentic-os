# Phase 6.4b: After-Effect — Integrity

## Data Integrity Assessment

### JSON File Database Risks

The project uses ~127 JSON files as its primary data store. This creates several integrity risks:

**Risks:**
1. **No transactions** — concurrent writes can interleave, corrupting data
2. **No schema enforcement** — any endpoint can write any shape to any file
3. **No migrations** — data format changes require manual migration scripts
4. **No referential integrity** — EZ IDs in eval_forms.json may not exist in crm_contacts.json
5. **File corruption on crash** — write during power loss = truncated file

**Current mitigation:** Most files are small and writes are infrequent. The cost_tracker module uses atomic writes (write to temp, rename). CRM module does NOT.

### Type Safety

- **Zero TypeScript** — all 73 JS files are vanilla JavaScript
- **No PropTypes, JSDoc types, or Flow**
- Python side: some Pydantic models used but most routes accept raw `dict`
- No mypy/pyright configuration

### Edge Cases Found

1. **Empty state handling:** Inconsistent — some pages crash on empty API responses
2. **Network failures:** Most `fetch()` calls lack timeout/retry logic
3. **Large datasets:** No pagination on most list endpoints (CRM contacts could grow)
4. **Special characters:** EZ IDs with special chars, names with apostrophes — not systematically tested
5. **Concurrent edits:** Two users editing same contact/cost entry — last write wins

### Data Quality Score: 5.0/10

JSON files are convenient for a solo developer but the lack of transactions, schema enforcement, and type safety creates real data integrity risk as the system grows.
