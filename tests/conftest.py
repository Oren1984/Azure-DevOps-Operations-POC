from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.container import Container
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings(database_path=":memory:")


@pytest.fixture
def container(settings: Settings) -> Container:
    return Container.build(settings)


@pytest.fixture
def app(settings: Settings):
    return create_app(settings)


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)
