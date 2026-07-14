"""Shared fixtures for Agentic OS test suite."""
import sys
import os
from pathlib import Path

# Add the project root to the path so imports work
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from fastapi.testclient import TestClient

# Import the app — this triggers config loading
os.chdir(str(PROJECT_ROOT))

@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient for the full app."""
    from server import app
    return TestClient(app)

@pytest.fixture
def temp_crm_file(tmp_path):
    """Temporary CRM file for CRUD tests."""
    crm_file = tmp_path / "crm_contacts.json"
    crm_file.write_text("[]")
    return crm_file
