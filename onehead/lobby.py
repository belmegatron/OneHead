from asyncio import sleep
from logging import Logger
from typing import TYPE_CHECKING

from discord import Status
from discord.ext.commands import (BucketType, Cog, Command, Context, command,
                                  cooldown, has_role, Bot)
from tabulate import tabulate

from onehead.common import Roles, get_bot_instance, get_logger, Player
from onehead.database import Database

if TYPE_CHECKING:
    from discord import VoiceState
    from discord.member import Member
    

log: Logger = get_logger()


class Lobby(Cog):
    def __init__(self, database: Database) -> None:

        self.database: Database = database
        self._signups: list[str] = []
        self.players_ready: list[str] = []
        self.ready_check_in_progress: bool = False
        self.context: Context = None
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

        ihl_role: list[Member] = [
            x for x in ctx.guild.roles if x.name == Roles.MEMBER
        ]
        if not ihl_role:
            return

        await ctx.send(f"IHL DOTA - LET'S GO! {ihl_role[0].mention}")

    async def signup_check(self, ctx: Context) -> bool:

        signup_count: int = len(self._signups)
        if signup_count < 10:
            if signup_count == 0:
                await ctx.send("There are currently no signups.")
            else:
                await ctx.send(
                    f"Only {signup_count} Signup(s), require {10 - signup_count} more."
                )
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
            
            await ctx.send("More than 10 signups identified, selecting the top 10 players with the highest behaviour score.")
            
            original_signups: list[str] = self._signups
            players: list[Player] = [self.database.lookup_player(signup) for signup in self._signups]
            top_10_players_by_behaviour_score: list[Player] = sorted(players, key=lambda d: d["behaviour"], reverse=True)[:10]
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
        signups_dict = [
            {"#": i + 1, "name": name} for i, name in enumerate(self._signups)
        ]
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
        exists, _ = self.database.player_exists(name)
        if exists is False:
            await ctx.send("Please register first using the !reg command.")
            return

        if name in self._signups:
            await ctx.send(f"{name} is already signed up.")
        else:
            self._signups.append(name)

        if self.context is None:
            self.context = ctx

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

        if self.ready_check_in_progress is False:
            await ctx.send("No ready check initiated.")
            return

        self.players_ready.append(name)
        await ctx.send(f"{name} is ready.")

    @has_role(Roles.MEMBER)
    @command(aliases=["rc"])
    async def ready_check(self, ctx: Context) -> None:
        """
        Initiates a ready check, after approx. 30s the result of the check will be displayed.
        """
        if await self.signup_check(ctx):
            await ctx.send(
                "Ready Check Started, 30s remaining - type '!ready' to ready up."
            )
            self.ready_check_in_progress = True
            await sleep(30)
            players_ready_count: int = len(self.players_ready)
            players_not_ready: str = ", ".join(
                [x for x in self._signups if x not in self.players_ready]
            )
            if players_ready_count == 10:
                await ctx.send("Ready Check Complete - All players ready.")
            else:
                await ctx.send(
                    f"Still waiting on {10 - players_ready_count} players: {players_not_ready}"
                )

        self.ready_check_in_progress = False
        self.players_ready = []


async def on_voice_state_update(
    member: "Member", before: "VoiceState", after: "VoiceState"
) -> None:

    bot: Bot = get_bot_instance()
    lobby: Lobby = bot.get_cog("Lobby")
    
    signups: list[str] = lobby.get_signups()

    name: str = member.display_name

    if after.afk and name in signups:
        signups.remove(name)
        log.info(f"{name} is now AFK.")
        await lobby.context.send(f"{name} has been signed out due to being AFK.")


async def on_member_update(before: "Member", after: "Member") -> None:

    bot: Bot = get_bot_instance()
    lobby: Lobby = bot.get_cog("Lobby")
    
    signups: list[str] = lobby.get_signups()

    name: str = after.display_name

    if after.status in (Status.offline, Status.idle) and name in signups:
        reason: str = "Offline" if after.status == Status.offline else "Idle"
        log.info(f"{name} is now {reason}.")
        signups.remove(name)
        await lobby.context.send(
            f"{name} has been signed out due to being {reason}."
        )
        
        
