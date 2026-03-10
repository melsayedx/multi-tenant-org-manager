from sqlalchemy.orm import DeclarativeBase

from app.core.utils import utcnow, uuid7


class Base(DeclarativeBase):
    pass


__all__ = ["Base", "utcnow", "uuid7"]
