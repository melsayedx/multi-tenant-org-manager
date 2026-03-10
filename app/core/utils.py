from datetime import datetime, timezone
from uuid import UUID

from uuid_utils import uuid7 as _uuid7


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def uuid7() -> UUID:
    """Return a time-ordered UUID v7 as a standard uuid.UUID for Pydantic compatibility."""
    return UUID(str(_uuid7()))
