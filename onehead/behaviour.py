from logging import Logger
from typing import TYPE_CHECKING

from discord.ext.commands import Bot, Cog, Context, command, has_role
from structlog import get_logger

from onehead.common import (
    Player,
    Roles,
    get_bot_instance,
    get_player_names,
    get_discord_id_from_name,
)
from onehead.game import Game
from onehead.protocols.database import OneHeadDatabase, Operation

if TYPE_CHECKING:
    from onehead.core import Core


log: Logger = get_logger()


class Behaviour(Cog):
    MAX_BEHAVIOUR_SCORE = 10000
    MIN_BEHAVIOUR_SCORE = 0
    COMMEND_MODIFIER = 100
    REPORT_MODIFIER = -200

    def __init__(self, database: OneHeadDatabase) -> None:
        self.database: OneHeadDatabase = database

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
        commender_id: int = ctx.author.id

        radiant: tuple[str, ...]
        dire: tuple[str, ...]
        radiant, dire = get_player_names(previous_game.radiant, previous_game.dire)

        if commender not in radiant and commender not in dire:
            await ctx.send(
                f"<@{commender_id}> did not participate in the previous game and therefore cannot commend another player."
            )
            return

        if commender == player_name:
            await ctx.send(f"<@{commender_id}> you cannot commend yourself, nice try...")
            return

        player_id: int = get_discord_id_from_name(ctx, player_name)
        if player_name not in radiant and player_name not in dire:
            await ctx.send(f"<@{player_id}> cannot be commended as they did not participate in the previous game.")
            return

        if previous_game.has_been_previously_commended(commender, player_name):
            await ctx.send(f"<@{player_id}> has already been commended by <@{commender_id}>.")
            return

        player: Player | None = self.database.get(player_name)
        if player is None:
            await ctx.send(f"<@{player_id}> could not be found in the database.")
            return

        current_behaviour_score: int = player["behaviour"]

        new_score: int = min(current_behaviour_score + self.COMMEND_MODIFIER, self.MAX_BEHAVIOUR_SCORE)

        self.database.modify(player_name, "behaviour", new_score)
        self.database.modify(player_name, "commends", 1, operation=Operation.ADD)

        previous_game.add_commend(commender, player_name)

        log.info(f"{commender} commended {player_name}.")

        await ctx.send(f"<@{player_id}> has been commended by <@{commender_id}>.")

    @has_role(Roles.MEMBER)
    @command()
    async def report(self, ctx: Context, player_name: str, reason: str) -> None:
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
        reporter_id: int = ctx.author.id

        radiant: tuple[str, ...]
        dire: tuple[str, ...]
        radiant, dire = get_player_names(previous_game.radiant, previous_game.dire)

        if reporter not in radiant and reporter not in dire:
            await ctx.send(
                f"<@{reporter_id}> did not participate in the previous game and therefore cannot report another player."
            )
            return

        if reporter == player_name:
            await ctx.send(
                f"<@{reporter_id}> has brought dishonour upon themselves and has attempted to commit seppuku. OneHead will now allow it... UWU!"
            )
            return

        player_id: int = get_discord_id_from_name(player_name)
        if player_name not in radiant and player_name not in dire:
            await ctx.send(f"<@{player_id}> cannot be reported as they did not participate in the previous game.")
            return

        if previous_game.has_been_previously_reported(reporter, player_name):
            await ctx.send(f"<@{player_id}> has already been reported by <@{reporter_id}>.")
            return

        player: Player | None = self.database.get(player_name)
        if player is None:
            await ctx.send(f"<@{player_id}> could not be found in the database.")
            return

        current_behaviour_score: int = player["behaviour"]

        new_score: int = max(current_behaviour_score + self.REPORT_MODIFIER, self.MIN_BEHAVIOUR_SCORE)

        self.database.modify(player_name, "behaviour", new_score)
        self.database.modify(player_name, "reports", 1, Operation.ADD)

        previous_game.add_report(reporter, player_name)

        log.info(f"{reporter} reported {player_name} for the following reason: {reason}.")

        await ctx.send(f"<@{player_id}> has been reported.")
