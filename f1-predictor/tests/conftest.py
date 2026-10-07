import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).parent / "unit"))  # tests/unit contains part2b test module
