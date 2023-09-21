from flask import Flask, render_template, send_from_directory, jsonify
from pathlib import Path
import ipytail

app = Flask(__name__)

@app.route("/")
def index():
    notebooks = Path("notebooks").glob("*.ipynb")
    return render_template("index.html", notebooks=list(notebooks))

@app.route("/nb/<name>.ipynb")
def notebook_ipynb(name):
    path = name + ".ipynb"
    return send_from_directory('notebooks', path)


@app.route("/nbtail/<name>.ipynb")
def notebook_tail(name):
    path = Path("notebooks") / (name + ".ipynb")

    tail = ipytail.IPyTail()
    nb = tail.process_file(path)
    return jsonify(nb)


@app.route("/nb/<name>")
def notebook(name):
    return render_template("notebook.html",
                           name=name)

if __name__ == "__main__":
    app.run()