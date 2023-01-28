from typing import TYPE_CHECKING, Literal

from discord.ext.commands import (Cog, command, has_role, Context)

from onehead.common import (OneHeadException, Roles, get_player_names)

if TYPE_CHECKING:
    from common import Player, Team
    from onehead.database import Database


class Transfers(Cog):
    
    def __init__(self, database: Database) -> None:
        self.database: Database = database
    
    async def refund_transactions(self, ctx: Context) -> None:
        if len(self.player_transactions) == 0:
            return

        for transaction in self.player_transactions:
            self.database.update_rbucks(transaction["name"], transaction["cost"])

        await ctx.send("All player transactions have been refunded.")
        
    @has_role(Roles.MEMBER)
    @command()
    async def shuffle(self, ctx: Context) -> None:
        """
        Shuffles teams (costs 500 RBUCKS)
        """

        if self.current_game.transfer_window_open() is False:
            await ctx.send("Unable to shuffle as player transfer window is closed.")
            return

        name: str = ctx.author.display_name

        if name not in self.lobby.signups:
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
        
        if self.current_game.radiant is None or self.current_game.dire is None:
            raise OneHeadException(f"Expected valid teams: {self.current_game.radiant}, {self.current_game.dire}")

        current_teams_names_only: tuple[
            tuple[str, ...], tuple[str, ...]
        ] = get_player_names(self.current_game.radiant, self.current_game.dire)
        
        shuffled_teams: tuple[Team, Team] = await self.matchmaking.balance(ctx)
        
        shuffled_teams_names_only: tuple[
            tuple[str, ...], tuple[str, ...]
        ] = get_player_names(shuffled_teams[0], shuffled_teams[1])

        while current_teams_names_only == shuffled_teams_names_only:
            shuffled_teams = await self.matchmaking.balance(ctx)
            shuffled_teams_names_only = get_player_names(
                shuffled_teams[0], shuffled_teams[1]
            )

        self.radiant, self.dire = shuffled_teams

        await self._setup_teams(ctx)