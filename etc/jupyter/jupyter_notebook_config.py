_script_exporter = None
import contextlib
import io
import os
import re
from notebook.utils import to_api_path

EXPORT_DIR = "/tmp/tmp/build/build/"

# debug
import builtins
import sys
def print(*args, **kwargs):
    builtins.print(*args, **kwargs)
    builtins.print(*args, **kwargs, file=sys.stderr)
# debug

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
    from nbconvert.exporters.html import HTMLExporter
    print("inside post save") # debug

    if model['type'] != 'notebook':
        print("not notebook") # debug
        return

    global _script_exporter

    if _script_exporter is None:
        _script_exporter = HTMLExporter(parent=contents_manager)

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

def script_with_umask(*args, **kwargs):
    with set_umask(0):
        result = script_post_save(*args, **kwargs)
    return result

c.FileContentsManager.post_save_hook = script_with_umask
