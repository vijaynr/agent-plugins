from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS_ROOT = Path(__file__).parents[1] / "skills" / "okf-toolkit" / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))
