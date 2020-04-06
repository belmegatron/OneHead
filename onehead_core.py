from discord.ext import commands
from tabulate import tabulate
from onehead_balance import OneHeadBalance
from onehead_scoreboard import OneHeadScoreBoard
from onehead_db import OneHeadDB
from onehead_common import OneHeadChannels
from onehead_user import OneHeadPreGame, OneHeadRegistration


class OneHeadCore(commands.Cog):
    def __init__(self, bot):

        self.game_in_progress = False
        self.t1 = []
        self.t2 = []

        self.bot = bot
        self.database = OneHeadDB()
        self.scoreboard = OneHeadScoreBoard(self.database)
        self.pre_game = OneHeadPreGame(self.database)
        self.team_balance = OneHeadBalance(self.database, self.pre_game)
        self.channels = OneHeadChannels(self.t1, self.t2)
        self.registration = OneHeadRegistration(self.database)

        bot.add_cog(self.pre_game)
        bot.add_cog(self.scoreboard)
        bot.add_cog(self.registration)

    @commands.has_role("IHL Admin")
    @commands.command()
    async def start(self, ctx):
        """
        Starts an IHL game.
        """
        if self.game_in_progress:
            await ctx.send("Game already in progress...")
            return

        signups_full = await self.pre_game.signup_check(ctx)
        if signups_full is False:
            return

        balanced_teams = await self.team_balance.balance(ctx)
        self.t1, self.t2 = balanced_teams
        self.team_balance.is_balanced = True

        if self.team_balance.is_balanced:
            self.game_in_progress = True
            status = self.bot.get_command("status")
            await commands.Command.invoke(status, ctx)
            await ctx.send("Setting up IHL Discord Channels...")
            await self.channels.create_discord_channels(ctx)
            await ctx.send("Moving Players to IHL Discord Channels...")
            self.channels.t1 = self.t1
            self.channels.t2 = self.t2
            await self.channels.move_discord_channels(ctx)

            await ctx.send("Setup Lobby in Dota 2 Client and join with the above teams.")

    @commands.has_role("IHL Admin")
    @commands.command()
    async def stop(self, ctx):
        """
        Cancels an IHL game. Can alternatively void a result using the !result command.
        """

        if self.game_in_progress:
            await ctx.send("Game stopped.")
            await self.channels.move_back_to_lobby(ctx)
            await self.channels.teardown_discord_channels()
            self.reset_state()
        else:
            await ctx.send("No currently active game.")

    @commands.has_role("IHL Admin")
    @commands.command()
    async def result(self, ctx, result):
        """
        Provide the result of game that has finished. Can pass 'void' if the match did not correctly terminate.
        """
        if self.game_in_progress is False:
            await ctx.send("No currently active game.")
            return

        accepted_results = ["t1", "t2", "void"]

        if result not in accepted_results:
            await ctx.send("Invalid Value - Must be either 't1' or 't2' or 'void' if appropriate.")
            return

        await ctx.send("Updating Scores...")

        t1_names = [x['name'] for x in self.t1]
        t2_names = [x['name'] for x in self.t2]

        if result == "t1":
            await ctx.send("Team 1 Victory!")
            for player in t1_names:
                self.database.update_player(player, True)
            for player in t2_names:
                self.database.update_player(player, False)
        elif result == "t2":
            await ctx.send("Team 2 Victory!")
            for player in t1_names:
                self.database.update_player(player, False)
            for player in t2_names:
                self.database.update_player(player, True)

        scoreboard = self.bot.get_command("scoreboard")
        await commands.Command.invoke(scoreboard, ctx)
        await self.channels.move_back_to_lobby(ctx)
        await self.channels.teardown_discord_channels()
        self.reset_state()

    @commands.command(aliases=['stat'])
    async def status(self, ctx):
        """
        If a game is active, displays the teams and their respective players.
        """
        if self.game_in_progress:
            t1_names = [x['name'] for x in self.t1]
            t2_names = [x['name'] for x in self.t2]
            players = {"Team 1": t1_names, "Team 2": t2_names}
            ig_players = tabulate(players, headers="keys", tablefmt="simple")
            await ctx.send("**Current Game** ```\n{}```".format(ig_players))
        else:
            await ctx.send("No currently active game.")

    def reset_state(self):

        self.game_in_progress = False
        self.team_balance.is_balanced = False
        self.t1 = []
        self.t2 = []


