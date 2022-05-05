from discord import Intents
from discord.ext import commands

from tabulate import tabulate
from version import __changelog__, __version__

import onehead.common

from onehead.balance import OneHeadBalance, OneHeadCaptainsMode
from onehead.betting import OneHeadBetting
from onehead.channels import OneHeadChannels
from onehead.common import OneHeadCommon, OneHeadException, RADIANT, DIRE
from onehead.db import OneHeadDB
from onehead.mental_health import OneHeadMentalHealth
from onehead.scoreboard import OneHeadScoreBoard

from onehead.user import (
    OneHeadPreGame,
    OneHeadRegistration,
    on_voice_state_update,
    on_member_update,
)


def bot_factory() -> commands.Bot:
    """
    Factory method for generating an instance of our Bot.

    :return: OneHead Bot
    """

    intents = Intents.all()
    intents.members = True
    intents.presences = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    config = OneHeadCommon.load_config()

    database = OneHeadDB(config)
    scoreboard = OneHeadScoreBoard(database)
    pre_game = OneHeadPreGame(database)
    team_balance = OneHeadBalance(database, pre_game, config)
    captains_mode = OneHeadCaptainsMode(database, pre_game)
    channels = OneHeadChannels(config)
    registration = OneHeadRegistration(database)
    mental_health = OneHeadMentalHealth()
    betting = OneHeadBetting(database)

    bot.add_cog(database)
    bot.add_cog(pre_game)
    bot.add_cog(scoreboard)
    bot.add_cog(registration)
    bot.add_cog(captains_mode)
    bot.add_cog(team_balance)
    bot.add_cog(channels)
    bot.add_cog(mental_health)
    bot.add_cog(betting)

    # Add cogs first, then instantiate OneHeadCore as we reference them as instance variables
    token = config["discord"]["token"]
    core = OneHeadCore(bot, token)
    bot.add_cog(core)

    # Register events
    bot.event(on_voice_state_update)
    bot.event(on_member_update)

    onehead.common.bot = bot

    return bot


class OneHeadCore(commands.Cog):
    def __init__(self, bot: commands.Bot, token: str):

        self.game_in_progress = False
        self.radiant = []  # type: list[dict]
        self.dire = []  # type: list[dict]

        self.bot = bot
        self.token = token

        self.config = OneHeadCommon.load_config()
        self.database = bot.get_cog("OneHeadDB")
        self.scoreboard = bot.get_cog("OneHeadScoreBoard")
        self.pre_game = bot.get_cog("OneHeadPreGame")
        self.team_balance = bot.get_cog("OneHeadBalance")
        self.captains_mode = bot.get_cog("OneHeadCaptainsMode")
        self.channels = bot.get_cog("OneHeadChannels")
        self.registration = bot.get_cog("OneHeadRegistration")
        self.betting = bot.get_cog("OneHeadBetting")

        if None in (
                self.database,
                self.scoreboard,
                self.pre_game,
                self.team_balance,
                self.captains_mode,
                self.channels,
                self.registration,
                self.betting
        ):
            raise OneHeadException("Unable to find cog(s)")

    @commands.has_role("IHL Admin")
    @commands.command()
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    async def start(self, ctx: commands.Context, captains_mode=False):
        """
        Starts an IHL game. Can optionally select 'cm' mode to start a Captain's mode game. This can be done by passing
        the game type after the start command e.g. !start cm.
        """

        if self.game_in_progress:
            await ctx.send("Game already in progress...")
            return

        signup_threshold_met = await self.pre_game.signup_check(ctx)
        if signup_threshold_met is False:
            return

        await self.pre_game.handle_signups(ctx)

        if captains_mode is False:
            balanced_teams = await self.team_balance.balance(ctx)
            self.radiant, self.dire = balanced_teams
        else:
            await self.captains_mode.nomination_phase(ctx)
            radiant, dire = await self.captains_mode.picking_phase(ctx)
            self.radiant, self.dire = radiant, dire

        self.game_in_progress = True
        self.pre_game.disable_signups()
        status = self.bot.get_command("status")
        await commands.Command.invoke(status, ctx)
        await self.channels.create_discord_channels(ctx)
        self.channels.set_teams(self.radiant, self.dire)
        await self.channels.move_discord_channels(ctx)
        await ctx.send("Setup Lobby in Dota 2 Client and join with the above teams.")

    @commands.has_role("IHL Admin")
    @commands.command()
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    async def stop(self, ctx: commands.Context):
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
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    async def result(self, ctx: commands.Context, result: str):
        """
        Provide the result of game that has finished. Can pass 'void' if the match did not correctly terminate.
        """

        if self.game_in_progress is False:
            await ctx.send("No currently active game.")
            return

        accepted_results = [RADIANT, DIRE]

        if result not in accepted_results:
            await ctx.send(f"Invalid Value - Must be either {RADIANT} or {DIRE}.")

            return

        await ctx.send("Updating Scores...")
        radiant_names, dire_names = OneHeadCommon.get_player_names(self.radiant, self.dire)

        if result == RADIANT:
            await ctx.send("Radiant Victory!")
            for player in radiant_names:
                self.database.update_player(player, True)
            for player in dire_names:
                self.database.update_player(player, False)
        elif result == DIRE:
            await ctx.send("Dire Victory!")
            for player in radiant_names:
                self.database.update_player(player, False)
            for player in dire_names:
                self.database.update_player(player, True)

        scoreboard = self.bot.get_command("scoreboard")
        await commands.Command.invoke(scoreboard, ctx)
        await self.channels.move_back_to_lobby(ctx)
        self._reset_state()

    @commands.has_role("IHL")
    @commands.command()
    async def status(self, ctx: commands.Context):
        """
        If a game is active, displays the teams and their respective players.
        """

        if self.game_in_progress:
            t1_names, t2_names = OneHeadCommon.get_player_names(self.radiant, self.dire)
            players = {RADIANT: t1_names, DIRE: t2_names}
            in_game_players = tabulate(players, headers="keys", tablefmt="simple")
            await ctx.send(f"**Current Game** ```\n" f"{in_game_players}```")
        else:
            await ctx.send("No currently active game.")

    @commands.has_role("IHL")
    @commands.command()
    async def version(self, ctx: commands.Context):
        """
        Displays the current version of OneHead.
        """

        await ctx.send(f"**Current Version** - {__version__}")
        await ctx.send(f"**Changelog** - {__changelog__}")

    @commands.has_role("IHL Admin")
    @commands.command()
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    async def reset(self, ctx: commands.Context):
        """
        Resets the current bot state.
        """

        self._reset_state()
        await ctx.send("Reset.")

    @commands.command()
    async def matches(self, ctx: commands.Context):
        """
        Display the top 10 most recent matches in the IHL.
        """
        await ctx.send(
            "https://www.dotabuff.com/esports/leagues/13630-igc-inhouse-league"
        )

    def _reset_state(self):
        """
        Resets state local to self and creates new instances of OneHeadPreGame and OneHeadCaptainsMode classes.
        """

        self.game_in_progress = False
        self.radiant = []
        self.dire = []

        self.pre_game.reset_state()
        self.captains_mode.reset_state()
