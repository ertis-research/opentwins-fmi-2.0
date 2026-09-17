#!/usr/bin/env bash
# common/ (shared with the other executer) lives one level up, at the repo root.
export PYTHONPATH="$(cd "$(dirname "$0")/.." && pwd)${PYTHONPATH:+:$PYTHONPATH}"
python3 single.py