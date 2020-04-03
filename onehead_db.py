from tinydb import TinyDB, Query, operations
from onehead_common import OneHeadException


class OneHeadDB(object):

    db = TinyDB('db.json', sort_keys=False, indent=4, separators=(',', ': '))
    user = Query()

    @classmethod
    def add_player(cls, player_name, mmr):

        if not isinstance(player_name, str):
            raise OneHeadException('Player Name not a valid string.')

        if not cls.db.search(cls.user.name == player_name):
            cls.db.insert({'name': player_name, 'win': 0, 'loss': 0, 'mmr': mmr})

    @classmethod
    def remove_player(cls, player_name):

        if not isinstance(player_name, str):
            raise OneHeadException('Player name not a valid string.')

        if cls.db.search(cls.user.name == player_name):
            cls.db.update(operations.delete('win'), cls.user.name == player_name)
            cls.db.update(operations.delete('loss'), cls.user.name == player_name)
            cls.db.update(operations.delete('mmr'), cls.user.name == player_name)
            cls.db.update(operations.delete('name'), cls.user.name == player_name)

    @classmethod
    def update_player(cls, player_name, win):

        if not isinstance(win, bool):
            raise OneHeadException('Win parameter must be a valid bool.')

        if not isinstance(player_name, str):
            raise OneHeadException('Player Name not a valid string.')

        if not cls.db.search(cls.user.name == player_name):
            raise OneHeadException('Player cannot be found.')

        if win:
            cls.db.update(operations.increment('win'), cls.user.name == player_name)
        else:
            cls.db.update(operations.increment('loss'), cls.user.name == player_name)

    @classmethod
    def lookup_player(cls, player_name):

        player = cls.db.search(cls.user.name == player_name)
        return player
