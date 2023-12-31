from typing import Any
import toml

with open("pyproject.toml", "r") as f:
    config: dict[str, Any] = toml.load(f)

__version__ = config["project"]["version"]
__changelog__ = "https://github.com/belmegatron/OneHead/blob/develop/CHANGELOG.md"
