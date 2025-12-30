from pathlib import Path
from typing import Any

import tomllib

from onehead.common import ROOT_DIR


target: Path = Path(ROOT_DIR, "pyproject.toml")
with open(target, "rb") as f:
    pyproject: dict[str, Any] = tomllib.load(f)

__version__ = pyproject["project"]["version"]
__changelog__ = "https://github.com/belmegatron/OneHead/blob/develop/CHANGELOG.md"
