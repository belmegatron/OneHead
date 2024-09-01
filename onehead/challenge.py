from asyncio import create_task, sleep
from datetime import datetime, timedelta, UTC
import itertools
from logging import Logger
from structlog import get_logger
from typing import Any

from discord.member import Member
from discord.user import User
from discord.ext.commands import Cog, Context, command, has_role
from pytz import timezone
from tabulate import tabulate

from onehead.common import (
    Player,
    Roles,
    get_discord_member_from_name,
    play_sound,
    get_discord_member_from_id
)
from onehead.game import Challenge
from onehead.protocols.database import OneHeadDatabase


log: Logger = get_logger()


class ChallengeMode(Cog):

    MAX_RATING_DIFFERENCE: int = 2000
    MAX_CHALLENGES_ISSUED: int = 1
    MAX_CHALLENGED_RECEIVED: int = 1

    counter = itertools.count()

    def __init__(self, database: OneHeadDatabase) -> None:
        self.database: OneHeadDatabase = database
        self.challenges: list[Challenge] = []
        self._active: bool = False

    @has_role(Roles.MEMBER)
    @command()
    async def challenge(self, ctx: Context, opponent_name: str) -> None:
        """
        Challenge an opponent to a 1v1 mid duel e.g. `!challenge ERIC`        
        """
        challenger: Member | User = ctx.author

        opponent: Member | None = get_discord_member_from_name(ctx, opponent_name)

        if opponent is None:
            return
        
        if challenger == opponent:
            await ctx.send("You cannot challenge yourself...")
            return

        for challenge in self.challenges:
            if challenge.challenger.id == challenger.id:
                opponent = get_discord_member_from_id(ctx, challenge.opponent.id)
                if opponent:
                    await ctx.send(f"{challenger.mention} has already issued a challenge to {opponent.mention}!\n Stop sending for man, kmt.")
                return
            elif challenge.opponent.id == opponent.id:
                other_challenger: Member | None = get_discord_member_from_id(ctx, challenge.challenger.id)
                if other_challenger:
                    await ctx.send(f"{opponent.mention} has already been challenged by {other_challenger.mention}!")
                return

        challenger_record: Player | None = self.database.get(challenger.id)
        opponent_record: Player | None = self.database.get(opponent.id)

        if challenger_record is None or opponent_record is None:
            raise

        if challenger_record["mmr"] - opponent_record["mmr"] > self.MAX_RATING_DIFFERENCE:
            await play_sound(ctx, "bully.mp3")
            await ctx.send(
                f"{challenger.mention}, your opponent must be within {self.MAX_RATING_DIFFERENCE} MMR of your MMR in order to duel them."
            )
            return

        # TODO: Persist challenges to database.
        await play_sound(ctx, "challenger.mp3")
        challenge: Challenge = Challenge(next(self.counter), challenger=challenger, opponent=opponent)
        self.challenges.append(challenge)

        await ctx.send(f"{challenger.mention} has challenged {opponent.mention} to a 1v1 mid!")
        await ctx.send(
            f"{opponent.mention} has 24 hours to accept this challenge, if they wish to accept, type `!accept` {challenger.mention}."
        )

        create_task(self.handle_expired_challenge(ctx, challenge))
    
    @has_role(Roles.MEMBER)
    @command(aliases=["challenges"])
    async def list_challenges(self, ctx: Context) -> None:
        """
        Lists all active challenges.
        """
        
        challenges: list[dict[str, Any]] = []
        for challenge in self.challenges:
            sorted_challenge: dict[str, Any] = {
                "id": challenge.id,
                "challenger": challenge.challenger.display_name,
                "opponent": challenge.opponent.display_name,
                "in_progress": challenge.in_progress(),
                "expires": challenge.expires.astimezone(timezone("Europe/London")).strftime("%d/%m/%Y, %H:%M:%S"),
            }
            challenges.append(sorted_challenge)

        if len(challenges) == 0:
            await ctx.send("There are no active challenges.")
        else:
            sorted: str = tabulate(challenges, headers="keys", tablefmt="simple")
            await ctx.send(f"**Challenges** ```\n{sorted}```")

    @has_role(Roles.MEMBER)
    @command()
    async def accept(self, ctx: Context, name: str) -> None:
        """
        Accept a duel issued by a challenger e.g. `!accept BOBBY`
        """
        challenge: Challenge | None = self.find_issued_challenge(ctx, name)

        if challenge:
            if challenge.in_progress() is False:
                challenge.start()
            else:
                await ctx.send(f"{challenge.opponent} has already accepted their duel vs. {challenge.challenger}!")
                await ctx.send(f"To start the game, ask an admin to type `!start {challenge.id}`")
        else:
            await ctx.send(f"Unable to find challenge issued to {ctx.author.mention} by {name}.")

    @has_role(Roles.MEMBER)
    @command()
    async def reject(self, ctx: Context, name: str) -> None:
        """
        Reject a duel issued by a challenger e.g. `!reject BOBBY`
        """
        challenge: Challenge | None = self.find_issued_challenge(ctx, name)

        if challenge:
            await ctx.send(
                f"{challenge.opponent.mention} has rejected the challenge issued by {challenge.challenger.mention}."
            )
            await play_sound(ctx, "shame.mp3")
            self.challenges.remove(challenge)
        else:
            await ctx.send(f"Unable to find challenge issued to {ctx.author.mention} by {name}.")

    def find_issued_challenge(self, ctx: Context, challenger_name: str) -> Challenge | None:
        challenged: Member | User = ctx.author

        challenger: Member | None = get_discord_member_from_name(ctx, challenger_name)

        for challenge in self.challenges:
            if challenge.opponent.id == challenged.id and challenge.challenger.id == challenger.id:
                return challenge

        return None      
        
    async def handle_expired_challenge(self, ctx: Context, challenge: Challenge) -> None:
        to_wait: timedelta = challenge.expires - datetime.now(UTC)

        # TODO: Maybe break this up and add reminder messages.
        await sleep(to_wait.total_seconds())

        if challenge.complete is False:
            await ctx.send(
                f"{challenge.opponent.mention} has failed to accept {challenge.challenger.mention}'s request to duel due to it expiring."
            )

        try:
            self.challenges.remove(challenge)
        except ValueError:
            pass
