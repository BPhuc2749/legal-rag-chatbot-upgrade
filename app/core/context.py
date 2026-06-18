import contextvars
from typing import Optional, Dict, Any


# =========================
# Context Variables
# =========================

request_id_var: contextvars.ContextVar[Optional[str]] = (
    contextvars.ContextVar(
        "request_id",
        default=None
    )
)

query_var: contextvars.ContextVar[Optional[str]] = (
    contextvars.ContextVar(
        "query",
        default=None
    )
)

session_id_var: contextvars.ContextVar[Optional[str]] = (
    contextvars.ContextVar(
        "session_id",
        default=None
    )
)

user_id_var: contextvars.ContextVar[Optional[str]] = (
    contextvars.ContextVar(
        "user_id",
        default=None
    )
)


# =========================
# Setters
# =========================

def set_request_id(request_id: str):
    request_id_var.set(request_id)


def set_query(query: str):
    query_var.set(query)


def set_session_id(session_id: str):
    session_id_var.set(session_id)


def set_user_id(user_id: str):
    user_id_var.set(user_id)


# =========================
# Getters
# =========================

def get_request_id() -> Optional[str]:
    return request_id_var.get()


def get_query() -> Optional[str]:
    return query_var.get()


def get_session_id() -> Optional[str]:
    return session_id_var.get()


def get_user_id() -> Optional[str]:
    return user_id_var.get()


# =========================
# Context Snapshot
# =========================

def get_context() -> Dict[str, Any]:
    return {
        "request_id": get_request_id(),
        "query": get_query(),
        "session_id": get_session_id(),
        "user_id": get_user_id(),
    }


# =========================
# Cleanup
# =========================

def clear_context():
    request_id_var.set(None)
    query_var.set(None)
    session_id_var.set(None)
    user_id_var.set(None)