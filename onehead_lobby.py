from steam import SteamClient
from dota2 import Dota2Client, enums
from onehead_common import OneHeadException
from onehead_db import OneHeadDB
from os import getenv
from dotenv import load_dotenv


class OneHeadLobby(object):

    def __init__(self, database):

        self.database = database
        self.steam_client = SteamClient()
        self.dota_client = Dota2Client(self.steam_client)
        self.t1_steam_ids = [76561197968189509]
        self.t2_steam_ids = []

    def launch(self):
        self.dota_client.launch_practice_lobby()

    def set_steam_ids(self, team, team_ids):

        if team == 't1':
            self.t1_steam_ids = team_ids
        elif team == 't2':
            self.t2_steam_ids = team_ids
        else:
            raise OneHeadException("Team should be either 't1' or 't2'.")

    def create_lobby(self):
        self.dota_client.create_practice_lobby(password="banana", options={"game_name": "IGC IHL Match",
                                                                           "server_region": enums.EServerRegion.Europe,
                                                                           "game_mode": enums.DOTA_GameMode.DOTA_GAMEMODE_CM,
                                                                           })
        self.dota_client.wait_event("lobby_new")
        self.dota_client.on("lobby_changed", self.dota_client.join_practice_lobby_team(1, 4))
        self.dota_client.channels.join_lobby_channel()

    def send_invites(self):
        for team_ids in (self.t1_steam_ids, self.t2_steam_ids):
            for steam_id in team_ids:
                if steam_id:
                    self.dota_client.invite_to_lobby(steam_id)

    def launch_dota_client(self):
        self.dota_client.launch()

    def monitor_lobby(self, lobby):

        members = lobby.members._values
        print("Match ID: {}".format(self.dota_client.lobby.match_id))
        for member in members:
            print(member)
            if member.id in self.t1_steam_ids and member.team != 0:
                self.dota_client.channels.lobby.send("{} move to Radiant.".format(member.name))
                return
            elif member.id in self.t2_steam_ids and member.team != 1:
                self.dota_client.channels.lobby.send("{} move to Dire".format(member.name))
                return

        print("Emitting lobby ready.")
        self.dota_client.emit("lobby_ready")

    def setup_lobby(self):

        self.dota_client.on('ready', x.create_lobby())
        self.dota_client.wait_event('ready')
        self.dota_client.on('lobby_changed', self.send_invites())

    def countdown(self):

        print("Countdown starting!")

        for i in reversed(range(6, 1)):
            foo = "Game starting in {}".format(i)
            print(foo)
            self.dota_client.channels.lobby.send(foo)
            self.dota_client.sleep(1)

        print("Emitting start!")
        self.dota_client.emit("start")


load_dotenv()
db = OneHeadDB()
x = OneHeadLobby(db)
x.steam_client.cli_login(username=getenv('STEAM_USER'), password=getenv('STEAM_PASS'))
x.steam_client.on('logged_on', x.dota_client.launch())
# x.dota_client.on('ready', x.dota_client.destroy_lobby)
x.dota_client.on('ready', x.setup_lobby())
x.dota_client.on('lobby_changed', x.monitor_lobby)
x.dota_client.on('lobby_ready', x.countdown)
x.dota_client.on('start', x.launch())
x.steam_client.run_forever()
