from logging import Logger

from discord.member import Member
from discord.ext.commands import Cog, Context, command, has_role
from structlog import get_logger

from onehead.common import Player, Roles, get_discord_member_from_name
from onehead.protocols.database import OneHeadDatabase


log: Logger = get_logger()


class Registration(Cog):
    MIN_MMR: int = 1000
    MAX_MMR: int = 10000

    def __init__(self, database: OneHeadDatabase) -> None:
        self.database: OneHeadDatabase = database

    @has_role(Roles.MEMBER)
    @command(aliases=["reg"])
    async def register(self, ctx: Context, mmr: str) -> None:
        """
        Register yourself to the IHL by typing !register <your mmr>.
        """

        try:
            mmr_int: int = int(mmr)
        except ValueError:
            await ctx.send(
                f"{ctx.author.mention}, the command you are looking for is `!register <MMR>` (e.g. `!register 9000`)"
            )
            return

        if mmr_int < self.MIN_MMR:
            await ctx.send(f"`{mmr}` MMR is too low, must be greater or equal to `{self.MIN_MMR}`.")
            return

        if mmr_int > self.MAX_MMR:
            await ctx.send(f"`{mmr}` MMR is too high, must be less than or equal to `{self.MAX_MMR}`.")
            return

        player: Player | None = self.database.get(id)
        if player is None:
            self.database.add(ctx.author.id, ctx.author.display_name, mmr_int)
            log.info(f"{ctx.author.display_name} registered with an MMR of {mmr}.")
            await ctx.send(f"{ctx.author.mention} successfully registered.")
        else:
            await ctx.send(f"{ctx.author.mention} is already registered.")

    @has_role(Roles.ADMIN)
    @command(aliases=["dereg"])
    async def deregister(self, ctx: Context, name: str) -> None:
        """
        Removes a player from the internal IHL database.
        """

        player: Player | None = self.database.get(name)
        member: Member | None = get_discord_member_from_name(ctx, name)

        if player and member:
            self.database.remove(member.id)
            log.info(f"{name} has been deregistered by {ctx.author.display_name}.")
            await ctx.send(f"{member.mention} has been deregistered.")
        else:
            await ctx.send(f"{member.mention} could not be found in the database.")
