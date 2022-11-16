import os
import json
import secrets
from datetime import date, datetime, timezone
from typing import Optional
from subprocess import check_call

from flask import Flask, abort, request
from flask.json.provider import DefaultJSONProvider
from pydantic import BaseModel, Field, ValidationError


class Event(BaseModel):
    id: Optional[int] = None
    type: str
    user: str
    filename: str
    path: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EventStore:
    def __init__(self):
        self._events = {}
        self._counter = 0

    def _next_id(self):
        self._counter += 1
        current = self._counter
        return current

    def add(self, event):
        key = self._get_key(type=event.type, user=event.user, path=event.path)
        event_id = self._events[key].id if key in self._events else self._next_id()
        event.id = event_id
        self._events[key] = event
        return event

    def find(self, **filters):
        def filter_func(e):
            return all(
                getattr(e, key) == val for key, val in filters.items()
            )
        events = filter(filter_func, self._events.values())
        # any limit or sorting can be applied here
        return list(events)

    def get(self, type, user, path):
        key = self._get_key(type=type, user=user, path=path)
        return self._events.get(key, None)

    def clear(self):
        self._events = []

    def _get_key(self, **kwargs):
        return json.dumps(kwargs)


class CustomJSONProvider(DefaultJSONProvider):
    @staticmethod
    def default(obj):
        if isinstance(obj, date):
            return obj.isoformat()
        else:
            return DefaultJSONProvider.default(obj)


prefix = os.environ.get("JUPYTERHUB_SERVICE_PREFIX", "/")

app = Flask(__name__)
app.secret_key = secrets.token_bytes(32)
app.json = CustomJSONProvider(app)

event_store = EventStore()


@app.route(prefix + "events", methods=["GET", "POST"])
def events():
    if request.method == "POST":
        data = request.json
        if not isinstance(data, dict):
            return abort(400, "JSON data must be an object")

        try:
            event = Event(**data)
        except ValidationError as e:
            return abort(400, e.json())
        else:
            event_store.add(event)
            handle_event(event)
            return event.dict(), 201
    else:
        events = event_store.find(**request.args)
        return [e.dict() for e in events]


def handle_event(event):
    if event.type == "save-notebook":
        on_save_notebook(event)
    else:
        app.logger.warning(f"Unknown event type received: {event.type}")


import glob
buildpy_path = os.path.join(os.path.dirname(__file__), "scripts", "build.py")
build_dir = "/tmp/tmp/build/build"
def on_save_notebook(event):
    filename = event.filename
    args = glob.glob(f"/home/*/{filename}")
    check_call(["python3", buildpy_path, "-d", build_dir, *args])
