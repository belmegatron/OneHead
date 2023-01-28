from discord.ext.commands import (Cog, command, has_role, Context)
from onehead.common import (OneHeadException, Roles)
from onehead.database import Database


class Registration(Cog):
    
    MIN_MMR: int = 1000
    
    def __init__(self, database: Database) -> None:

        self.database: Database = database

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
            await ctx.send(
                f"{mmr_int} MMR is too low, must be greater or equal to {self.MIN_MMR}."
            )
            return

        exists, _ = self.database.player_exists(name)
        if exists is False:
            self.database.add_player(ctx.author.display_name, mmr_int)
            await ctx.send(f"{name} successfully registered.")
        else:
            await ctx.send(f"{name} is already registered.")

    @has_role(Roles.ADMIN)
    @command(aliases=["dereg"])
    async def deregister(self, ctx: Context, name: str) -> None:
        """
        Removes a player from the internal IHL database.
        """

        exists, _ = self.database.player_exists(name)
        if exists:
            self.database.remove_player(name)
            await ctx.send(f"{name} successfully removed from the database.")
        else:
            await ctx.send(f"{name} could not be found in the database.")

