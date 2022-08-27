import asyncio
from typing import TYPE_CHECKING, Optional

from discord import Intents
from discord.ext import commands
from tabulate import tabulate

import onehead.common
from onehead.balance import OneHeadBalance
from onehead.betting import OneHeadBetting
from onehead.channels import OneHeadChannels
from onehead.common import DIRE, RADIANT, OneHeadCommon, OneHeadException
from onehead.db import OneHeadDB
from onehead.mental_health import OneHeadMentalHealth
from onehead.scoreboard import OneHeadScoreBoard
from onehead.user import (OneHeadPreGame, OneHeadRegistration,
                          on_member_update, on_voice_state_update)
from version import __changelog__, __version__

if TYPE_CHECKING:
    from onehead.common import Team


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
    team_balance = OneHeadBalance(database, pre_game)
    channels = OneHeadChannels(config)
    registration = OneHeadRegistration(database)
    mental_health = OneHeadMentalHealth()
    betting = OneHeadBetting(database, pre_game)

    bot.add_cog(database)
    bot.add_cog(pre_game)
    bot.add_cog(scoreboard)
    bot.add_cog(registration)
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
        self.player_transfer_window_open = False
        self.radiant = None  # type: Optional[Team]
        self.dire = None  # type: Optional[Team]
        self.game_cancelled = asyncio.Event()

        self.player_transactions = []  # type: list[dict]

        self.bot = bot
        self.token = token

        self.config = OneHeadCommon.load_config()
        self.database = bot.get_cog("OneHeadDB")
        self.scoreboard = bot.get_cog("OneHeadScoreBoard")
        self.pre_game = bot.get_cog("OneHeadPreGame")
        self.team_balance = bot.get_cog("OneHeadBalance")
        self.channels = bot.get_cog("OneHeadChannels")
        self.registration = bot.get_cog("OneHeadRegistration")
        self.betting = bot.get_cog("OneHeadBetting")

        if None in (
            self.database,
            self.scoreboard,
            self.pre_game,
            self.team_balance,
            self.channels,
            self.registration,
            self.betting,
        ):
            raise OneHeadException("Unable to find cog(s)")

    async def _setup_teams(self, ctx: commands.Context):

        status = self.bot.get_command("status")
        await commands.Command.invoke(status, ctx)
        await self.channels.create_discord_channels(ctx)
        self.channels.set_teams(self.radiant, self.dire)
        await self.channels.move_discord_channels(ctx)
        await ctx.send("Setup Lobby in Dota 2 Client and join with the above teams.")

    @commands.has_role("IHL Admin")
    @commands.command()
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    async def start(self, ctx: commands.Context):
        """
        Starts an IHL game.
        """

        if self.game_in_progress:
            await ctx.send("Game already in progress...")
            return

        signup_threshold_met = await self.pre_game.signup_check(ctx)
        if signup_threshold_met is False:
            return

        await self.pre_game.handle_signups(ctx)

        self.game_in_progress = True
        self.pre_game.disable_signups()

        self.radiant, self.dire = await self.team_balance.balance(ctx)
        await self._setup_teams(ctx)

        await self._open_player_transfer_window(ctx)
        
        # Allow bets!
        await self.betting.open_betting_window(ctx, self.game_cancelled)
        
    @commands.has_role("IHL Admin")
    @commands.command()
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    async def stop(self, ctx: commands.Context):
        """
        Cancels an IHL game.
        """

        if self.game_in_progress:
            self.game_cancelled.set()
            await ctx.send("Game stopped.")
            await self.channels.move_back_to_lobby(ctx)
            await self._refund_player_transactions(ctx)
            await self.betting.refund_all_bets(ctx)
            self._reset_state()
        else:
            await ctx.send("No currently active game.")

    @commands.has_role("IHL Admin")
    @commands.command()
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    async def result(self, ctx: commands.Context, result: str):
        """
        Provide the result of game that has finished.
        """

        if self.game_in_progress is False:
            await ctx.send("No currently active game.")
            return

        if self.radiant is None or self.dire is None:
            return

        accepted_results = [RADIANT, DIRE]

        if result not in accepted_results:
            await ctx.send(f"Invalid Value - Must be either {RADIANT} or {DIRE}.")
            return

        bet_results = self.betting.get_bet_results(result == RADIANT)

        for name, delta in bet_results.items():
            if delta > 0:
                self.database.update_rbucks(name, delta)

        report = self.betting.create_bet_report(bet_results)
        await ctx.send(embed=report)

        await ctx.send("Updating Scores...")
        radiant_names, dire_names = OneHeadCommon.get_player_names(
            self.radiant, self.dire
        )

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

        if self.game_in_progress and self.radiant and self.dire:
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

        if self.game_in_progress:
            await ctx.send("Cannot reset state while a game is in progress.")
            return

        self._reset_state()

    @commands.command()
    async def matches(self, ctx: commands.Context):
        """
        Display the top 10 most recent matches in the IHL.
        """

        await ctx.send(
            "https://www.dotabuff.com/esports/leagues/13630-igc-inhouse-league"
        )

    @commands.has_role("IHL Admin")
    @commands.command(aliases=["sim"])
    async def simulate_signups(self, ctx: commands.Context):
        self.pre_game.signups = [
            "ERIC",
            "GEE",
            "JEFFERIES",
            "ZEED",
            "PECRO",
            "LAURENCE",
            "THANOS",
            "JAMES",
            "LUKE",
            "EDD",
        ]

    @commands.has_role("IHL")
    @commands.command()
    async def shuffle(self, ctx: commands.Context):
        """
        Shuffles teams (costs 500 RBUCKS)
        """

        if self.player_transfer_window_open is False:
            await ctx.send("Unable to shuffle as player transfer window is closed.")
            return

        name = ctx.author.display_name

        if name not in self.pre_game.signups:
            await ctx.send(f"{name} is unable to shuffle as they did not sign up.")
            return

        profile = self.database.lookup_player(name)
        current_balance = profile["rbucks"]

        cost = 500
        if current_balance < cost:
            await ctx.send(
                f"{name} cannot shuffle as they only have {current_balance} "
                f"RBUCKS. A shuffle costs {cost} RBUCKS"
            )
            return

        await ctx.send(f"{name} has spent **{cost}** RBUCKS to **shuffle** the teams!")

        self.database.update_rbucks(name, -1 * cost)
        self.player_transactions.append({"name": name, "cost": cost})

        while True:
            balanced_teams = await self.team_balance.balance(ctx)
            if balanced_teams != (self.radiant, self.dire):
                self.radiant, self.dire = balanced_teams
                break

        await self._setup_teams(ctx)

    async def _open_player_transfer_window(self, ctx: commands.Context):
        
        self.player_transfer_window_open = True
        await ctx.send(f"Player transfer window is now open for 2 minutes!")
        
        try:
            await asyncio.wait_for(self.game_cancelled.wait(), timeout=120)
        except asyncio.TimeoutError:
            pass

        self.player_transfer_window_open = False
        await ctx.send(f"Player transfer window has now closed!")

    async def _refund_player_transactions(self, ctx: commands.Context):
        if len(self.player_transactions) == 0:
            return

        for transaction in self.player_transactions:
            self.database.update_rbucks(transaction["name"], transaction["cost"])

        await ctx.send("All player transactions have been refunded.")

    def _reset_state(self):
        self.game_in_progress = False
        self.radiant = None
        self.dire = None
        self.player_transactions = []
        self.player_transfer_window_open = False
        self.game_cancelled.clear()

        self.pre_game.reset_state()
        self.betting.reset_state()
