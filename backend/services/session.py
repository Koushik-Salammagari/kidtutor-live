"""
Firestore helpers for session state.
Session documents expire after 2 hours (TTL). Project: kidtutor-v2.
"""
import os
from datetime import datetime, timedelta
from typing import Any

from google.cloud import firestore

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "kidtutor-v2")
COLLECTION = "sessions"
# Firestore TTL: expire after 2 hours (CURSOR_CONTEXT.md). Set TTL policy on expire_at in console.
SESSION_TTL_HOURS = 2


def _get_client() -> firestore.Client:
    return firestore.Client(project=GOOGLE_CLOUD_PROJECT)


def _expire_at_timestamp() -> datetime:
    return datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS)


def create_session(session_data: dict[str, Any], session_id: str | None = None) -> str:
    """
    Create a session document in Firestore. Sets created_at and expire_at (TTL).
    If session_id is provided, uses it as the document id; otherwise Firestore generates one.
    Returns the session_id (document id).
    """
    client = _get_client()
    col = client.collection(COLLECTION)
    if session_id is not None:
        doc_ref = col.document(session_id)
    else:
        doc_ref = col.document()
        session_id = doc_ref.id
    data = {
        **session_data,
        "session_id": session_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "expire_at": _expire_at_timestamp(),  # Firestore TTL field (Timestamp)
    }
    doc_ref.set(data)
    return session_id


def get_session(session_id: str) -> dict[str, Any] | None:
    """
    Get session by session_id. Returns the session dict or None if not found.
    """
    client = _get_client()
    doc_ref = client.collection(COLLECTION).document(session_id)
    doc = doc_ref.get()
    if not doc.exists:
        return None
    return doc.to_dict()


def update_session(session_id: str, updates: dict[str, Any]) -> None:
    """Update a session document with the given fields."""
    client = _get_client()
    doc_ref = client.collection(COLLECTION).document(session_id)
    doc_ref.update(updates)
