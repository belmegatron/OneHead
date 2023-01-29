from logging import Logger

from discord.ext.commands import Bot, Cog, Context, command, has_role

from onehead.common import (OneHeadException, Player, Roles, get_bot_instance,
                            get_logger, get_player_names)
from onehead.database import Database
from onehead.game import Game

log: Logger = get_logger()


class Behaviour(Cog):
    
    MAX_BEHAVIOUR_SCORE = 10000
    MIN_BEHAVIOUR_SCORE = 0
    COMMEND_MODIFIER = 100
    REPORT_MODIFIER = -200
    
    def __init__(self, database: Database) -> None:

        self.database: Database = database
    
    @has_role(Roles.MEMBER)
    @command()
    async def commend(self, ctx: Context, player_name: str) -> None:
        """
        Commend a player for playing well.
        """
        
        bot: Bot = get_bot_instance()
        core: Cog = bot.get_cog("Core")
        previous_game: Game = core.previous_game
        
        if previous_game is None or previous_game.radiant is None or previous_game.dire is None:
            await ctx.send("Unable to commend as a game is yet to be played.")
            return        
        
        commender: str = ctx.author.display_name
        radiant, dire = get_player_names(previous_game.radiant, previous_game.dire)
        if commender not in radiant and commender not in dire:
            await ctx.send(f"{commender} is unable to commend as they did not participate in the previous game.")
            return
        
        if player_name not in radiant and player_name not in dire:
            await ctx.send(f"{player_name} cannot be commended as they did not participate in the previous game")
            return
        
        if previous_game.has_been_previously_commended(commender, player_name):
            await ctx.send(f"{commender} has already commended by {player_name} and therefore cannot be commended again.")
            return
        
        player: Player = self.database.lookup_player(player_name)
        current_behaviour_score: int = player["behaviour"]
        
        new_score: int = min(current_behaviour_score + self.COMMEND_MODIFIER, self.MAX_BEHAVIOUR_SCORE)
        
        self.database.modify_behaviour_score(player_name, new_score, True)
            
        previous_game.add_commend(commender, player_name)

        await ctx.send(f"{player_name} has been commended.")
        
    @has_role(Roles.MEMBER)
    @command()
    async def report(self, ctx: Context, player_name: str, *, reason: str) -> None:
        """
        Report a player for intentionally ruining the game experience.
        """
        
        bot: Bot = get_bot_instance()
        core: Cog = bot.get_cog("Core")
        previous_game: Game = core.previous_game
        
        if previous_game is None or previous_game.radiant is None or previous_game.dire is None:
            await ctx.send("Unable to report as a game is yet to be played.")
            return       

        reporter: str = ctx.author.display_name
        radiant, dire = get_player_names(previous_game.radiant, previous_game.dire)
        if reporter not in radiant and reporter not in dire:
            await ctx.send(f"{reporter} is unable to report as they did not participate in the previous game.")
            return
        
        if player_name not in radiant and player_name not in dire:
            await ctx.send(f"{player_name} cannot be reported as they did not participate in the previous game")
            return
        
        if previous_game.has_been_previously_reported(reporter, player_name):
            await ctx.send(f"{reporter} has already reported by {player_name} and therefore cannot be reported again.")
            return
        
        player: Player = self.database.lookup_player(player_name)
        current_behaviour_score: int = player["behaviour"]
        
        new_score: int = max(current_behaviour_score + self.REPORT_MODIFIER, self.MIN_BEHAVIOUR_SCORE)

        self.database.modify_behaviour_score(player_name, new_score, False)
        
        previous_game.add_report(reporter, player_name)

        log.info(f"{ctx.author.display_name} reported {player_name} for {reason}")
        
        await ctx.send(f"{player_name} has been reported.")