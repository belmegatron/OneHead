import tomllib
from dataclasses import dataclass
from pathlib import Path

from dacite import from_dict

from onehead.common import ROOT_DIR


CONFIG_PATH: Path = ROOT_DIR / "secrets/config.toml"


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
    with open(CONFIG_PATH, "rb") as f:
        blob: dict = tomllib.load(f)

    return from_dict(data_class=Config, data=blob)
