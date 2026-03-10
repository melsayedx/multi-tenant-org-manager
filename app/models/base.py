from app.core.utils import utcnow, uuid7
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


__all__ = ["Base", "utcnow", "uuid7"]
