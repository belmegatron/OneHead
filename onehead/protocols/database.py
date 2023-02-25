from enum import Enum
from typing import Protocol

from onehead.common import Player


class Operation(Enum):
    REPLACE = 0
    ADD = 1
    SUBTRACT = 2


class IPlayerDatabase(Protocol):
    def get(self, name: str) -> Player | None:
        pass

    def add(self, name: str, mmr: int) -> None:
        pass

    def remove(self, name: str) -> None:
        pass

    def get_all(self) -> list[Player]:
        pass

    def modify(self, name: str, key: str, value: str | int, operation: Operation = Operation.REPLACE) -> None:
        pass
