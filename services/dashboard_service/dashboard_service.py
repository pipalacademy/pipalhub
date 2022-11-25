import os
import json
import secrets
import string
import pwd
from datetime import date, datetime, timezone
from functools import wraps
from subprocess import check_call
from typing import Optional

from flask import Flask, abort, request
from flask.json.provider import DefaultJSONProvider
from pydantic import BaseModel, Field, ValidationError

from jupyterhub.services.auth import HubAuth


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

auth = HubAuth(cache_max_age=60)

def authenticated(f):
    """Decorator for authenticating with Hub"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_auth_token(request.headers.get("authorization", ""))
        if token:
            user = auth.user_for_token(token)
        else:
            user = None

        if user:
            # this authorizes any user of the JupyterHub system, not just admins
            # TODO: take a call on whether to continue this or to add more elaborate
            # authentication (such as only allowing certain usernames or only admins)
            app.logger.info(f"[{request.path}] Authorizing user {user['name']}")
            return f(*args, **kwargs)
        else:
            app.logger.info(f"[{request.path}] Authorization denied due to invalid token")
            abort(401)

    return decorated


def get_auth_token(header):
    parts = header.split(maxsplit=1)
    if len(parts) == 2 and parts[0].lower() == "token":
        return parts[1]
    else:
        return None

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


@app.route(prefix + "users", methods=["POST"])
@authenticated
def users():
    data = request.json
    if not isinstance(data, dict):
        return {"message": "JSON data must be an object"}, 400

    username, password = data["username"], data["password"]
    if not validate_username(username):
        return {"message": "Username is invalid"}, 400
    elif not validate_password(password):
        return {"message": "Password is invalid"}, 400
    elif does_user_exist(username):
        return {"message": "User already exists"}, 400

    create_user(username=username, password=password)
    return {"username": username}, 201


def create_user(username, password):
    usersfile = "/srv/jupyterhub/users.txt"
    add_users_py = "/opt/jhub/add-users.py"

    with open(usersfile, "a") as f:
        f.write(f"{username}:{password}\n")
    check_call(["python3", add_users_py, usersfile])


def does_user_exist(username):
    try:
        pwd.getpwnam(username)
    except KeyError:
        return False
    else:
        return True


def validate_username(val):
    allowed_chars = string.ascii_letters + string.digits
    return all(char in allowed_chars for char in val)


def validate_password(val):
    allowed_chars = string.ascii_letters + string.digits
    return all(char in allowed_chars for char in val)


import glob
buildpy_path = os.path.join(os.path.dirname(__file__), "scripts", "build.py")
build_dir = "/tmp/tmp/build/build"
def on_save_notebook(event):
    filename = event.filename
    args = glob.glob(f"/home/*/{filename}")
    check_call(["python3", buildpy_path, "-d", build_dir, *args])
