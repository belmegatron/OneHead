from discord.ext.commands import Cog, Context, command, has_role

from onehead.common import OneHeadException, Player, Roles
from onehead.protocols.database import IPlayerDatabase


class Registration(Cog):
    MIN_MMR: int = 1000
    MAX_MMR: int = 10000

    def __init__(self, database: IPlayerDatabase) -> None:
        self.database: IPlayerDatabase = database

    @has_role(Roles.MEMBER)
    @command(aliases=["reg"])
    async def register(self, ctx: Context, mmr: str) -> None:
        """
        Register yourself to the IHL by typing !register <your mmr>.
        """

        name: str = ctx.author.display_name

        try:
            mmr_int: int = int(mmr)
        except ValueError:
            raise OneHeadException(f"{mmr} is not a valid integer.")

        if mmr_int < self.MIN_MMR:
            await ctx.send(f"{mmr_int} MMR is too low, must be greater or equal to {self.MIN_MMR}.")
            return
        
        if mmr_int > self.MAX_MMR:
            await ctx.send(f"{mmr_int} MMR is too high, must be less than or equal to {self.MAX_MMR}.")
            return

        player: Player | None = self.database.get(name)
        if player is None:
            self.database.add(ctx.author.display_name, mmr_int)
            await ctx.send(f"{name} successfully registered.")
        else:
            await ctx.send(f"{name} is already registered.")

    @has_role(Roles.ADMIN)
    @command(aliases=["dereg"])
    async def deregister(self, ctx: Context, name: str) -> None:
        """
        Removes a player from the internal IHL database.
        """

        player: Player | None = self.database.get(name)
        if player:
            self.database.remove(name)
            await ctx.send(f"{name} has been successfully removed from the database.")
        else:
            await ctx.send(f"{name} could not be found in the database.")
