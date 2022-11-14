#!/bin/bash
this_dir="$(dirname -- $0)"
python3 -m pip install --upgrade -r "$this_dir/requirements.txt" && python3 -m flask run
