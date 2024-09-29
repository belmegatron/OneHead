from abc import abstractmethod, ABC

from onehead.common import Metadata, Player


class PlayerDatabase(ABC):
    @abstractmethod
    def get(self, id: int) -> Player | None:
        raise NotImplementedError()

    @abstractmethod
    def add(self, id: int, name: str, mmr: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def remove(self, id: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_all(self) -> list[Player]:
        raise NotImplementedError()

    @abstractmethod
    def update(self, modified: Player) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_metadata(self) -> Metadata:
        raise NotImplementedError()

    @abstractmethod
    def update_metadata(self, data: Metadata) -> None:
        raise NotImplementedError()
