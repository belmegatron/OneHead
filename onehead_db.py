from tinydb import TinyDB, Query, operations
from onehead_common import OneHeadException


class OneHeadDB(object):
    
    def __init__(self):

        self.db = TinyDB('db.json', sort_keys=False, indent=4, separators=(',', ': '))
        self.user = Query()

    def add_player(self, player_name, mmr):

        if not isinstance(player_name, str):
            raise OneHeadException('Player Name not a valid string.')

        if not self.db.search(self.user.name == player_name):
            self.db.insert({'name': player_name, 'win': 0, 'loss': 0, 'mmr': int(mmr)})

    def remove_player(self, player_name):

        if not isinstance(player_name, str):
            raise OneHeadException('Player name not a valid string.')

        if self.db.search(self.user.name == player_name):
            self.db.update(operations.delete('win'), self.user.name == player_name)
            self.db.update(operations.delete('loss'), self.user.name == player_name)
            self.db.update(operations.delete('mmr'), self.user.name == player_name)
            self.db.update(operations.delete('name'), self.user.name == player_name)

    def update_player(self, player_name, win):

        if not isinstance(win, bool):
            raise OneHeadException('Win parameter must be a valid bool.')

        if not isinstance(player_name, str):
            raise OneHeadException('Player Name not a valid string.')

        if not self.db.search(self.user.name == player_name):
            raise OneHeadException('Player cannot be found.')

        if win:
            self.db.update(operations.increment('win'), self.user.name == player_name)
        else:
            self.db.update(operations.increment('loss'), self.user.name == player_name)

    def lookup_player(self, player_name):

        player = self.db.search(self.user.name == player_name)
        if player:
            return player[0]

        return player
