# Project commands

Use Python 3 standard library in `venv`: `python3 -m venv venv`.
Build: `venv/bin/python scripts/build.py`.
Verify: `venv/bin/python -m unittest discover -s tests -v`.
Serve the static website: `venv/bin/python -m http.server 8765 --bind 127.0.0.1 --directory docs`.
Never overwrite a locked forecast. Results and evaluation are separate artifacts.
No forecast publication after 2026-10-21 23:59 Europe/Bratislava.

