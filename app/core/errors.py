"""Domain-level exceptions, translated to HTTP responses at the API boundary."""

from __future__ import annotations


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass
