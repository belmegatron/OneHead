import time
from tabulate import tabulate
from tinydb import TinyDB, Query, operations
from discord.ext import commands

class OneHeadException(BaseException):
    pass


class TeamBalance(object):

    @staticmethod
    def balance(self, signups, method):
        pass


class Database(object):

    db = TinyDB('db.json', sort_keys=False, indent=4, separators=(',', ': '))
    user = Query()

    @classmethod
    def add_player(cls, player_name):

        if not isinstance(player_name, str):
            raise OneHeadException('Player Name not a valid string.')

        if not cls.db.search(cls.user.name == player_name):
            cls.db.insert({'name': player_name, 'win': 0, 'loss': 0})

    @classmethod
    def remove_player(cls, player_name):

        if not isinstance(player_name, str):
            raise OneHeadException('Player name not a valid string.')

        if cls.db.search(cls.user.name == player_name):
            cls.db.update(operations.delete('win'), cls.user.name == player_name)
            cls.db.update(operations.delete('loss'), cls.user.name == player_name)
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


class ScoreBoard(object):
    database = Database()
    db = database.db
    user = Database.user

    @staticmethod
    def _calculate_win_loss_ratio(scoreboard):

        for record in scoreboard:
            if record["loss"] == 0 or record["win"] == 0:
                record["ratio"] = record["win"]
            else:
                record["ratio"] = float(record["win"] / record["loss"])

    @staticmethod
    def _sort_scoreboard_key_order(scoreboard):

        key_order = ["#", "name", "win", "loss", "ratio"]
        sorted_scoreboard = []

        for record in scoreboard:
            record = {k: record[k] for k in key_order}
            sorted_scoreboard.append(record)

        return sorted_scoreboard

    @staticmethod
    def _calculate_positions(scoreboard, sort_key):

        scoreboard = sorted(scoreboard, key=lambda k: k[sort_key], reverse=True)
        scoreboard_positions = []

        pos = 1
        modifier = 1

        for i, record in enumerate(scoreboard):
            if i != 0:
                if scoreboard[i - 1][sort_key] > scoreboard[i][sort_key]:
                    pos += modifier
                    modifier = 1
                else:
                    modifier += 1

            record["#"] = pos
            scoreboard_positions.append(record)

        return scoreboard_positions

    @classmethod
    def get_scoreboard(cls):

        scoreboard = cls.db.search(cls.user.name.exists())

        if not scoreboard:
            return scoreboard

        cls._calculate_win_loss_ratio(scoreboard)
        sorted_scoreboard = cls._calculate_positions(scoreboard, "ratio")
        sorted_scoreboard = cls._sort_scoreboard_key_order(sorted_scoreboard)
        sorted_scoreboard = tabulate(sorted_scoreboard, headers="keys", tablefmt="simple")

        return sorted_scoreboard


