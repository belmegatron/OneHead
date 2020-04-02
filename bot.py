from tabulate import tabulate
from tinydb import TinyDB, Query, operations
from discord.ext import commands
from itertools import combinations
from random import choice
from asyncio import sleep


class OneHeadException(BaseException):
    pass


class Database(object):

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


class ScoreBoard(object):

    def __init__(self, database):

        self.database = database
        self.db = self.database.db
        self.user = self.database.user

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

    def get_scoreboard(self):

        scoreboard = self.db.search(self.user.name.exists())

        if not scoreboard:
            return scoreboard

        self._calculate_win_loss_ratio(scoreboard)
        sorted_scoreboard = self._calculate_positions(scoreboard, "ratio")
        sorted_scoreboard = self._sort_scoreboard_key_order(sorted_scoreboard)
        sorted_scoreboard = tabulate(sorted_scoreboard, headers="keys", tablefmt="simple")

        return sorted_scoreboard


class TeamBalance(object):

    def __init__(self, onehead):

        self.onehead = onehead
        self.database = self.onehead.database

    def balance(self):

        profiles = []
        for player in self.onehead.signups:
            profile = self.database.db.lookup_player(player)
            profiles.append(profile)

        all_five_man_lineups = list(combinations(profiles, 5))
        all_matchups = list(combinations(all_five_man_lineups, 2))
        valid_combinations = []

        for matchup in all_matchups:
            share_players = False
            for player in list(matchup[0]):
                if player in list(matchup[1]):
                    share_players = True
            if share_players is False:
                valid_combinations.append(matchup)

        rating_differences = []
        for vc in valid_combinations:
            t1_rating = sum([player["mmr"] for player in vc[0]])
            t2_rating = sum([player["mmr"] for player in vc[1]])
            rating_difference = abs(t1_rating - t2_rating)
            rating_differences.append(rating_difference)

        rating_differences = dict(enumerate(rating_differences, start=0))
        rating_differences = {k: v for k, v in sorted(rating_differences.items(), key=lambda item: item[1])}
        indices = list(rating_differences.keys())[:10]
        balanced_teams = valid_combinations[choice(indices)]

        return balanced_teams


