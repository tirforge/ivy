"""Shared path setup for the test suite.

scripts/ is not a package, so tests add it to sys.path. Each test module
calls `add_scripts_path()` before importing.
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def add_scripts_path() -> None:
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