class OneHead(commands.Cog):
    def __init__(self, bot):

        self.bot = bot
        self.database = Database()
        self.game_in_progress = False
        self.is_balanced = False
        self.signups = []
        self.ready_check = []

        self.channel_names = ['IGC IHL #1', 'IGC IHL #2']
        self.channels = []

        self.t1 = []
        self.t2 = []

    def reset_state(self):

        self.game_in_progress = False
        self.is_balanced = False
        self.signups = []
        self.t1 = []
        self.t2 = []

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def start(self, ctx):

        if self.game_in_progress:
            await ctx.send("Game already in progress...")
            return

        signup_count = len(self.signups)
        if signup_count != 10:
            if signup_count == 0:
                await ctx.send("There are currently no signups.")
            elif signup_count == 1:
                await ctx.send("Only {} Signup, require {} more.".format(signup_count, 10 - signup_count))
            else:
                await ctx.send("Only {} Signups, require {} more.".format(signup_count, 10 - signup_count))
            return

        if self.is_balanced is False:
            await self.balance(ctx)

        await self.create_discord_channels(ctx)
        await self.move_discord_channels(ctx)

        await ctx.send("Game starting in ...")
        for second in range(3, 0, -1):
            await ctx.send("{}".format(second))
            time.sleep(1)
        await ctx.send("Go!")
        self.game_in_progress = True

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def stop(self, ctx):
        if self.game_in_progress:
            await ctx.send("Game stopped.")
            self.reset_state()
        else:
            await ctx.send("No currently active game.")

        await self.teardown_discord_channels()

    async def balance(self, ctx):
        await ctx.send("Balancing teams...")
        # TODO: Calculate how to balance teams based on DB entries.
        self.is_balanced = True

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def result(self, ctx, side):
        if self.game_in_progress is False:
            await ctx.send("No currently active game.")
            return

        sides = ["t1", "t2"]

        if side not in sides:
            await ctx.send("Invalid Value - Must be either 't1' or 't2'.")
            return

        await ctx.send("{} Victory!".format(side))
        await ctx.send("Updating Scores...")

        if side == "t1":
            for player in self.t1:
                self.database.update_player(player, True)
            for player in self.t2:
                self.database.update_player(player, False)
        else:
            for player in self.t1:
                self.database.update_player(player, False)
            for player in self.t2:
                self.database.update_player(player, True)

        await commands.Command.invoke(self.scoreboard, ctx)
        await self.move_back_to_lobby(ctx)
        self.reset_state()

    @commands.command(aliases=['sb'])
    async def scoreboard(self, ctx):

        scoreboard = ScoreBoard.get_scoreboard()
        await ctx.send("**IGC Leaderboard** ```\n{}```".format(scoreboard))

    @commands.command(aliases=['reg'])
    async def register(self, ctx):

        if not self.database.db.search(self.database.user.name == ctx.author.display_name):
            self.database.add_player(ctx.author.display_name)
            await ctx.send("Successfully Registered.")
        else:
            await ctx.send("Already registered.")

    @commands.has_permissions(administrator=True)
    @commands.command(aliases=['dereg'])
    async def deregister(self, ctx):

        if self.database.db.search(self.database.user.name == ctx.author.display_name):
            self.database.remove_player(ctx.author.display_name)
            await ctx.send("Successfully Deregistered.")
        else:
            await ctx.send("Discord Name could not be found.")

    @commands.command(aliases=['su'])
    async def signup(self, ctx):
        name = ctx.author.display_name

        if not self.database.db.search(self.database.user.name == name):
            await ctx.send("Please register first using the !reg command.")
            return

        if name in self.signups:
            await ctx.send("{} is already signed up.".format(name))
        elif len(self.signups) >= 10:
            ctx.send("Signups full.")
        else:
            self.signups.append(name)

        await ctx.send("Current Signups: {}".format(self.signups))

    @commands.command(aliases=['so'])
    async def signout(self, ctx):
        if ctx.author.display_name not in self.signups:
            await ctx.send("{} is not currently signed up.".format(ctx.author.display_name))
        else:
            self.signups.remove(ctx.author.display_name)

        await ctx.send("Current Signups: {}".format(self.signups))

    @commands.command(aliases=['rc'])
    async def readycheck(self, ctx):
        pass

    @commands.command(aliases=['r'])
    async def ready(self, ctx):
        pass

    async def create_discord_channels(self, ctx):

        for channel in self.channel_names:
            await ctx.guild.create_voice_channel(channel)

        self.channels = [x for x in ctx.guild.voice_channels if x.name in self.channel_names]

    async def teardown_discord_channels(self):

        for channel in self.channels:
            await channel.delete()

    async def move_back_to_lobby(self, ctx):

        team_1 = [x for x in ctx.guild.members if x.display_name in self.t1]
        team_2 = [x for x in ctx.guild.members if x.display_name in self.t2]

        lobby = [x for x in ctx.guild.voice_channels if x.name == "LOBBY"]

        for member in team_1:
            member.move_to(lobby)
        for member in team_2:
            member.move_to(lobby)

    async def move_discord_channels(self, ctx):

        team_1 = [x for x in ctx.guild.members if x.display_name in self.t1]
        team_2 = [x for x in ctx.guild.members if x.display_name in self.t2]

        for member in team_1:
            member.move_to(self.channel_names[0])
        for member in team_2:
            member.move_to(self.channel_names[1])
