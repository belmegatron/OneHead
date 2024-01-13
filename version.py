from pathlib import Path
from typing import Any
import toml

from onehead.common import ROOT_DIR


target: Path = Path(ROOT_DIR, "pyproject.toml")
with open(target, "r") as f:
    config: dict[str, Any] = toml.load(f)

__version__ = config["project"]["version"]
__changelog__ = "https://github.com/belmegatron/OneHead/blob/develop/CHANGELOG.md"
