import os
import sys

# Ensure the project root is on sys.path so imports like "from app..." work.
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest

pytest_plugins = ("pytest_asyncio",)
