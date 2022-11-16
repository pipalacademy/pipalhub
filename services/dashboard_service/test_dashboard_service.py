import pytest
import yaml
from datetime import datetime

import dashboard_service
from dashboard_service import app


YAML_FILENAME = "test_dashboard.yml"


@pytest.fixture()
def client():
    return app.test_client()


def test_create_new_event(client):
    ts_json = "2022-11-14T16:00:00.511Z"
    ts_datetime = datetime.fromisoformat(ts_json.replace("Z", "+00:00"))
    event_data = {
        "type": "test-event",
        "user": "alice",
        "filename": "module1-day1.ipynb",
        "path": "/home/alice/module1-day1.ipynb",
        "timestamp": ts_json,
    }

    response = client.post(
        "/events",
        json=event_data,
    )
    assert response.status_code == 201
    response_data = response.json
    id = response_data.pop("id")
    assert id is not None
    assert response_data == {
        **event_data,
        "timestamp": ts_datetime.isoformat()
    }

    response = client.get("/events", query_string={"user": "alice"})
    assert response.status_code == 200
    expected = [
        {
            "id": id,
            **event_data,
            "timestamp": ts_datetime.isoformat(),
        }
    ]
    assert response.json == expected


def check_request(client, method, endpoint,
                  query_string=None, json=None,
                  expected_status="200 OK", expected_response=None):
    options = dict(method=method)
    if query_string:
        options.update(query_string=query_string)
    if json:
        options.update(json=json)

    response = client.open(endpoint, **options)

    assert response.status == expected_status

    if isinstance(expected_response, dict) or isinstance(expected_response, list):
        assert response.json == expected_response
    elif expected_response is not None:
        assert response.get_data(as_text=True) == expected_response


def reset():
    dashboard_service.event_store = dashboard_service.EventStore()


def test_from_yaml(client):
    with open(YAML_FILENAME) as fd:
        for check_data in yaml.safe_load_all(fd):
            reset()
            for kwargs in load_check(check_data):
                check_request(client, **kwargs)


def load_check(check_data):
    if isinstance(check_data, list):
        for check in check_data:
            yield from load_check(check)
    elif isinstance(check_data, dict):
        yield check_data
    else:
        raise ValueError(f"Can't parse value: {check_data}")
