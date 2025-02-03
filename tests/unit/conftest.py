import sys
from pathlib import Path

import pytest

# Add the src directory to Python path for importing vmpilot
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))
