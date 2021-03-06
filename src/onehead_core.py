from discord.ext import commands
from tabulate import tabulate
from version import __version__, __changelog__
from src.onehead_balance import OneHeadBalance, OneHeadCaptainsMode
from src.onehead_scoreboard import OneHeadScoreBoard
from src.onehead_db import OneHeadDB
from src.onehead_common import OneHeadCommon, OneHeadException
from src.onehead_channels import OneHeadChannels
from src.onehead_user import OneHeadPreGame, OneHeadRegistration


class OneHeadCore(commands.Cog):
    def __init__(self, bot):

        self.game_in_progress = False
        self.t1 = []
        self.t2 = []

        self.bot = bot
        self.config = OneHeadCommon.load_config()
        self.database = OneHeadDB(self.config)
        self.scoreboard = OneHeadScoreBoard(self.database)
        self.pre_game = OneHeadPreGame(self.database)
        self.team_balance = OneHeadBalance(self.database, self.pre_game, self.config)
        self.captains_mode = OneHeadCaptainsMode(self.database, self.pre_game)
        self.channels = OneHeadChannels(self.config)
        self.registration = OneHeadRegistration(self.database)

        bot.add_cog(self.pre_game)
        bot.add_cog(self.scoreboard)
        bot.add_cog(self.registration)
        bot.add_cog(self.captains_mode)

    @commands.has_role("IHL Admin")
    @commands.command()
    async def start(self, ctx, mode="rating"):
        """
        Starts an IHL game. Can optionally select 'cm' mode to start a Captains mode game. This can be done by passing
        the game type after the start command e.g. !start cm.
        """

        if self.game_in_progress:
            await ctx.send("Game already in progress...")
            return

        signup_threshold_met = await self.pre_game.signup_check(ctx)
        if signup_threshold_met is False:
            return

        await self.pre_game.handle_signups(ctx)

        if mode == "rating":
            balanced_teams = await self.team_balance.balance(ctx)
            self.t1, self.t2 = balanced_teams
        elif mode == "cm":
            await self.captains_mode.nomination_phase(ctx)
            t1, t2 = await self.captains_mode.picking_phase(ctx)
            self.t1, self.t2 = t1, t2
        else:
            raise OneHeadException("{} mode is not currently supported.".format(mode))

        self.game_in_progress = True
        status = self.bot.get_command("status")
        await commands.Command.invoke(status, ctx)
        await self.channels.create_discord_channels(ctx)
        self.channels.set_teams(self.t1, self.t2)
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
            self._reset_state()
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
        t1_names, t2_names = OneHeadCommon.get_player_names(self.t1, self.t2)

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
        self._reset_state()

    @commands.has_role("IHL")
    @commands.command(aliases=['stat'])
    async def status(self, ctx):
        """
        If a game is active, displays the teams and their respective players.
        """

        if self.game_in_progress:
            t1_names, t2_names = OneHeadCommon.get_player_names(self.t1, self.t2)
            players = {"Team 1": t1_names, "Team 2": t2_names}
            in_game_players = tabulate(players, headers="keys", tablefmt="simple")
            await ctx.send("**Current Game** ```\n{}```".format(in_game_players))
        else:
            await ctx.send("No currently active game.")

    @commands.has_role("IHL")
    @commands.command(aliases=['v'])
    async def version(self, ctx):
        """
        Displays the current version of OneHead.
        """

        await ctx.send("**Current Version** - {}".format(__version__))
        await ctx.send("**Changelog** - {}".format(__changelog__))

    def _reset_state(self):
        """
        Resets state local to self and creates new instances of OneHeadPreGame and OneHeadCaptainsMode classes.
        """

        self.game_in_progress = False
        self.t1 = []
        self.t2 = []
        self.pre_game = OneHeadPreGame(self.database)
        self.captains_mode = OneHeadCaptainsMode(self.database, self.pre_game)


