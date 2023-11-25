from logging import Logger
from typing import TYPE_CHECKING, Literal

from discord.ext.commands import Bot, Cog, Context, command, has_role
from structlog import get_logger

from onehead.common import (
    OneHeadException,
    Player,
    PlayerTransfer,
    Roles,
    Team,
    get_bot_instance,
    get_player_names,
)
from onehead.game import Game
from onehead.lobby import Lobby
from onehead.protocols.database import IPlayerDatabase, Operation


if TYPE_CHECKING:
    from onehead.core import Core
    from onehead.matchmaking import Matchmaking


log: Logger = get_logger()


class Transfers(Cog):
    SHUFFLE_COST: Literal[500] = 500

    def __init__(self, database: IPlayerDatabase, lobby: Lobby) -> None:
        self.database: IPlayerDatabase = database
        self.lobby: Lobby = lobby

    async def refund_transfers(self, ctx: Context) -> None:
        bot: Bot = get_bot_instance()
        core: Core = bot.get_cog("Core")  # type: ignore[assignment]
        current_game: Game = core.current_game

        transfers: list[PlayerTransfer] = current_game.get_player_transfers()

        if len(transfers) == 0:
            return

        for transfer in transfers:
            self.database.modify(
                transfer.buyer, "rbucks", transfer.amount, Operation.ADD
            )

        message: str = "All player transactions have been refunded."
        log.info(message)
        await ctx.send(message)

    @has_role(Roles.MEMBER)
    @command()
    async def shuffle(self, ctx: Context) -> None:
        """
        Shuffles teams (costs 500 RBUCKS)
        """

        bot: Bot = get_bot_instance()
        core: Core = bot.get_cog("Core")  # type: ignore[assignment]
        current_game: Game = core.current_game

        transfers: list[PlayerTransfer] = current_game.get_player_transfers()

        if current_game.transfer_window_open() is False:
            await ctx.send("Unable to shuffle as player transfer window is closed.")
            return

        if current_game.radiant is None or current_game.dire is None:
            raise OneHeadException(
                f"Expected valid teams: {current_game.radiant}, {current_game.dire}"
            )

        name: str = ctx.author.display_name
        id: int = ctx.author.id

        if name not in self.lobby.get_signups():
            await ctx.send(
                f"<@{id}> is unable to shuffle are not participating in the current game."
            )
            return

        profile: Player | None = self.database.get(name)
        if profile is None:
            await ctx.send(f"Unable to find <@{id}> in database.")
            return

        current_balance: int = profile["rbucks"]

        if current_balance < self.SHUFFLE_COST:
            await ctx.send(
                f"<@{id}> cannot shuffle as they only have {current_balance} "
                f"RBUCKS. A shuffle costs {Transfers.SHUFFLE_COST} RBUCKS"
            )
            return

        await ctx.send(
            f"@<{id}> has spent **{Transfers.SHUFFLE_COST}** RBUCKS to **shuffle** the teams!"
        )

        self.database.modify(name, "rbucks", Transfers.SHUFFLE_COST, Operation.SUBTRACT)
        transfers.append(PlayerTransfer(name, Transfers.SHUFFLE_COST))

        current_teams_names_only: tuple[
            tuple[str, ...], tuple[str, ...]
        ] = get_player_names(current_game.radiant, current_game.dire)

        matchmaking: Matchmaking = bot.get_cog("Matchmaking")  # type: ignore[assignment]

        shuffled_teams: tuple[Team, Team] = await matchmaking.balance(ctx)

        shuffled_teams_names_only: tuple[
            tuple[str, ...], tuple[str, ...]
        ] = get_player_names(shuffled_teams[0], shuffled_teams[1])

        while current_teams_names_only == shuffled_teams_names_only:
            shuffled_teams = await matchmaking.balance(ctx)
            shuffled_teams_names_only = get_player_names(
                shuffled_teams[0], shuffled_teams[1]
            )

        log.info(
            f"@<{id}> has shuffled the teams. New teams are: {shuffled_teams_names_only}"
        )
        current_game.radiant, current_game.dire = shuffled_teams

        await core.setup_teams(ctx)
