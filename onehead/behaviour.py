from logging import Logger

from discord import Embed, colour
from discord.ext.commands import (BucketType, Cog, Command, Context, command,
                                  cooldown, has_role)

from onehead.common import DIRE, RADIANT, OneHeadException, Roles, get_logger
from onehead.database import Database

log: Logger = get_logger()


class Behaviour(Cog):
    
    def __init__(self, database: Database) -> None:

        self.database: Database = database
    
    @has_role(Roles.MEMBER)
    @command()
    async def commend(self, ctx: Context, player: str) -> None:
        """
        Commend a player for playing well.
        """
        
        player_exists, _ = self.database.player_exists(player)
        if player_exists is False:
            await ctx.send(f"{player} does not exist.")

        await ctx.send(f"{player} has been commended.")
        
    @has_role(Roles.MEMBER)
    @command()
    async def report(self, ctx: Context, player: str, *, reason: str) -> None:
        """
        Report a player for intentionally ruining the game experience.
        """

        log.info(f"{ctx.author.display_name} reported {player} for {reason}")
        
        await ctx.send(f"{player} has been reported.")