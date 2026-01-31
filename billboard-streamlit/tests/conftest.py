"""!
@file tests/conftest.py
@brief Pytest configuration for import path setup.

Ensures the project root is available on `sys.path` so imports like
`from services...` work when running tests.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
