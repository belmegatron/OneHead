from enum import Enum
from typing import Protocol

from onehead.common import Metadata, Player


class Operation(Enum):
    REPLACE = 0
    ADD = 1
    SUBTRACT = 2


class OneHeadDatabase(Protocol):
    def get(self, id: int) -> Player | None:
        pass

    def add(self, id: int, name: str, mmr: int) -> None:
        pass

    def remove(self, id: int) -> None:
        pass

    def get_all(self) -> list[Player]:
        pass

    def modify(
        self,
        id: int,
        key: str,
        value: str | int,
        operation: Operation = Operation.REPLACE,
    ) -> None:
        pass

    def get_metadata(self) -> Metadata:
        pass

    def update_metadata(self, data: Metadata) -> None:
        pass
