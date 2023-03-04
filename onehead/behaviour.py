from logging import Logger
from typing import TYPE_CHECKING

from discord.ext.commands import Bot, Cog, Context, command, has_role

from onehead.common import (
    BehaviourConstants,
    Player,
    Roles,
    get_bot_instance,
    get_logger,
    get_player_names
)
from onehead.game import Game
from onehead.protocols.database import IPlayerDatabase, Operation

if TYPE_CHECKING:
    from onehead.core import Core


log: Logger = get_logger()


class Behaviour(Cog):
    def __init__(self, database: IPlayerDatabase) -> None:
        self.database: IPlayerDatabase = database

    @has_role(Roles.MEMBER)
    @command()
    async def commend(self, ctx: Context, player_name: str) -> None:
        """
        Commend a player for playing well.
        """

        bot: Bot = get_bot_instance()
        core: Core = bot.get_cog("Core")  # type: ignore[assignment]
        previous_game: Game | None = core.previous_game

        if previous_game is None or previous_game.radiant is None or previous_game.dire is None:
            await ctx.send("Unable to commend as a game is yet to be played.")
            return

        commender: str = ctx.author.display_name
        radiant, dire = get_player_names(previous_game.radiant, previous_game.dire)
        if commender not in radiant and commender not in dire:
            await ctx.send(
                f"{commender} did not participate in the previous game and therefore cannot commend another player."
            )
            return

        if commender == player_name:
            await ctx.send(f"{commender} you cannot commend yourself, nice try...")
            return

        if player_name not in radiant and player_name not in dire:
            await ctx.send(f"{player_name} cannot be commended as they did not participate in the previous game.")
            return

        if previous_game.has_been_previously_commended(commender, player_name):
            await ctx.send(f"{player_name} has already been commended by {commender}.")
            return

        player: Player | None = self.database.get(player_name)
        if player is None:
            await ctx.send(f"{player_name} could not be found in the database.")
            return

        new_score: int = min(player.behaviour + BehaviourConstants.COMMEND.value, BehaviourConstants.MAX_BEHAVIOUR_SCORE.value)

        self.database.modify(player_name, "behaviour", new_score)
        self.database.modify(player_name, "commends", 1, operation=Operation.ADD)

        previous_game.add_commend(commender, player_name)

        await ctx.send(f"{player_name} has been commended.")

    @has_role(Roles.MEMBER)
    @command()
    async def report(self, ctx: Context, player_name: str, *, reason: str) -> None:
        """
        Report a player for intentionally ruining the game experience.
        """

        bot: Bot = get_bot_instance()
        core: Core = bot.get_cog("Core")  # type: ignore[assignment]
        previous_game: Game | None = core.previous_game

        if previous_game is None or previous_game.radiant is None or previous_game.dire is None:
            await ctx.send("Unable to report as a game is yet to be played.")
            return

        reporter: str = ctx.author.display_name
        radiant, dire = get_player_names(previous_game.radiant, previous_game.dire)
        if reporter not in radiant and reporter not in dire:
            await ctx.send(
                f"{reporter} did not participate in the previous game and therefore cannot report another player."
            )
            return

        if reporter == player_name:
            await ctx.send(
                f"{player_name} has brought dishonour upon themselves and has attempted to commit seppuku. OneHead will now allow it... UWU!"
            )
            return

        if player_name not in radiant and player_name not in dire:
            await ctx.send(f"{player_name} cannot be reported as they did not participate in the previous game.")
            return

        if previous_game.has_been_previously_reported(reporter, player_name):
            await ctx.send(f"{player_name} has already been reported by {reporter}.")
            return

        player: Player | None = self.database.get(player_name)
        if player is None:
            await ctx.send(f"{player_name} could not be found in the database.")
            return

        new_score: int = max(player.behaviour + BehaviourConstants.REPORT.value, BehaviourConstants.MIN_BEHAVIOUR_SCORE.value)

        self.database.modify(player_name, "behaviour", new_score)
        self.database.modify(player_name, "reports", 1, Operation.ADD)

        previous_game.add_report(reporter, player_name)

        log.info(f"{ctx.author.display_name} reported {player_name} for {reason}")

        await ctx.send(f"{player_name} has been reported.")
