import asyncio
from typing import TYPE_CHECKING, Literal

from discord import Embed, Intents
from discord.ext.commands import (Bot, BucketType, Cog, Command, Context,
                                  command, has_role, max_concurrency)
from tabulate import tabulate

import onehead.common
from onehead.balance import OneHeadBalance
from onehead.betting import OneHeadBetting
from onehead.channels import OneHeadChannels
from onehead.common import (DIRE, RADIANT, OneHeadCommon, OneHeadException,
                            OneHeadRoles, log)
from onehead.db import OneHeadDB
from onehead.mental_health import OneHeadMentalHealth
from onehead.scoreboard import OneHeadScoreBoard
from onehead.user import (OneHeadPreGame, OneHeadRegistration,
                          on_member_update, on_voice_state_update)
from version import __changelog__, __version__

if TYPE_CHECKING:
    from onehead.common import Player, Team


def bot_factory() -> Bot:
    """
    Factory method for generating an instance of our Bot.

    :return: OneHead Bot
    """

    intents: Intents = Intents.all()
    intents.members = True
    intents.presences = True
    bot: Bot = Bot(command_prefix="!", intents=intents)

    config: dict = OneHeadCommon.load_config()

    database: OneHeadDB = OneHeadDB(config)
    scoreboard: OneHeadScoreBoard = OneHeadScoreBoard(database)
    pre_game: OneHeadPreGame = OneHeadPreGame(database)
    team_balance: OneHeadBalance = OneHeadBalance(database, pre_game)
    channels: OneHeadChannels = OneHeadChannels(config)
    registration: OneHeadRegistration = OneHeadRegistration(database)
    mental_health: OneHeadMentalHealth = OneHeadMentalHealth()
    betting: OneHeadBetting = OneHeadBetting(database, pre_game)

    bot.add_cog(database)
    bot.add_cog(pre_game)
    bot.add_cog(scoreboard)
    bot.add_cog(registration)
    bot.add_cog(team_balance)
    bot.add_cog(channels)
    bot.add_cog(mental_health)
    bot.add_cog(betting)

    # Add cogs first, then instantiate OneHeadCore as we reference them as instance variables
    token: str = config["discord"]["token"]
    core: OneHeadCore = OneHeadCore(bot, token)
    bot.add_cog(core)

    # Register events
    bot.event(on_voice_state_update)
    bot.event(on_member_update)

    # Make the bot instance globally accessible for callbacks.
    onehead.common.bot = bot

    return bot