class OneHead(commands.Cog):
    def __init__(self, bot):

        self.bot = bot
        self.database = Database()
        self.scoreboard = ScoreBoard(self.database)
        self.team_balance = TeamBalance(self)
        self.game_in_progress = False
        self.is_balanced = False
        self.signups = []
        self.players_ready = []

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

        signups_full = await self.signup_check(ctx)
        if signups_full is False:
            return

        await self.balance(ctx)

        if self.is_balanced:
            await self.create_discord_channels(ctx)
            await self.move_discord_channels(ctx)

            await ctx.send("Game starting in ...")
            for second in range(3, 0, -1):
                await ctx.send("{}".format(second))
                await sleep(1)
            await ctx.send("Go!")
            self.game_in_progress = True

    async def signup_check(self, ctx):

        signups_full = False
        signup_count = len(self.signups)
        if signup_count != 10:
            if signup_count == 0:
                await ctx.send("There are currently no signups.")
            elif signup_count == 1:
                await ctx.send("Only {} Signup, require {} more.".format(signup_count, 10 - signup_count))
            else:
                await ctx.send("Only {} Signups, require {} more.".format(signup_count, 10 - signup_count))
        else:
            signups_full = True

        return signups_full

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def stop(self, ctx):
        if self.game_in_progress:
            await ctx.send("Game stopped.")
            await self.move_back_to_lobby(ctx)
            await self.teardown_discord_channels()
            self.reset_state()
        else:
            await ctx.send("No currently active game.")

    async def balance(self, ctx):
        signup_count = len(self.signups)
        await ctx.send("Balancing teams...")
        if len(self.signups) != 10:
            await ctx.send("Only {} Signups, require {} more.".format(signup_count, 10 - signup_count))
            return

        balanced_teams = self.team_balance.balance()
        self.t1 = balanced_teams[0]
        self.t1 = balanced_teams[1]
        self.is_balanced = True

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def result(self, ctx, result):
        if self.game_in_progress is False:
            await ctx.send("No currently active game.")
            return

        accepted_results = ["t1", "t2", "void"]

        if result not in accepted_results:
            await ctx.send("Invalid Value - Must be either 't1' or 't2' or 'void' if appropriate.")
            return

        await ctx.send("Updating Scores...")

        if result == "t1":
            await ctx.send("Team 1 Victory!")
            for player in self.t1:
                self.database.update_player(player, True)
            for player in self.t2:
                self.database.update_player(player, False)
        elif result == "t2":
            await ctx.send("Team 2 Victory!")
            for player in self.t1:
                self.database.update_player(player, False)
            for player in self.t2:
                self.database.update_player(player, True)

        await commands.Command.invoke(self.scoreboard.get_scoreboard(), ctx)
        await self.move_back_to_lobby(ctx)
        self.reset_state()

    @commands.command(aliases=['sb'])
    async def scoreboard(self, ctx):

        scoreboard = self.scoreboard.get_scoreboard()
        await ctx.send("**IGC Leaderboard** ```\n{}```".format(scoreboard))

    @commands.command(aliases=['reg'])
    async def register(self, ctx, mmr):

        name = ctx.author.display_name

        if not self.database.db.search(self.database.user.name == name):
            self.database.add_player(ctx.author.display_name, mmr)
            await ctx.send("{} successfully registered.".format(name))
        else:
            await ctx.send("{} is already registered.".format(name))

    @commands.has_permissions(administrator=True)
    @commands.command(aliases=['dereg'])
    async def deregister(self, ctx):

        if self.database.db.search(self.database.user.name == ctx.author.display_name):
            self.database.remove_player(ctx.author.display_name)
            await ctx.send("Successfully Deregistered.")
        else:
            await ctx.send("Discord Name could not be found.")

    @commands.command()
    async def who(self, ctx):
        await ctx.send("Current Signups: {}".format(self.signups))

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def summon(self, ctx):

        all_registered_players = self.database.db.search(self.database.user.name.exists())
        names = [x['name'] for x in all_registered_players]
        members = [x for x in ctx.guild.members if x.display_name in names]
        mentions = " ".join([x.mention for x in members])
        message = "IT'S DOTA TIME BOYS! Summoning all 1Heads - {}".format(mentions)
        await ctx.send(message)

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
    async def ready_check(self, ctx):

        if await self.signup_check(ctx):
            await ctx.send("Ready Check Started, 30s remaining - type '!ready' to ready up.")
            await sleep(30)
            players_ready_count = len(self.players_ready)
            players_not_ready = " ,".join([x for x in self.signups if x not in self.players_ready])
            if players_ready_count == 10:
                await ctx.send("Ready Check Complete - All players ready.")
            else:
                await ctx.send("Still waiting on {} players: {}".format(10 - players_ready_count, players_not_ready))

        self.players_ready = []

    @commands.command(aliases=['r'])
    async def ready(self, ctx):
        name = ctx.author.display_name

        if name not in self.signups:
            await ctx.send("{} needs to sign in first.".format(name))
            return

        self.players_ready.append(name)
        await ctx.send("{} is ready.".format(name))

    @commands.command()
    async def rugor(self, ctx):
        await ctx.send("Everyone SHUT the FUCK up. Lewis has something to say, please speak my good sir.", tts=True)

    @commands.command(aliases=['stat'])
    async def status(self, ctx):

        if self.game_in_progress:
            players = {"Team 1": self.t1, "Team 2": self.t2}
            ig_players = tabulate(players, headers="keys", tablefmt="simple")
            await ctx.send("**Current Game** ```\n{}```".format(ig_players))
        else:
            await ctx.send("No currently active game.")

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
