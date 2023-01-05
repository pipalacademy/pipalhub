import contextlib
import io
import os
import re
import requests
from notebook.utils import to_api_path

EXPORT_DIR = "/tmp/tmp/build/build/"
SAVE_EVENT_TYPE = "save-notebook"

# NOTE: if the jupterhub URL may be different and you don't want to hardcode it
# the service URL can be obtained by hitting the `/services/{name}` endpoint of
# the JupyterHub API (`os.environ['API_URL']`)
EVENTS_ENDPOINT = "http://127.0.0.1:8000/services/dashboard/events"

from nbconvert.exporters.html import HTMLExporter
_script_exporter = HTMLExporter()

def strip_prefix(word, prefix):
    if word.startswith(prefix):
        return word[len(prefix):]
    else:
        return word

def create_parent_dirs(path):
    parent_dir = os.path.dirname(path)
    os.makedirs(parent_dir, exist_ok=True)

re_notebook_path = re.compile("/home/([^/]+)/(.*)\.ipynb")
def find_dest_path(src_path, output_dir):
    m = re_notebook_path.match(src_path)
    if m:
        username, path = m.groups()
        html_path = "{}/{}.html".format(path, username)
    else:
        html_path = src_path.replace(".ipynb", ".html")
    return os.path.join(output_dir, html_path)

def find_symlink_path(src_path):
    dest_path = find_dest_path(src_path, EXPORT_DIR)
    notebooks_dir = os.path.join(os.path.dirname(dest_path), "notebooks")
    basename = os.path.basename(dest_path).replace(".html", ".ipynb")
    return os.path.join(notebooks_dir, basename)

@contextlib.contextmanager
def set_umask(new_mask):
    previous = os.umask(new_mask)
    try:
        yield
    finally:
        os.umask(previous)

def script_post_save(model, os_path, contents_manager, **kwargs):
    """convert notebooks to Python script after save with nbconvert

    replaces `jupyter notebook --script`
    """
    if model['type'] != 'notebook':
        return

    log = contents_manager.log

    script, _ = _script_exporter.from_filename(os_path)
    script_fname = find_dest_path(os_path, EXPORT_DIR)
    create_parent_dirs(script_fname)

    log.info(f"Saving exported HTML: {script_fname}")
    with io.open(script_fname, 'w', encoding='utf-8') as f:
        f.write(script)

    symlink_path = find_symlink_path(os_path)
    if not os.path.exists(symlink_path):
        create_parent_dirs(symlink_path)
        log.info(f"Symlinking notebook to: {symlink_path}")
        os.symlink(os.path.abspath(os_path), symlink_path)

    #debug
    for key, val in os.environ.items():
        if key.startswith("JUPYTERHUB"):
            log.info(f"{key}: {val}")
    #debug

    # send save event to dashboard service
    send_save_event(os_path)

def send_save_event(path):
    filename = get_filename(path)
    body = {
        "user": os.getenv("JUPYTERHUB_USER"),
        "type": SAVE_EVENT_TYPE,
        "filename": filename,
        "path": path,
    }
    r = requests.post(EVENTS_ENDPOINT, json=body)
    r.raise_for_status()

def get_filename(path):
    parts = path.split("/", maxsplit=4)
    filename = (os.path.join(*parts[3:])
                if path.startswith("/home/") and len(parts) > 3
                else path)
    return filename

def script_with_umask(*args, **kwargs):
    with set_umask(0):
        result = script_post_save(*args, **kwargs)
    return result

c.FileContentsManager.post_save_hook = script_with_umask
