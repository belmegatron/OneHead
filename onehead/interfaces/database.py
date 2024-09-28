from abc import abstractmethod

from discord.ext.commands import CogMeta
from onehead.common import Metadata, Player


class PlayerDatabase(metaclass=CogMeta):
    
    @abstractmethod
    def get(self, id: int) -> Player | None:
        pass

    @abstractmethod
    def add(self, id: int, name: str, mmr: int) -> None:
        pass

    @abstractmethod
    def remove(self, id: int) -> None:
        pass

    @abstractmethod
    def get_all(self) -> list[Player]:
        pass

    @abstractmethod
    def update(
        self,
        modified: Player
    ) -> None:
        pass

    @abstractmethod
    def get_metadata(self) -> Metadata:
        pass

    @abstractmethod
    def update_metadata(self, data: Metadata) -> None:
        pass
