from dataclasses import dataclass, asdict
from dacite import from_dict
import json
from pathlib import Path


ROOT_DIR: Path = Path(__file__).resolve().parent.parent


class ConfigException(Exception):
    pass


@dataclass
class TinyDBConfig:
    path: str


@dataclass
class DiscordChannelConfig:
    lobby: str
    match: str


@dataclass
class DiscordConfig:
    token: str
    channels: DiscordChannelConfig
    
    
@dataclass
class Config:
    tinydb: TinyDBConfig
    discord: DiscordConfig


def load_config() -> Config:
    config_path: Path = Path(ROOT_DIR, "secrets/config.json")
    with open(config_path, "r") as f:
        json_blob: dict = json.load(f)
    
    return from_dict(data_class=Config, data=json_blob)


def update_config(updated_config: Config) -> None:
    config_path: Path = Path(ROOT_DIR, "secrets/config.json")
    with open(config_path, "w") as f:
        json.dump(asdict(updated_config), f)