class OneHeadCore(Cog):
    def __init__(self, bot: Bot, token: str) -> None:
        self.game_in_progress: bool = False
        self.player_transfer_window_open: bool = False
        self.radiant: Team | None = None
        self.dire: Team | None = None
        self.game_cancelled: asyncio.Event = asyncio.Event()

        self.player_transactions: list[dict] = []

        self.bot: Bot = bot
        self.token: str = token

        self.config: dict = OneHeadCommon.load_config()
        self.database: OneHeadDB = bot.get_cog("OneHeadDB")
        self.scoreboard: OneHeadScoreBoard = bot.get_cog("OneHeadScoreBoard")
        self.pre_game: OneHeadPreGame = bot.get_cog("OneHeadPreGame")
        self.team_balance: OneHeadBalance = bot.get_cog("OneHeadBalance")
        self.channels: OneHeadChannels = bot.get_cog("OneHeadChannels")
        self.registration: OneHeadRegistration = bot.get_cog("OneHeadRegistration")
        self.betting: OneHeadBetting = bot.get_cog("OneHeadBetting")

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

    async def _setup_teams(self, ctx: Context) -> None:

        if self.radiant is None or self.dire is None:
            return

        status: Command = self.bot.get_command("status")
        await Command.invoke(status, ctx)
        await self.channels.create_discord_channels(ctx)
        self.channels.set_teams(self.radiant, self.dire)
        await self.channels.move_discord_channels(ctx)
        await ctx.send("Setup Lobby in Dota 2 Client and join with the above teams.")

    def _reset_state(self) -> None:

        self.radiant = None
        self.dire = None
        self.game_cancelled.clear()
        self.game_in_progress = False
        self.player_transfer_window_open = False

        self.bot.remove_cog("OneHeadPreGame")
        self.pre_game = OneHeadPreGame(self.database)
        self.bot.add_cog(self.pre_game)

        self.bot.remove_cog("OneHeadBalance")
        self.team_balance = OneHeadBalance(self.database, self.pre_game)
        self.bot.add_cog(self.team_balance)

        self.bot.remove_cog("OneHeadChannels")
        self.channels = OneHeadChannels(self.config)
        self.bot.add_cog(self.channels)

        self.bot.remove_cog("OneHeadBetting")
        self.betting = OneHeadBetting(self.database, self.pre_game)
        self.bot.add_cog(self.betting)

    @has_role(OneHeadRoles.ADMIN)
    @command()
    @max_concurrency(1, per=BucketType.default, wait=False)
    async def start(self, ctx: Context) -> None:
        """
        Starts an IHL game.
        """

        if self.game_in_progress:
            await ctx.send("Game already in progress...")
            return

        signup_threshold_met: bool = await self.pre_game.signup_check(ctx)
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

    @has_role(OneHeadRoles.ADMIN)
    @command()
    @max_concurrency(1, per=BucketType.default, wait=False)
    async def stop(self, ctx: Context) -> None:
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

            log.info("Game has stopped")
        else:
            await ctx.send("No currently active game.")

    @has_role(OneHeadRoles.ADMIN)
    @command()
    @max_concurrency(1, per=BucketType.default, wait=False)
    async def result(self, ctx: Context, result: str) -> None:
        """
        Provide the result of game that has finished.
        """

        if self.game_in_progress is False:
            await ctx.send("No currently active game.")
            return

        if self.radiant is None or self.dire is None:
            return

        accepted_results: list[str] = [RADIANT, DIRE]

        if result not in accepted_results:
            await ctx.send(f"Invalid Value - Must be either {RADIANT} or {DIRE}.")
            return

        bet_results: dict = self.betting.get_bet_results(result == RADIANT)

        for name, delta in bet_results.items():
            if delta > 0:
                self.database.update_rbucks(name, delta)

        report: Embed = self.betting.create_bet_report(bet_results)
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

        scoreboard: Command = self.bot.get_command("scoreboard")
        await Command.invoke(scoreboard, ctx)
        await self.channels.move_back_to_lobby(ctx)

        self._reset_state()

    @has_role(OneHeadRoles.MEMBER)
    @command()
    async def status(self, ctx: Context) -> None:
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

    @has_role(OneHeadRoles.MEMBER)
    @command()
    async def version(self, ctx: Context) -> None:
        """
        Displays the current version of OneHead.
        """

        await ctx.send(f"**Current Version** - {__version__}")
        await ctx.send(f"**Changelog** - {__changelog__}")

    @has_role(OneHeadRoles.ADMIN)
    @command()
    @max_concurrency(1, per=BucketType.default, wait=False)
    async def reset(self, ctx: Context) -> None:
        """
        Resets the current bot state.
        """

        if self.game_in_progress:
            await ctx.send("Cannot reset state while a game is in progress.")
            return

        self._reset_state()

    @command()
    async def matches(self, ctx: Context) -> None:
        """
        Display the top 10 most recent matches in the IHL.
        """

        await ctx.send(
            "https://www.dotabuff.com/esports/leagues/13630-igc-inhouse-league"
        )

    @has_role(OneHeadRoles.MEMBER)
    @command()
    async def shuffle(self, ctx: Context) -> None:
        """
        Shuffles teams (costs 500 RBUCKS)
        """

        if self.player_transfer_window_open is False:
            await ctx.send("Unable to shuffle as player transfer window is closed.")
            return

        name: str = ctx.author.display_name

        if name not in self.pre_game.signups:
            await ctx.send(f"{name} is unable to shuffle as they did not sign up.")
            return

        profile: Player = self.database.lookup_player(name)
        current_balance: int = profile["rbucks"]

        cost: Literal[500] = 500
        if current_balance < cost:
            await ctx.send(
                f"{name} cannot shuffle as they only have {current_balance} "
                f"RBUCKS. A shuffle costs {cost} RBUCKS"
            )
            return

        await ctx.send(f"{name} has spent **{cost}** RBUCKS to **shuffle** the teams!")

        self.database.update_rbucks(name, -1 * cost)
        self.player_transactions.append({"name": name, "cost": cost})
        
        if (self.radiant is None or self.dire is None):
            raise OneHeadException("Attempted to shuffle with invalid teams.")

        current_teams_names_only: tuple[
            tuple[str, ...], tuple[str, ...]
        ] = OneHeadCommon.get_player_names(self.radiant, self.dire)
        
        shuffled_teams: tuple[Team, Team] = await self.team_balance.balance(ctx)
        
        shuffled_teams_names_only: tuple[
            tuple[str, ...], tuple[str, ...]
        ] = OneHeadCommon.get_player_names(shuffled_teams[0], shuffled_teams[1])

        while current_teams_names_only == shuffled_teams_names_only:
            shuffled_teams = await self.team_balance.balance(ctx)
            shuffled_teams_names_only = OneHeadCommon.get_player_names(
                shuffled_teams[0], shuffled_teams[1]
            )

        self.radiant, self.dire = shuffled_teams

        await self._setup_teams(ctx)

    async def _open_player_transfer_window(self, ctx: Context) -> None:

        self.player_transfer_window_open = True
        await ctx.send(f"Player transfer window is now open for 2 minutes!")

        try:
            await asyncio.wait_for(self.game_cancelled.wait(), timeout=120)
        except asyncio.TimeoutError:
            pass

        self.player_transfer_window_open = False
        await ctx.send(f"Player transfer window has now closed!")

    async def _refund_player_transactions(self, ctx: Context) -> None:
        if len(self.player_transactions) == 0:
            return

        for transaction in self.player_transactions:
            self.database.update_rbucks(transaction["name"], transaction["cost"])

        await ctx.send("All player transactions have been refunded.")

    @has_role(OneHeadRoles.ADMIN)
    @command(aliases=["sim"])
    async def simulate_signups(self, ctx: Context) -> None:
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
            "RBEEZAY",
        ]
