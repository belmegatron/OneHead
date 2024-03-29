from asyncio import sleep
from logging import Logger
from typing import TYPE_CHECKING, Any

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
    max_concurrency
)
from discord.guild import Guild
from discord.message import Message
from discord.role import Role
from structlog import get_logger
from tabulate import tabulate

from onehead.common import (
    OneHeadException,
    Player,
    Roles,
    get_bot_instance,
    get_discord_member_from_name,
    play_sound
)
from onehead.game import Game
from onehead.protocols.database import OneHeadDatabase

if TYPE_CHECKING:
    from discord.member import Member


log: Logger = get_logger()


class Lobby(Cog):
    def __init__(self, database: OneHeadDatabase) -> None:
        self.database: OneHeadDatabase = database
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
            raise OneHeadException("No Guild associated with Discord context.")

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
                await ctx.send(f"Only `{signup_count}` signup(s), require `{10 - signup_count}` more.")
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
            f"`{number_of_signups}` Players have signed up and therefore `{number_of_signups - 10}` players will be benched."
        )

        if len(self._signups) > 10:
            await ctx.send(
                "More than `10` signups identified, selecting the top `10` players with the highest behaviour score."
            )

            original_signups: list[str] = self._signups

            players: list[Player] = []

            for signup in self._signups:
                member: Member | None = get_discord_member_from_name(ctx, signup)
                player: Player | None = self.database.get(member.id)

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

        await ctx.send(f"There are currently `{len(self._signups)}` players signed up.")
        signups_dict: list[dict[str, Any]] = [{"#": i, "name": name} for i, name in enumerate(self._signups, start=1)]
        signups: str = tabulate(signups_dict, headers="keys", tablefmt="simple")

        await ctx.send(f"**Current Signups** ```\n{signups}```")

    @cooldown(1, 10, BucketType.user)
    @has_role(Roles.MEMBER)
    @command(aliases=["su"])
    async def signup(self, ctx: Context) -> None:
        """
        Signup to join a game in the IHL.
        """

        if self._signups_disabled:
            await ctx.send("Game in progress - `!su` command unavailable.")
            return

        name: str = ctx.author.display_name
        player: Player | None = self.database.get(ctx.author.id)
        if player is None:
            await ctx.send("Please register first using the `!register` command.")
            return

        if name in self._signups:
            await ctx.send(f"{ctx.author.mention} is already signed up.")
            return
        else:
            self._signups.append(name)

        if self._context is None:
            self._context = ctx

        log.info(f"{name} has signed up.")

        await Command.invoke(self.who, ctx)

    @cooldown(1, 10, BucketType.user)
    @has_role(Roles.MEMBER)
    @command(aliases=["so"])
    async def signout(self, ctx: Context) -> None:
        """
        Remove yourself from the current pool of signed up players.
        """

        if self._signups_disabled:
            await ctx.send("Game in progress - `!so` command unavailable.")
            return

        name: str = ctx.author.display_name

        if name not in self._signups:
            await ctx.send(f"{ctx.author.mention} is not currently signed up.")
        else:
            self._signups.remove(name)

        log.info(f"{name} has signed out.")

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

        log.info(f"{name} has been removed from the signup pool by {ctx.author.display_name}.")

        member: Member | None = get_discord_member_from_name(ctx, name)
        await ctx.send(f"{member.mention} has been removed from the signup pool.")

    @has_role(Roles.MEMBER)
    @command(aliases=["r"])
    async def ready(self, ctx: Context) -> None:
        """
        Use this command in response to a ready check.
        """
        name: str = ctx.author.display_name

        if name not in self._signups:
            await ctx.send(f"{ctx.author.mention} needs to sign in first.")
            return

        if self._ready_check_in_progress is False:
            await ctx.send("No ready check initiated.")
            return

        self._players_ready.append(name)

        log.info(f"{name} is ready.")

        await ctx.send(f"{ctx.author.mention} is ready.")

    @has_role(Roles.MEMBER)
    @command(aliases=["rc"])
    @max_concurrency(1, per=BucketType.default, wait=False)
    async def ready_check(self, ctx: Context) -> None:
        """
        Initiates a ready check, after approx. 30s the result of the check will be displayed.
        """
        
        if await self.signup_check(ctx):
            await play_sound(ctx, "ready.mp3")
            
            log.info(f"{ctx.author.display_name} initiated a ready check.")
            await ctx.send("Ready check started - `30s` remaining - type `!ready` to ready up.")
            self._ready_check_in_progress = True
            await sleep(30)

            players_not_ready: list[str] = [name for name in self._signups if name not in self._players_ready]
            mentions_not_ready: list[str] = [get_discord_member_from_name(ctx, name).mention for name in players_not_ready]
            if len(players_not_ready) == 0:
                await ctx.send("Ready check complete.")
            else:
                log.info(f"{len(players_not_ready)} not ready: {', '.join(players_not_ready)}.")
                await ctx.send(f"Still waiting on `{len(players_not_ready)}` players: {', '.join(mentions_not_ready)}.")

        self._ready_check_in_progress = False
        self._players_ready = []


async def on_presence_update(before: "Member", after: "Member") -> None:
    bot: Bot = get_bot_instance()

    core: Cog = bot.get_cog("Core")  # type: ignore[assignment]
    game: Game = core.current_game  # type: ignore[attr-defined]

    if game.in_progress():
        return

    lobby: Lobby = bot.get_cog("Lobby")  # type: ignore[assignment]
    if lobby._context is None:
        return

    signups: list[str] = lobby.get_signups()

    name: str = after.display_name

    if after.status in (Status.offline, Status.idle) and name in signups:
        reason: str = "Offline" if after.status == Status.offline else "Idle"
        log.info(f"{name} is now {reason}.")
        signups.remove(name)
        await lobby._context.send(f"{after.mention} has been signed out due to being {reason}.")


async def allow_message(message: Message, bot: Bot) -> bool:
    if message.author.display_name not in ("ERIC", "SCOUT"):
        return True

    commands: list[str] = [command.name for command in bot.commands]
    command_aliases: list[str] = []
    for cmd in bot.commands:
        command_aliases += cmd.aliases

    split_message: list[str] = message.content.split()
    user_command: str = split_message[0]

    prefix: str = user_command[0]
    if prefix != bot.command_prefix:
        return True

    user_command = user_command[1:]
    if user_command not in commands and user_command not in command_aliases:
        return False

    return True


async def on_message(message: Message) -> None:
    bot: Bot = get_bot_instance()

    if message.author.bot:
        return

    allow: bool = await allow_message(message, bot)
    if allow is False:
        await message.delete()
        return

    await bot.process_commands(message)
