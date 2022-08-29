from typing import TYPE_CHECKING, Tuple

from discord.ext import commands
from tinydb import Query, TinyDB
from tinydb.operations import add

from onehead.common import OneHeadException

if TYPE_CHECKING:
    from onehead.common import Player


class OneHeadDB(commands.Cog):
    def __init__(self, config: dict):
        self.db = TinyDB(config["tinydb"]["path"])

    def player_exists(self, player_name: str) -> Tuple[bool, int]:

        User = Query()
        
        result = self.db.get(User.name == player_name)
        
        if result:
            return True, result.doc_id
        else:
            return False, -1
        

    def add_player(self, player_name: str, mmr: int):

        if not isinstance(player_name, str):
            raise OneHeadException("Player Name not a valid string.")

        exists, _ = self.player_exists(player_name)
        
        if exists is True:
            raise OneHeadException(f"{player_name} is already registered.")

        self.db.insert(
            {
                "name": player_name,
                "win": 0,
                "loss": 0,
                "mmr": mmr,
                "win_streak": 0,
                "loss_streak": 0,
                "rbucks": 100,
            }
        )

    def remove_player(self, player_name: str):

        if not isinstance(player_name, str):
            raise OneHeadException("Player name not a valid string.")

        exists, doc_id = self.player_exists(player_name)
        
        if exists is False:
            raise OneHeadException(f"{player_name} does not exist in database.")    
        
        self.db.remove(doc_ids=[doc_id])

    def update_rbucks(self, bettor_name: str, rbucks: int):
        
        exists, doc_id = self.player_exists(bettor_name)
        
        if exists is False:
            raise OneHeadException(f"{player_name} cannot be found.")
        
        self.db.update(add("rbucks", rbucks), doc_ids=[doc_id])

    def update_player(self, player_name: str, win: bool):

        exists, doc_id = self.player_exists(player_name)
        
        if exists is False:
            raise OneHeadException(f"{player_name} does not exist in database.")    

        if win:
            self.db.update(add("win", 1), doc_ids=[doc_id])
            self.db.update(add("win_streak", 1), doc_ids=[doc_id])
            self.db.update({"loss_streak", 0}, doc_ids=[doc_id])
            self.db.update(add("rbucks", 100), doc_ids=[doc_id])
        else:
            self.db.update(add("loss", 1), doc_ids=[doc_id])
            self.db.update(add("loss_streak", 1), doc_ids=[doc_id])
            self.db.update({"win_streak", 0}, doc_ids=[doc_id])
            self.db.update(add("rbucks", 50), doc_ids=[doc_id])


    def lookup_player(self, player_name: str) -> "Player":
        
        User = Query()

        response = self.db.get(User.name == player_name)
        if response is False:
            raise OneHeadException(f"Failed to find {player_name} when performing a lookup in the database.")
            
        return response

    def retrieve_table(self) -> list["Player"]:
        table = self.db.table("_default")
        table_dict = table._read_table()
        return table_dict.values()