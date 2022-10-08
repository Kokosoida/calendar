import json
from typing import AsyncGenerator, Generator

import sqlalchemy.dialects.postgresql
from pydantic.json import pydantic_encoder
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.db import SessionLocal, async_session_maker


def get_db() -> Generator:
    db = None
    try:
        db = SessionLocal(future=True)
        yield db
    finally:
        if db is not None:
            db.close()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
        await session.close()


class PydanticType(sqlalchemy.dialects.postgresql.JSONB):
    """Pydantic type.
    SAVING:
    - Uses SQLAlchemy JSON type under the hood.
    - Acceps the pydantic model and converts it to a dict on save.
    - SQLAlchemy engine JSON-encodes the dict to a string.
    RETRIEVING:
    - Pulls the string from the database.
    - SQLAlchemy engine JSON-decodes the string to a dict.
    - Uses the dict to create a pydantic model.
    """

    impl = sqlalchemy.dialects.postgresql.JSONB

    def __init__(self, pydantic_type):
        super().__init__()
        self.pydantic_type = pydantic_type

    def process_bind_param(self, value, dialect):
        return value.dict() if value else None

    def process_result_value(self, value, dialect):
        return self.pydantic_type.parse_obj(value) if value else None


def json_serializer(*args, **kwargs) -> str:
    return json.dumps(*args, default=pydantic_encoder, **kwargs)
