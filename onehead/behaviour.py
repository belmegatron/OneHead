from logging import Logger
from typing import TYPE_CHECKING

from discord.member import Member
from discord.ext.commands import Bot, Cog, Context, command, has_role
from structlog import get_logger

from onehead.common import (
    Player,
    Roles,
    get_bot_instance,
    get_player_names,
    get_discord_member_from_name,
    get_discord_member_from_id,
    OneHeadException
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
        
    def is_mention(self, s: str) -> bool:
        return s[:2] == "<@" and len(s) > 3
    
    def get_discord_id_from_mention(self, mention: str) -> int:
        try:
            player_id: int = int(mention[2:-1])
        except ValueError:
            raise OneHeadException(f"Failed to extract discord id from mention: {mention}")
        
        return player_id
        
    @has_role(Roles.MEMBER)
    @command()
    async def commend(self, ctx: Context, target: str) -> None:
        """
        Commend a player for playing well.
        """

        bot: Bot = get_bot_instance()
        core: Core = bot.get_cog("Core")  # type: ignore[assignment]
        previous_game: Game | None = core.previous_game

        if previous_game is None or previous_game.radiant is None or previous_game.dire is None:
            await ctx.send("Unable to commend as a game is yet to be played.")
            return

        commender: Member = ctx.author

        radiant: tuple[str, ...]
        dire: tuple[str, ...]
        radiant, dire = get_player_names(previous_game.radiant, previous_game.dire)

        if commender.display_name not in radiant and commender.display_name not in dire:
            await ctx.send(
                f"{commender.mention} did not participate in the previous game and therefore cannot commend another player."
            )
            return

        commendee: Member
        
        if self.is_mention(target):
            commendee_id: int = self.get_discord_id_from_mention(target)
            commendee = get_discord_member_from_id(ctx, commendee_id)
        else:
            commendee = get_discord_member_from_name(ctx, target)
        
        if commender.id == commendee.id:
            await ctx.send(f"{commender.mention} you cannot commend yourself, nice try...")
            return

        if commendee.display_name not in radiant and commendee.display_name not in dire:
            await ctx.send(f"{commendee.mention} cannot be commended as they did not participate in the previous game.")
            return

        if previous_game.has_been_previously_commended(commender.display_name, commendee.display_name):
            await ctx.send(f"{commendee.mention} has already been commended by {commender.mention}.")
            return

        commendee_record: Player | None = self.database.get(commendee.id)
        if commendee_record is None:
            await ctx.send(f"{commendee.mention} could not be found in the database.")
            return

        current_behaviour_score: int = commendee_record["behaviour"]

        new_score: int = min(current_behaviour_score + self.COMMEND_MODIFIER, self.MAX_BEHAVIOUR_SCORE)

        self.database.modify(commendee.id, "behaviour", new_score)
        self.database.modify(commendee.id, "commends", 1, operation=Operation.ADD)

        previous_game.add_commend(commender.display_name, commendee.display_name)

        log.info(f"{commender.display_name} commended {commendee.display_name}.")

        await ctx.send(f"{commendee.mention} has been commended by {commender.mention}.")

    @has_role(Roles.MEMBER)
    @command()
    async def report(self, ctx: Context, target: str, reason: str) -> None:
        """
        Report a player for intentionally ruining the game experience.
        """

        bot: Bot = get_bot_instance()
        core: Core = bot.get_cog("Core")  # type: ignore[assignment]
        previous_game: Game | None = core.previous_game

        if previous_game is None or previous_game.radiant is None or previous_game.dire is None:
            await ctx.send("Unable to report as a game is yet to be played.")
            return

        reporter: Member = ctx.author

        radiant: tuple[str, ...]
        dire: tuple[str, ...]
        radiant, dire = get_player_names(previous_game.radiant, previous_game.dire)

        if reporter.display_name not in radiant and reporter.display_name not in dire:
            await ctx.send(
                f"{reporter.mention} did not participate in the previous game and therefore cannot report another player."
            )
            return
        
        reported: Member
        
        if self.is_mention(target):
            reported_id: int = self.get_discord_id_from_mention(target)
            reported = get_discord_member_from_id(ctx, reported_id)
        else:
            reported = get_discord_member_from_name(ctx, target)

        if reporter.id == reported.id:
            await ctx.send(
                f"{reporter.mention} has brought dishonour upon themselves and has attempted to commit seppuku. OneHead will now allow it... UWU!"
            )
            return

        if reported.display_name not in radiant and reported.display_name not in dire:
            await ctx.send(f"{reported.mention} cannot be reported as they did not participate in the previous game.")
            return

        if previous_game.has_been_previously_reported(reporter.display_name, reported.display_name):
            await ctx.send(f"{reported.mention} has already been reported by {reporter.mention}.")
            return

        reported_record: Player | None = self.database.get(reported.id)
        if reported_record is None:
            await ctx.send(f"{reported.mention} could not be found in the database.")
            return

        current_behaviour_score: int = reported_record["behaviour"]

        new_score: int = max(current_behaviour_score + self.REPORT_MODIFIER, self.MIN_BEHAVIOUR_SCORE)

        self.database.modify(reported.id, "behaviour", new_score)
        self.database.modify(reported.id, "reports", 1, Operation.ADD)

        previous_game.add_report(reporter.display_name, reported.display_name)

        log.info(f"{reporter.display_name} reported {reported.display_name} for the following reason: {reason}.")

        await ctx.send(f"{reported.mention} has been reported.")
