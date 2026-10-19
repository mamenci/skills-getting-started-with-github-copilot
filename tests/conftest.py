from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def initial_activities():
    return deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def isolated_activities(monkeypatch, initial_activities):
    monkeypatch.setattr(app_module, "activities", deepcopy(initial_activities))


@pytest.fixture
def client(isolated_activities):
    with TestClient(app_module.app) as test_client:
        yield test_client