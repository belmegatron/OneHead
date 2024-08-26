from asyncio import create_task, sleep
from datetime import datetime, timedelta, UTC
from dataclasses import dataclass
import itertools
from logging import Logger
from structlog import get_logger
from typing import Any

from discord.member import Member
from discord.ext.commands import Cog, Context, command, has_role
from pytz import timezone
from tabulate import tabulate

from onehead.common import (
    Player,
    Roles,
    get_discord_member_from_name,
    play_sound,
    is_mention,
    get_discord_member_from_id,
    get_discord_id_from_mention,
)
from onehead.protocols.database import OneHeadDatabase


log: Logger = get_logger()


@dataclass
class Challenge:
    id: int
    expires: datetime
    challenger: Member
    opponent: Member
    in_progress: bool = False
    complete: bool = False


class ChallengeMode(Cog):

    MAX_RATING_DIFFERENCE: int = 2000
    MAX_CHALLENGES_ISSUED: int = 1
    MAX_CHALLENGED_RECEIVED: int = 1
    EXPIRATION: timedelta = timedelta(hours=24)

    counter = itertools.count()

    def __init__(self, database: OneHeadDatabase) -> None:
        self.database: OneHeadDatabase = database
        self.challenges: list[Challenge] = []

    @has_role(Roles.MEMBER)
    @command()
    async def challenge(self, ctx: Context, opponent_name: str) -> None:
        challenger: Member = ctx.author
        opponent: Member

        if is_mention(opponent_name):
            opponent_id: int | None = get_discord_id_from_mention(opponent_name)
            if opponent_id:
                opponent = get_discord_member_from_id(ctx, opponent_id)
        else:
            opponent = get_discord_member_from_name(ctx, opponent_name)

        if challenger == opponent:
            await ctx.send("You cannot challenge yourself...")
            return

        for challenge in self.challenges:
            if challenge.challenger.id == challenger.id:
                opponent = get_discord_member_from_id(ctx, challenge.opponent.id)
                await ctx.send(f"{challenger.mention} has already issued a challenge to {opponent.mention}!")
                return
            elif challenge.opponent.id == opponent.id:
                other_challenger: Member = get_discord_member_from_id(ctx, challenge.challenger.id)
                await ctx.send(f"{opponent.mention} has already been challenged by {other_challenger.mention}!")
                return

        challenger_record: Player | None = self.database.get(challenger.id)
        opponent_record: Player | None = self.database.get(opponent.id)

        if challenger_record is None or opponent_record is None:
            raise

        # TODO: Compare IHL ratings and/or MMR to see if it's a suitable challenge.
        if challenger_record["mmr"] - opponent_record["mmr"] > self.MAX_RATING_DIFFERENCE:
            await play_sound(ctx, "bully.mp3")
            await ctx.send(
                f"{challenger.mention}, your opponent must be within {self.MAX_RATING_DIFFERENCE} MMR of your MMR in order to duel them."
            )
            return

        # TODO: Persist challenges to database.

        await play_sound(ctx, "challenger.mp3")
        challenge: Challenge = Challenge(
            next(self.counter), datetime.now(UTC) + self.EXPIRATION, challenger=challenger, opponent=opponent
        )
        self.challenges.append(challenge)

        await ctx.send(f"{challenger.mention} has challenged {opponent.mention} to a 1v1 mid!")
        await ctx.send(
            f"{opponent.mention} has 24 hours to accept this challenge, if they wish to accept, type `!accept` {challenger.mention}."
        )

        create_task(self.handle_expired_challenge(ctx, challenge))

    @has_role(Roles.MEMBER)
    @command(aliases=["challenges"])
    async def list_active_challenges(self, ctx: Context) -> None:
        challenges: list[dict[str, Any]] = []
        for challenge in self.challenges:
            sorted_challenge: dict[str, Any] = {
                "challenger": challenge.challenger.display_name,
                "opponent": challenge.opponent.display_name,
                "in_progress": challenge.in_progress,
                "expires": challenge.expires.astimezone(timezone("Europe/London")).strftime("%d/%m/%Y, %H:%M:%S"),
            }
            challenges.append(sorted_challenge)

        if len(challenges) == 0:
            await ctx.send("There are no active challenges.")
        else:
            sorted: str = tabulate(challenges, headers="keys", tablefmt="simple")
            await ctx.send(f"**Challenges** ```\n{sorted}```")

    @has_role(Roles.MEMBER)
    @command(aliases=["accept"])
    async def accept_challenge(self, ctx: Context, name: str) -> None:
        challenge: Challenge | None = self.find_issued_challenge(ctx, name)

        if challenge:
            self.start_challenge(ctx, challenge)
        else:
            await ctx.send(f"Unable to find challenge issued to {ctx.author.mention} by {name}.")

    @has_role(Roles.MEMBER)
    @command(aliases=["reject"])
    async def reject_challenge(self, ctx: Context, name: str) -> None:
        challenge: Challenge | None = self.find_issued_challenge(ctx, name)

        if challenge:
            await ctx.send(
                f"{challenge.opponent.mention} has rejected the challenge issued by {challenge.challenger.mention}."
            )
            await play_sound(ctx, "shame.mp3")
            self.challenges.remove(challenge)
        else:
            await ctx.send(f"Unable to find challenge issued to {ctx.author.mention} by {name}.")

    @has_role(Roles.MEMBER)
    @command(aliases=["challenge_result"])
    async def enter_challenge_result(self, ctx: Context, opponent: str) -> None:
        pass

    def find_issued_challenge(self, ctx: Context, name: str) -> Challenge | None:
        challenged: Member = ctx.author
        challenger: Member

        if is_mention(name):
            challenger_id: int | None = get_discord_id_from_mention(name)
            challenger = get_discord_member_from_id(ctx, challenger_id)
        else:
            challenger = get_discord_member_from_name(ctx, challenger)

        for challenge in self.challenges:
            if challenge.opponent.id == challenged.id and challenge.challenger.id == challenger_id:
                return challenge

        return None

    async def start_challenge(self, ctx: Context, challenge: Challenge) -> None:
        # TODO: Calculate RBUCKS reward based on some base rate and then scaled based on difference in rating/MMR.
        # odds: float = self.calculate_odds(challenger, opponent)
        await play_sound(ctx, "gong.mp3")
        pass

    async def handle_expired_challenge(self, ctx: Context, challenge: Challenge):
        to_wait: timedelta = challenge.expires - datetime.now(UTC)
        await sleep(to_wait.total_seconds())

        if challenge.complete is False:
            await ctx.send(
                f"{challenge.opponent.mention} has failed to accept {challenge.challenger.mention}'s request to duel."
            )

        try:
            self.challenges.remove(challenge)
        except ValueError:
            pass

    def calculate_odds(self, challenger: Member, opponent: Member) -> float:
        pass
