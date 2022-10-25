import logging
import random
from asyncio import sleep
from typing import TYPE_CHECKING, Optional

from discord import Status
from discord.ext import commands
from tabulate import tabulate

import onehead.common
from onehead.common import log

if TYPE_CHECKING:
    from discord import VoiceState
    from discord.member import Member

    from onehead.db import OneHeadDB


class OneHeadRegistration(commands.Cog):
    def __init__(self, database: "OneHeadDB"):

        self.database = database

    @commands.has_role("IHL")
    @commands.command(aliases=["reg"])
    async def register(self, ctx: commands.Context, mmr: str):
        """
        Register yourself to the IHL by typing !register <your mmr>.
        """

        name = ctx.author.display_name

        try:
            mmr_int = int(mmr)  # type: int
        except ValueError:
            raise onehead.common.OneHeadException(f"{mmr} is not a valid integer.")

        if mmr_int < 1000:
            await ctx.send(
                f"{mmr_int} MMR is too low, must be greater or equal to 1000."
            )
            return

        exists, _ = self.database.player_exists(name)
        if exists is False:
            self.database.add_player(ctx.author.display_name, mmr_int)
            await ctx.send(f"{name} successfully registered.")
        else:
            await ctx.send(f"{name} is already registered.")

    @commands.has_role("IHL Admin")
    @commands.command(aliases=["dereg"])
    async def deregister(self, ctx: commands.Context, name: str):
        """
        Removes a player from the internal IHL database.
        """

        exists, _ = self.database.player_exists(name)
        if exists:
            self.database.remove_player(name)
            await ctx.send(f"{name} successfully removed from the database.")
        else:
            await ctx.send(f"{name} could not be found in the database.")


class OneHeadPreGame(commands.Cog):
    def __init__(self, database: "OneHeadDB"):

        self.database = database
        self.signups = []  # type: list[str]
        self.players_ready = []  # type: list[str]
        self.ready_check_in_progress = False
        self.context = None  # type: Optional[commands.Context]
        self._signups_disabled = False

    def disable_signups(self):
        self._signups_disabled = True

    @commands.has_role("IHL Admin")
    @commands.command()
    async def summon(self, ctx: commands.Context):
        """
        Messages all registered players of the IHL to come and sign up.
        """

        ihl_role = [x for x in ctx.guild.roles if x.name == "IHL"]
        if not ihl_role:
            return

        await ctx.send(f"IHL DOTA - LET'S GO! {ihl_role[0].mention}")

    def reset_state(self):
        self.signups = []
        self._signups_disabled = False

    async def signup_check(self, ctx: commands.Context) -> bool:

        signup_count = len(self.signups)
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

    async def handle_signups(self, ctx: commands.Context):
        """
        Handle the case where there are less than 10 signups, exactly 10 signups or more than 10 signups. If there are
        more, then players will be randomly removed until there are only 10 players in self.signups.

        :param ctx: Discord context
        """

        number_of_signups = len(self.signups)
        if number_of_signups <= 10:
            return

        benched_players = []
        await ctx.send(
            f"{number_of_signups} Players have signed up and therefore {number_of_signups - 10} players will be benched."
        )
        while len(self.signups) > 10:
            idx = self.signups.index(random.choice(self.signups))
            random_selection = self.signups.pop(idx)
            benched_players.append(random_selection)

        await ctx.send(f"**Benched Players:** ```\n{benched_players}```")
        await ctx.send(f"**Selected Players:** ```\n{self.signups}```")

    @commands.has_role("IHL")
    @commands.command()
    async def who(self, ctx: commands.Context):
        """
        Shows all players currently signed up to play in the IHL.
        """

        await ctx.send(f"There are currently {len(self.signups)} players signed up.")
        signups_dict = [
            {"#": i + 1, "name": name} for i, name in enumerate(self.signups)
        ]
        signups = tabulate(signups_dict, headers="keys", tablefmt="simple")

        await ctx.send(f"**Current Signups** ```\n{signups}```")

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.has_role("IHL")
    @commands.command(aliases=["su"])
    async def signup(self, ctx: commands.Context):
        """
        Signup to join a game in the IHL.
        """

        if self._signups_disabled:
            await ctx.send("Game in Progress - Signup command unavailable.")
            return

        name = ctx.author.display_name
        exists, _ = self.database.player_exists(name)
        if exists is False:
            await ctx.send("Please register first using the !reg command.")
            return

        if name in self.signups:
            await ctx.send(f"{name} is already signed up.")
        else:
            self.signups.append(name)

        if self.context is None:
            self.context = ctx

        await commands.Command.invoke(self.who, ctx)

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.has_role("IHL")
    @commands.command(aliases=["so"])
    async def signout(self, ctx: commands.Context):
        """
        Remove yourself from the current pool of signed up players.
        """

        if self._signups_disabled:
            await ctx.send("Game in Progress - Signout command unavailable.")
            return

        if ctx.author.display_name not in self.signups:
            await ctx.send(f"{ctx.author.display_name} is not currently signed up.")
        else:
            self.signups.remove(ctx.author.display_name)

        await commands.Command.invoke(self.who, ctx)

    @commands.has_role("IHL Admin")
    @commands.command(aliases=["rm"])
    async def remove(self, ctx: commands.Context, name: str):
        """
        Remove a player who is currently signed up.
        """

        if name not in self.signups:
            await ctx.send(f"{name} is not currently signed up.")
            return

        self.signups.remove(name)
        await ctx.send(f"{name} has been removed from the signup pool.")

    @commands.has_role("IHL")
    @commands.command(aliases=["r"])
    async def ready(self, ctx: commands.Context):
        """
        Use this command in response to a ready check.
        """
        name = ctx.author.display_name

        if name not in self.signups:
            await ctx.send(f"{name} needs to sign in first.")
            return

        if self.ready_check_in_progress is False:
            await ctx.send("No ready check initiated.")
            return

        self.players_ready.append(name)
        await ctx.send(f"{name} is ready.")

    @commands.has_role("IHL")
    @commands.command(aliases=["rc"])
    async def ready_check(self, ctx: commands.Context):
        """
        Initiates a ready check, after approx. 30s the result of the check will be displayed.
        """
        if await self.signup_check(ctx):
            await ctx.send(
                "Ready Check Started, 30s remaining - type '!ready' to ready up."
            )
            self.ready_check_in_progress = True
            await sleep(30)
            players_ready_count = len(self.players_ready)
            players_not_ready = ", ".join(
                [x for x in self.signups if x not in self.players_ready]
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

    if onehead.common.bot is None:
        return

    pre_game = onehead.common.bot.get_cog("OneHeadPreGame")

    name = member.display_name

    if after.afk and name in pre_game.signups:
        pre_game.signups.remove(name)
        log.info(f"{name} is now AFK.")
        await pre_game.context.send(f"{name} has been signed out due to being AFK.")


async def on_member_update(before: "Member", after: "Member") -> None:

    if onehead.common.bot is None:
        return

    pre_game = onehead.common.bot.get_cog("OneHeadPreGame")

    name = after.display_name

    if after.status in (Status.offline, Status.idle) and name in pre_game.signups:
        pre_game.signups.remove(name)
        reason = "Offline" if after.status == Status.offline else "Idle"
        log.info(f"{name} is now {reason}.")
        await pre_game.context.send(
            f"{name} has been signed out due to being {reason}."
        )
