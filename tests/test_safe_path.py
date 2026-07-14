"""Tests for _safe_path — path traversal protection."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi import HTTPException


def test_safe_path_allows_normal_paths():
    """Normal paths within base should resolve correctly."""
    from server import _safe_path
    
    base = Path("/workspace/agentic-os/data")
    result = _safe_path(base, "crm_contacts.json")
    assert result == base / "crm_contacts.json"


def test_safe_path_blocks_parent_traversal():
    """../ should be rejected to prevent directory escape."""
    from server import _safe_path
    
    base = Path("/workspace/agentic-os/data")
    with pytest.raises(HTTPException) as exc:
        _safe_path(base, "../.env")
    assert exc.value.status_code == 400


def test_safe_path_blocks_absolute_path():
    """Absolute paths should be rejected."""
    from server import _safe_path
    
    base = Path("/workspace/agentic-os/data")
    with pytest.raises(HTTPException) as exc:
        _safe_path(base, "/etc/passwd")
    assert exc.value.status_code == 400


def test_safe_path_subdirectory():
    """Paths with subdirectories within base should work."""
    from server import _safe_path
    
    base = Path("/workspace/agentic-os/data")
    result = _safe_path(base, "subdir/file.json")
    assert result == base / "subdir" / "file.json"
