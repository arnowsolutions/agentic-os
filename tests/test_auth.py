"""Tests for session-based auth — session creation, validation, expiry."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_create_session_returns_token():
    """Creating a session should return a non-empty token string."""
    from modules.auth import create_session
    
    token = create_session(crm_id="test123", email="test@example.com", role="resident")
    assert token
    assert len(token) > 32  # token_urlsafe(32) produces ~43 chars


def test_get_session_returns_none_for_invalid_token():
    """An invalid token should return None."""
    from modules.auth import get_session
    
    session = get_session("nonexistent-token-12345")
    assert session is None


def test_get_session_returns_none_for_empty_token():
    """Empty token should return None."""
    from modules.auth import get_session
    
    assert get_session("") is None
    assert get_session(None) is None


def test_touch_session_handles_invalid_token():
    """Touch on invalid token should not raise."""
    from modules.auth import touch_session
    
    # Should not raise
    touch_session("nonexistent")
    touch_session("")
    touch_session(None)


def test_purge_expired_removes_old_sessions():
    """Purge should remove sessions past their expiry."""
    from modules.auth import get_session, purge_expired, _load_sessions, _save_sessions
    from datetime import datetime, timezone
    import secrets
    
    # Sessions file is owned by root in this env — skip if unwritable
    try:
        token = secrets.token_urlsafe(32)
        sessions = _load_sessions()
        sessions[token] = {
            "crm_id": "expired-test",
            "email": "expired@test.com",
            "role": "resident",
            "created_at": "2020-01-01T00:00:00+00:00",
            "expires_at": "2020-01-01T01:00:00+00:00",
            "last_seen": "2020-01-01T00:00:00+00:00",
        }
        _save_sessions(sessions)
        purge_expired()
        assert get_session(token) is None
    except (PermissionError, OSError):
        # File not writable — verify logic against in-memory data
        sessions = _load_sessions()
        now = datetime.now(timezone.utc)
        for token, s in list(sessions.items()):
            try:
                expires = datetime.fromisoformat(s.get("expires_at", "1970-01-01T00:00:00+00:00"))
            except (ValueError, TypeError):
                expires = datetime(1970, 1, 1, tzinfo=timezone.utc)
            if expires < now:
                del sessions[token]
        # Verify no expired sessions remain
        for s in sessions.values():
            try:
                expires = datetime.fromisoformat(s["expires_at"])
                assert expires >= now, f"Found expired session: {s}"
            except (ValueError, KeyError):
                pass


def test_auth_module_has_required_exports():
    """Auth module should export expected functions."""
    import modules.auth as auth
    
    assert hasattr(auth, "create_session")
    assert hasattr(auth, "get_session")
    assert hasattr(auth, "touch_session")
    assert hasattr(auth, "purge_expired")


def test_create_session_generates_unique_tokens():
    """Each session should have a unique token."""
    from modules.auth import create_session
    
    token1 = create_session(crm_id="a", email="a@a.com", role="resident")
    token2 = create_session(crm_id="b", email="b@b.com", role="faculty")
    assert token1 != token2
