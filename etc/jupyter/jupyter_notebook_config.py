_script_exporter = None
import io
import os
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

    base, ext = os.path.splitext(os_path)
    script, resources = _script_exporter.from_filename(os_path)
    script_fname = os.path.join(EXPORT_DIR, strip_prefix(base, "/home/") + resources.get('output_extension', '.txt'))
    create_parent_dirs(script_fname)
    log.info("Saving exported HTML: " + str(script_fname))

    with io.open(script_fname, 'w', encoding='utf-8') as f:
        f.write(script)

c.FileContentsManager.post_save_hook = script_post_save
