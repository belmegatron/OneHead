from typing import Literal

from discord.ext.commands import Bot, Cog, Context, command, has_role

from onehead.common import (
    OneHeadException,
    Player,
    PlayerTransfer,
    Roles,
    Team,
    get_bot_instance,
    get_player_names,
)
from onehead.database import Database
from onehead.game import Game
from onehead.lobby import Lobby


class Transfers(Cog):
    def __init__(self, database: Database, lobby: Lobby) -> None:
        self.database: Database = database
        self.lobby: Lobby = lobby

    async def refund_transfers(self, ctx: Context) -> None:

        bot: Bot = get_bot_instance()
        core: Cog = bot.get_cog("Core")
        current_game: Game = core.current_game

        transfers: list[PlayerTransfer] = current_game.get_player_transfers()

        if len(transfers) == 0:
            return

        for transfer in transfers:
            self.database.update_rbucks(transfer.buyer, transfer.amount)

        await ctx.send("All player transactions have been refunded.")

    @has_role(Roles.MEMBER)
    @command()
    async def shuffle(self, ctx: Context) -> None:
        """
        Shuffles teams (costs 500 RBUCKS)
        """

        bot: Bot = get_bot_instance()
        core: Cog = bot.get_cog("Core")
        current_game: Game = core.current_game

        transfers: list[PlayerTransfer] = current_game.get_player_transfers()

        if current_game.transfer_window_open() is False:
            await ctx.send("Unable to shuffle as player transfer window is closed.")
            return

        name: str = ctx.author.display_name

        if name not in self.lobby.get_signups():
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
        transfers.append(PlayerTransfer(name, cost))

        if current_game.radiant is None or current_game.dire is None:
            raise OneHeadException(
                f"Expected valid teams: {current_game.radiant}, {current_game.dire}"
            )

        current_teams_names_only: tuple[
            tuple[str, ...], tuple[str, ...]
        ] = get_player_names(current_game.radiant, current_game.dire)

        matchmaking: Cog = bot.get_cog("Matchmaking")

        shuffled_teams: tuple[Team, Team] = await matchmaking.balance(ctx)

        shuffled_teams_names_only: tuple[
            tuple[str, ...], tuple[str, ...]
        ] = get_player_names(shuffled_teams[0], shuffled_teams[1])

        while current_teams_names_only == shuffled_teams_names_only:
            shuffled_teams = await matchmaking.balance(ctx)
            shuffled_teams_names_only = get_player_names(
                shuffled_teams[0], shuffled_teams[1]
            )

        current_game.radiant, current_game.dire = shuffled_teams

        await core.setup_teams(ctx)
