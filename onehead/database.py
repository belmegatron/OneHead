from typing import cast

from discord.ext import commands
from tinydb import Query, TinyDB
from tinydb.operations import add, subtract
from tinydb.table import Document, Table

from onehead.behaviour import Behaviour
from onehead.betting import Betting
from onehead.common import OneHeadException, Player, Metadata
from onehead.protocols.database import Operation


class Database(commands.Cog):
    def __init__(self, config: dict) -> None:
        self.db: TinyDB = TinyDB(config["tinydb"]["path"])
        self.players: Table = self.db.table("players")
        self.metadata: Table = self.db.table("metadata")

    def _get_document(self, name: str) -> Document | None:
        User: Query = Query()
        result: Document | None = self.players.get(User.name == name)
        return result

    def get(self, name: str) -> Player | None:
        document: Document | None = self._get_document(name)
        player: Player | None = cast(Player, document)
        return player

    def add(self, name: str, mmr: int) -> None:
        player: Player | None = self.get(name)

        if player:
            raise OneHeadException(f"{name} is already registered.")

        self.players.insert(
            {
                "name": name,
                "win": 0,
                "loss": 0,
                "mmr": mmr,
                "win_streak": 0,
                "loss_streak": 0,
                "rbucks": Betting.INITIAL_BALANCE,
                "commends": 0,
                "reports": 0,
                "behaviour": Behaviour.MAX_BEHAVIOUR_SCORE,
            }
        )

    def remove(self, name: str) -> None:
        player: Document | None = self._get_document(name)

        if player is None:
            raise OneHeadException(f"{name} does not exist in database.")

        self.players.remove(doc_ids=[player.doc_id])

    def modify(
        self,
        name: str,
        key: str,
        value: str | int,
        operation: Operation = Operation.REPLACE,
    ) -> None:
        document: Document | None = self._get_document(name)

        if document is None:
            raise OneHeadException(f"{name} does not exist in database.")

        if operation == Operation.REPLACE:
            self.players.update({key: value}, doc_ids=[document.doc_id])
        elif operation == Operation.ADD:
            self.players.update(add(key, value), doc_ids=[document.doc_id])
        elif operation == Operation.SUBTRACT:
            self.players.update(subtract(key, value), doc_ids=[document.doc_id])
        else:
            raise OneHeadException(f"{operation} is not a valid database operation.")

    def get_all(self) -> list[Player]:
        table_dict: dict[str, Player] = self.players._read_table()  # type: ignore
        return list(table_dict.values())

    def get_metadata(self) -> Metadata:
        q: Query = Query()
        result: Document | None = self.metadata.get(q.name == "season")
        meta: Metadata | None = cast(Metadata, result)
        return meta

    def update_metadata(self, data: Metadata) -> None:
        q: Query = Query()
        self.metadata.upsert(data, q.name == "season")
