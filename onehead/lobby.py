from asyncio import sleep
from logging import Logger
from typing import TYPE_CHECKING

from discord import Status
from discord.ext.commands import (
    Bot,
    BucketType,
    Cog,
    Command,
    Context,
    command,
    cooldown,
    has_role,
)
from discord.guild import Guild
from discord.role import Role
from tabulate import tabulate

from onehead.common import OneHeadException, IPlayerDatabase, Player, Roles, get_bot_instance, get_logger

if TYPE_CHECKING:
    from discord.member import Member


log: Logger = get_logger()


class Lobby(Cog):
    def __init__(self, database: IPlayerDatabase) -> None:
        self.database: IPlayerDatabase = database
        self._signups: list[str] = []
        self._players_ready: list[str] = []
        self._ready_check_in_progress: bool = False
        self._context: Context | None = None
        self._signups_disabled: bool = False

    def disable_signups(self) -> None:
        self._signups_disabled = True

    def clear_signups(self) -> None:
        self._signups = []
        self._signups_disabled = False

    def get_signups(self) -> list[str]:
        return self._signups

    @has_role(Roles.ADMIN)
    @command()
    async def summon(self, ctx: Context) -> None:
        """
        Messages all registered players of the IHL to come and sign up.
        """

        guild: Guild | None = ctx.guild
        if guild is None:
            raise OneHeadException("No Guild associated with Discord Context.")

        ihl_role: Role = [x for x in guild.roles if x.name == Roles.MEMBER][0]
        if not ihl_role:
            return

        await ctx.send(f"IHL DOTA - LET'S GO! {ihl_role.mention}")

    async def signup_check(self, ctx: Context) -> bool:
        signup_count: int = len(self._signups)
        if signup_count < 10:
            if signup_count == 0:
                await ctx.send("There are currently no signups.")
            else:
                await ctx.send(f"Only {signup_count} Signup(s), require {10 - signup_count} more.")
        else:
            return True

        return False

    async def select_players(self, ctx: Context) -> None:
        """
        Handle the case where there are less than 10 signups, exactly 10 signups or more than 10 signups. If there are
        more, then players will be randomly removed until there are only 10 players in self.signups.

        :param ctx: Discord context
        """

        number_of_signups: int = len(self._signups)
        if number_of_signups <= 10:
            return

        await ctx.send(
            f"{number_of_signups} Players have signed up and therefore {number_of_signups - 10} players will be benched."
        )

        if len(self._signups) > 10:
            await ctx.send(
                "More than 10 signups identified, selecting the top 10 players with the highest behaviour score."
            )

            original_signups: list[str] = self._signups

            players: list[Player] = []

            for signup in self._signups:
                player: Player | None = self.database.get(signup)

                if player is None:
                    raise OneHeadException(f"Unable to find {signup} in database.")

                players.append(player)

            # TODO: Need to handle the case where we have > 10 with the same behaviour score.

            top_10_players_by_behaviour_score: list[Player] = sorted(
                players, key=lambda d: d["behaviour"], reverse=True
            )[:10]
            self._signups = [player["name"] for player in top_10_players_by_behaviour_score]
            benched_players: list[str] = [x for x in original_signups if x not in self._signups]

        await ctx.send(f"**Benched Players:** ```\n{benched_players}```")
        await ctx.send(f"**Selected Players:** ```\n{self._signups}```")

    @has_role(Roles.MEMBER)
    @command()
    async def who(self, ctx: Context) -> None:
        """
        Shows all players currently signed up to play in the IHL.
        """

        await ctx.send(f"There are currently {len(self._signups)} players signed up.")
        signups_dict = [{"#": i, "name": name} for i, name in enumerate(self._signups, start=1)]
        signups: str = tabulate(signups_dict, headers="keys", tablefmt="simple")

        await ctx.send(f"**Current Signups** ```\n{signups}```")

    @cooldown(1, 30, BucketType.user)
    @has_role(Roles.MEMBER)
    @command(aliases=["su"])
    async def signup(self, ctx: Context) -> None:
        """
        Signup to join a game in the IHL.
        """

        if self._signups_disabled:
            await ctx.send("Game in Progress - Signup command unavailable.")
            return

        name: str = ctx.author.display_name
        player: Player | None = self.database.get(name)
        if player is None:
            await ctx.send("Please register first using the !reg command.")
            return

        if name in self._signups:
            await ctx.send(f"{name} is already signed up.")
            return
        else:
            self._signups.append(name)

        if self._context is None:
            self._context = ctx

        await Command.invoke(self.who, ctx)

    @cooldown(1, 30, BucketType.user)
    @has_role(Roles.MEMBER)
    @command(aliases=["so"])
    async def signout(self, ctx: Context) -> None:
        """
        Remove yourself from the current pool of signed up players.
        """

        if self._signups_disabled:
            await ctx.send("Game in Progress - Signout command unavailable.")
            return

        if ctx.author.display_name not in self._signups:
            await ctx.send(f"{ctx.author.display_name} is not currently signed up.")
        else:
            self._signups.remove(ctx.author.display_name)

        await Command.invoke(self.who, ctx)

    @has_role(Roles.ADMIN)
    @command(aliases=["rm"])
    async def remove(self, ctx: Context, name: str) -> None:
        """
        Remove a player who is currently signed up.
        """

        if name not in self._signups:
            await ctx.send(f"{name} is not currently signed up.")
            return

        self._signups.remove(name)
        await ctx.send(f"{name} has been removed from the signup pool.")

    @has_role(Roles.MEMBER)
    @command(aliases=["r"])
    async def ready(self, ctx: Context) -> None:
        """
        Use this command in response to a ready check.
        """
        name: str = ctx.author.display_name

        if name not in self._signups:
            await ctx.send(f"{name} needs to sign in first.")
            return

        if self._ready_check_in_progress is False:
            await ctx.send("No ready check initiated.")
            return

        self._players_ready.append(name)
        await ctx.send(f"{name} is ready.")

    @has_role(Roles.MEMBER)
    @command(aliases=["rc"])
    async def ready_check(self, ctx: Context) -> None:
        """
        Initiates a ready check, after approx. 30s the result of the check will be displayed.
        """
        if await self.signup_check(ctx):
            await ctx.send("Ready Check Started, 30s remaining - type '!ready' to ready up.")
            self._ready_check_in_progress = True
            await sleep(30)
            players_not_ready: list[str] = [x for x in self._signups if x not in self._players_ready]
            if len(players_not_ready) == 0:
                await ctx.send("Ready Check Complete - All players ready.")
            else:
                await ctx.send(f"Still waiting on {len(players_not_ready)} players: {', '.join(players_not_ready)}")

        self._ready_check_in_progress = False
        self._players_ready = []


async def on_presence_update(before: "Member", after: "Member") -> None:
    bot: Bot = get_bot_instance()
    lobby: Lobby = bot.get_cog("Lobby")  # type: ignore[assignment]
    if lobby._context is None:
        return

    signups: list[str] = lobby.get_signups()

    name: str = after.display_name

    if after.status in (Status.offline, Status.idle) and name in signups:
        reason: str = "Offline" if after.status == Status.offline else "Idle"
        log.info(f"{name} is now {reason}.")
        signups.remove(name)
        await lobby._context.send(f"{name} has been signed out due to being {reason}.")
