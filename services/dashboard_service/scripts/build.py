"""Program to build a easy interface to navigate the user notebooks of jupyterhub.

Each notebook /home/username/x.ipynb gets exported to html/x/username.html
"""
import argparse
import os
import os.path
import subprocess
import re
import pathlib
import json

import sys
sys.path.append(os.path.dirname(__name__))
from ipytail import IPyTail

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('-d', '--output-dir', default='html',
                    help="Directory to save the output files")
    p.add_argument("notebooks", nargs="+",
                    help="Notebooks to convert")
    return p.parse_args()

def mkdir_p(path):
    if not os.path.exists(path):
        os.makedirs(path)

def export_notebook(src_path, dest_path, force=False):
    if (not force
        and os.path.exists(dest_path)
        and os.path.getmtime(dest_path) > os.path.getmtime(src_path)):
        return

    notebooks_dir = os.path.join(os.path.dirname(dest_path), "notebooks")
    mkdir_p(notebooks_dir)

    basename = os.path.basename(dest_path).replace(".html", ".ipynb")

    subprocess.call(["ln", "-sf", src_path, "{}/{}".format(notebooks_dir, basename)])

    print("{} -> {}".format(src_path, dest_path))
    cmd = ["jupyter", "nbconvert", "--to", "html", "--stdout", src_path]
    with open(dest_path, "w") as stdout:
        exit_status = subprocess.call(cmd, stdout=stdout)

    return exit_status

def export_summary(path):
    print("export_summary", path)
    p = pathlib.Path(path)

    outputfile = p.joinpath("00-summary.ipynb")
    notebooks = list(p.joinpath("notebooks").glob("*.ipynb"))
    #max_timestamp = max(f.stat().st_mtime for f in notebooks)

    #print("notebooks", notebooks)

    ipytail = IPyTail()
    nb = ipytail.ipytail(sorted(str(f) for f in notebooks if f.exists()))

    notebook_json = json.dumps(nb, indent=True)
    p.joinpath("00-summary.ipynb").write_text(notebook_json)

    cmd = ["jupyter", "nbconvert", "--to", "html", str(p.joinpath("00-summary.ipynb"))]
    subprocess.call(cmd)


re_notebook_path = re.compile("/home/([^/]+)/(.*)\.ipynb")
def find_dest_path(src_path, output_dir):
    m = re_notebook_path.match(src_path)
    if m:
        username, path = m.groups()
        html_path = "{}/{}.html".format(path, username)
    else:
        html_path = src_path.replace(".ipynb", ".html")
    return os.path.join(output_dir, html_path)

def main():
    args = parse_args()

    dest_dirs = set()
    for f in args.notebooks:
        dest_path = find_dest_path(f, args.output_dir)
        # export_notebook(f, dest_path)
        dest_dirs.add(os.path.dirname(dest_path))

    for d in sorted(dest_dirs):
        export_summary(d)

def test_find_dest_path():
    assert find_dest_path("/home/a/x.ipynb", "html") == "html/x/a.html"
    assert find_dest_path("/home/a/x/y.ipynb", "html") == "html/x/y/a.html"
    assert find_dest_path("a/b/x.ipynb", "html") == "html/a/b/x.html"

if __name__ == '__main__':
    main()
