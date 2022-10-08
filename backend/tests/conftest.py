import asyncio
from typing import Generator

import pytest
from pytest_factoryboy import register
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session, sessionmaker
from starlette.testclient import TestClient

from app.core.config import settings
from app.db import Base, _custom_json_serializer
from app.deps.db import get_db
from app.factory import create_app
from tests import factories
from tests.factories import (
    DailyRecurrenceSchemaFactory,
    EventFactory,
    EventInviteFactory,
    MonthlyRecurrenceSchemaFactory,
    UserFactory,
    WeeklyRecurrenceSchemaFactory,
    YearlyRecurrenceSchemaFactory,
)
from tests.utils import generate_random_string

engine = create_engine(settings.DATABASE_URL, json_serializer=_custom_json_serializer)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture(scope="session")
def default_password():
    return generate_random_string(32)


@pytest.fixture(scope="session")
def async_loop():
    loop = asyncio.get_event_loop()
    try:
        yield loop
    finally:
        loop.stop()


@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest.fixture(scope="session")
def client(app) -> Generator:

    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def db() -> Generator:
    # TODO: find out a way to clean up DB between test (use nested transactions?)
    session = TestingSessionLocal()

    yield session

    session.rollback()
    session.commit()


@pytest.fixture(scope="session", autouse=True)
def override_get_db(app):
    db = None
    try:
        db = TestingSessionLocal()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        yield db
    finally:
        if db:
            db.close()
    app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def auto_rollback(db: Session):
    db.rollback()


@pytest.fixture(scope="session", autouse=True)
def set_factory_db(db: Session):
    factories.session = db


register(DailyRecurrenceSchemaFactory)
register(WeeklyRecurrenceSchemaFactory)
register(MonthlyRecurrenceSchemaFactory)
register(YearlyRecurrenceSchemaFactory)
register(UserFactory)
register(EventFactory)
register(EventInviteFactory)
