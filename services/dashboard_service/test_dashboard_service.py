import contextlib
import pytest
import yaml
from dataclasses import dataclass
from io import StringIO
from unittest.mock import Mock, MagicMock, patch
from typing import Any

import dashboard_service
from dashboard_service import app


YAML_FILENAME = "test_dashboard.yml"

@pytest.fixture()
def client():
    return app.test_client()

def reset():
    dashboard_service.event_store = dashboard_service.EventStore()

def test_from_yaml(client):
    with open(YAML_FILENAME) as fd:
        for check in map(Check.from_dict, yaml.safe_load_all(fd)):
            try:
                check.run(client)
            finally:
                reset()

@dataclass
class Request:
    method: str
    endpoint: str
    query_string: dict[str, str] | None = None
    json: dict[str, Any] | None = None
    headers: dict[str, str] | None = None

    expected_status: str  = "200 OK"
    expected_response: dict | list | str | None = None

    def _get_client_kwargs(self):
        options = dict(method=self.method)
        if self.query_string:
            options.update(query_string=self.query_string)
        if self.json:
            options.update(json=self.json)
        if self.headers:
            options.update(headers=self.headers)
        return options

    def run(self, client):
        options = self._get_client_kwargs()
        response = client.open(self.endpoint, **options)

        assert response.status == self.expected_status

        if isinstance(self.expected_response, dict) or isinstance(self.expected_response, list):
            assert response.json == self.expected_response
        elif self.expected_response is not None:
            assert response.get_data(as_text=True) == self.expected_response

    @classmethod
    def from_dict(cls, request_data):
        return cls(**request_data)

@dataclass
class Check:
    name: str
    steps: list[Request]
    patches: list

    def run(self, client):
        with apply_patches(self.patches):
            for step in self.steps:
                try:
                    step.run(client)
                except AssertionError as e:
                    raise AssertionError(f"Check failed: {step.name}") from e

    @staticmethod
    def _get_patcher(item, kwargs):
        return patch(item, **{k: eval(v) for k, v in kwargs.items()})

    @classmethod
    def from_dict(cls, check_data):
        check_name = check_data["name"]
        steps = list(map(Request.from_dict, check_data["steps"]))

        _patches = check_data.get("patches", {})
        patches = [cls._get_patcher(item, kwargs)
                   for item, kwargs in _patches.items()]

        return Check(name=check_name, steps=steps, patches=patches)

@contextlib.contextmanager
def apply_patches(patches):
    for patcher in patches: patcher.start()
    try:
        yield
    finally:
        for patcher in patches:
            patcher.stop()
