"""The release version, read from package.json so there is one source of truth.

Bump it there and the book, the website and the GitHub release all follow.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read_version():
    try:
        return json.loads((ROOT / 'package.json').read_text(encoding='utf-8'))['version']
    except (OSError, ValueError, KeyError):
        return '0.0.0'


VERSION = read_version()
