"""Request correlation ID propagation via a contextvar."""

from __future__ import annotations

from contextvars import ContextVar
from uuid import uuid4

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def new_correlation_id() -> str:
    return str(uuid4())


def set_correlation_id(value: str) -> None:
    _correlation_id.set(value)


def get_correlation_id() -> str | None:
    return _correlation_id.get()
