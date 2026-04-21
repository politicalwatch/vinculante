from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from alembic import command
from alembic.config import Config
from langchain_core.embeddings import DeterministicFakeEmbedding
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from vinculante.infrastructure.config.settings import get_settings

TEST_DB_NAME = "vinculante_test"
APP_TABLES = ("matches", "sections", "proposals", "target_documents")


def _swap_db(url: str, new_name: str) -> str:
    return url.rsplit("/", 1)[0] + "/" + new_name


@pytest.fixture(scope="session")
def test_db_url() -> str:
    return _swap_db(get_settings().db_url, TEST_DB_NAME)


@pytest.fixture(scope="session", autouse=True)
def _prepare_test_database(test_db_url: str) -> Generator[None, None, None]:
    admin_url = _swap_db(get_settings().db_url, "postgres")
    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"'))
        conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    admin.dispose()

    cfg = Config("alembic.ini")
    prior_db_url = os.environ.get("DB_URL")
    os.environ["DB_URL"] = test_db_url
    try:
        command.upgrade(cfg, "head")
        yield
    finally:
        if prior_db_url is None:
            os.environ.pop("DB_URL", None)
        else:
            os.environ["DB_URL"] = prior_db_url
        admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"'))
        admin.dispose()


@pytest.fixture(scope="session")
def engine(test_db_url: str) -> Generator[Engine, None, None]:
    eng = create_engine(test_db_url)
    yield eng
    eng.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Generator[Session, None, None]:
    SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {', '.join(APP_TABLES)} RESTART IDENTITY CASCADE"))


@pytest.fixture
def embedder() -> DeterministicFakeEmbedding:
    return DeterministicFakeEmbedding(size=8)
