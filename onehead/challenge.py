from asyncio import create_task, sleep, wait_for
from datetime import datetime, timedelta, UTC
from dataclasses import dataclass
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
    is_mention,
    get_discord_member_from_id,
    get_discord_id_from_mention,
)
from onehead.protocols.database import OneHeadDatabase
from onehead.betting import Betting


log: Logger = get_logger()


@dataclass
class Challenge:
    id: int
    expires: datetime
    challenger: Member
    opponent: Member
    in_progress: bool = False
    complete: bool = False
    # TODO: We need to store the bet prices in here too as they will be accessed by the Betting cog.


class ChallengeMode(Cog):

    MAX_RATING_DIFFERENCE: int = 2000
    MAX_CHALLENGES_ISSUED: int = 1
    MAX_CHALLENGED_RECEIVED: int = 1
    EXPIRATION: timedelta = timedelta(hours=24)

    counter = itertools.count()

    def __init__(self, database: OneHeadDatabase, betting: Betting) -> None:
        self.database: OneHeadDatabase = database
        self.betting: Betting = betting
        self.challenges: list[Challenge] = []
        self._active: bool = False

    @has_role(Roles.MEMBER)
    @command()
    async def challenge(self, ctx: Context, opponent_name: str) -> None:
        """
        Challenge an opponent to a 1v1 mid duel e.g. `!challenge ERIC`        
        """
        challenger: Member | User = ctx.author
        opponent: Member | None = None

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
                other_challenger: Member | None = get_discord_member_from_id(ctx, challenge.challenger.id)
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
        challenge: Challenge = Challenge(
            next(self.counter), datetime.now(UTC) + self.EXPIRATION, challenger=challenger, opponent=opponent
        )
        self.challenges.append(challenge)

        await ctx.send(f"{challenger.mention} has challenged {opponent.mention} to a 1v1 mid!")
        await ctx.send(
            f"{opponent.mention} has 24 hours to accept this challenge, if they wish to accept, type `!accept` {challenger.mention}."
        )

        create_task(self.handle_expired_challenge(ctx, challenge))
    
    # TODO: Remove this.
    @has_role(Roles.ADMIN)
    @command()
    async def sim_challenge(self, ctx: Context) -> None:
        challenge: Challenge = Challenge(
            next(self.counter), datetime.now(UTC) + self.EXPIRATION, challenger=get_discord_member_from_name(ctx, "GEE"), opponent=get_discord_member_from_name(ctx, "RBEEZAY")
        )
        self.challenges.append(challenge)

    @has_role(Roles.MEMBER)
    @command(aliases=["challenges"])
    async def list_challenges(self, ctx: Context) -> None:
        """
        Lists all active challenges.
        """
        
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
    @command()
    async def accept(self, ctx: Context, name: str) -> None:
        """
        Accept a duel issued by a challenger e.g. `!accept BOBBY`
        """
        challenge: Challenge | None = self.find_issued_challenge(ctx, name)

        if challenge:
            if challenge.in_progress is False:
                await self.start_challenge(ctx, challenge)
                challenge.in_progress = True
            else:
                await ctx.send(f"{challenge.opponent} has already accepted their duel vs. {challenge.challenger}!")
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

    async def result(self, ctx: Context, opponent: str) -> None:
        # TODO: Allow the user to use the !result command to also enter results for duels.
        pass

    def find_issued_challenge(self, ctx: Context, challenger_name: str) -> Challenge | None:
        challenged: Member | User = ctx.author
        challenger: Member | None = None

        if is_mention(challenger_name):
            challenger_id: int | None = get_discord_id_from_mention(challenger_name)
            challenger = get_discord_member_from_id(ctx, challenger_id)
        else:
            challenger = get_discord_member_from_name(ctx, challenger_name)

        for challenge in self.challenges:
            if challenge.opponent.id == challenged.id and challenge.challenger.id == challenger.id:
                return challenge

        return None

    async def start_challenge(self, ctx: Context, challenge: Challenge) -> None:
        await play_sound(ctx, "gong.mp3")
        
        challenger_odds: float
        opponent_odds: float
        
        challenger_odds, opponent_odds = self.betting.calculate_challenge_odds(challenge)
        await ctx.send(f"{challenge.challenger.mention} price: {challenger_odds}, {challenge.opponent.mention} price: {opponent_odds}")
        # TODO: Open betting window.
        # TODO: Close betting window.
        
        await play_sound(ctx, "fight.mp3")
        
        
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
