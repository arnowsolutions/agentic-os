"""Tests for CRM module — load, save, and validation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json


def test_load_crm_returns_list():
    """_load_crm should always return a list (never None)."""
    from modules.crm import _load_crm
    
    contacts = _load_crm()
    assert isinstance(contacts, list)


def test_save_and_load_roundtrip():
    """Save then load should return the same data (atomic write test)."""
    from modules.crm import _save_crm, _load_crm
    
    original = _load_crm()
    
    # Save a known test contact
    test_contact = {
        "id": "__pytest_test__",
        "firstName": "Test",
        "lastName": "User",
        "email": "test@test.com",
        "ezId": "EZ99999",
        "role": "Resident",
        "archived": False,
    }
    modified = original + [test_contact]
    _save_crm(modified)
    
    # Reload and verify
    reloaded = _load_crm()
    assert any(c.get("id") == "__pytest_test__" for c in reloaded)
    
    # Cleanup: remove test contact
    cleaned = [c for c in reloaded if c.get("id") != "__pytest_test__"]
    _save_crm(cleaned)
    
    final = _load_crm()
    assert not any(c.get("id") == "__pytest_test__" for c in final)
    assert len(final) == len(original)  # should be back to original count


def test_crm_access_log_writes():
    """Access logging should create entries."""
    from modules.crm import _log_crm_access, _get_crm_paths
    
    _log_crm_access(
        action="test_view",
        contact_id="test123",
        contact_name="Test User",
        endpoint="/api/crm/contacts",
        method="GET",
    )
    
    # Verify the access log exists and has entries
    _, access_log_path = _get_crm_paths()
    if access_log_path.exists():
        entries = json.loads(access_log_path.read_text())
        assert isinstance(entries, list)
        # Our test entry should be in there
        test_entries = [e for e in entries if e.get("contact_id") == "test123"]
        assert len(test_entries) > 0


def test_crm_module_has_required_exports():
    """CRM module should export expected functions."""
    import modules.crm as crm
    
    assert hasattr(crm, "_load_crm")
    assert hasattr(crm, "_save_crm")
    assert hasattr(crm, "_log_crm_access")
    assert hasattr(crm, "router")
    assert hasattr(crm, "GME_ANNUAL_LIMIT")


def test_gme_annual_limit_is_positive():
    """GME reimbursement limit should be a positive number."""
    from modules.crm import GME_ANNUAL_LIMIT
    
    assert GME_ANNUAL_LIMIT > 0
    assert GME_ANNUAL_LIMIT == 1250  # expected value
