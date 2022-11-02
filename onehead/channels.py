from typing import TYPE_CHECKING

from discord import VoiceChannel
from discord.errors import HTTPException
from discord.ext import commands
from discord.member import Member

from onehead.common import OneHeadCommon, OneHeadException, Team


class OneHeadChannels(commands.Cog):
    def __init__(self, config: dict) -> None:

        channel_config_settings: dict = config["discord"]["channels"]
        self.channel_names: list[str] = [
            f"{channel_config_settings['match']} #{x}" for x in (1, 2)
        ]
        self.lobby_name: str = channel_config_settings["lobby"]

        self.ihl_discord_channels: list[VoiceChannel]
        self.t1: Team
        self.t2: Team
        self.t1_discord_members: list[Member]
        self.t2_discord_members: list[Member]

    def set_teams(self, t1: Team, t2: Team) -> None:
        """
        To be called by an object that has instantiated a OneHeadChannels object.

        :param t1: Players in Team 1
        :param t2: Players in Team 2
        """

        self.t1 = t1
        self.t2 = t2

    def _set_discord_members(
        self,
        ctx: commands.Context,
        t1_names: tuple[str, ...],
        t2_names: tuple[str, ...],
    ) -> None:
        """
        Obtains Discord Member objects for corresponding list of names.

        :param ctx: Discord Context
        :param t1_names: Names of players in Team 1
        :param t2_names: Names of players in Team 2
        """

        self.t1_discord_members = [
            x for x in ctx.guild.members if x.display_name in t1_names
        ]
        self.t2_discord_members = [
            x for x in ctx.guild.members if x.display_name in t2_names
        ]

    async def create_discord_channels(self, ctx: commands.Context) -> None:
        """
        We check if the channels already exist, if not we create them.

        :param ctx: Discord Context
        """

        expected_ihl_channels: list[str] = [
            x.name for x in ctx.guild.voice_channels if x.name in self.channel_names
        ]

        for channel in self.channel_names:
            if channel not in expected_ihl_channels:
                await ctx.send(f"Creating {channel} channel")
                await ctx.guild.create_voice_channel(channel)

        self.ihl_discord_channels = [
            x for x in ctx.guild.voice_channels if x.name in self.channel_names
        ]

    async def move_back_to_lobby(self, ctx: commands.Context) -> None:
        """
        Move players back from IHL Team Channels to a communal channel.

        :param ctx: Discord Context
        """

        lobby: VoiceChannel = [
            x for x in ctx.guild.voice_channels if x.name == self.lobby_name
        ][0]

        for member in self.t1_discord_members:
            try:
                await member.move_to(lobby)
            except HTTPException:
                pass

        for member in self.t2_discord_members:
            try:
                await member.move_to(lobby)
            except HTTPException:
                pass

    async def move_discord_channels(self, ctx: commands.Context) -> None:
        """
        Move players to IHL Team Channels.

        :param ctx: Discord Context
        """

        channel_count: int = len(self.ihl_discord_channels)
        if channel_count != 2:
            raise OneHeadException(
                f"Expected 2 Discord Channels, Identified {channel_count}."
            )

        if self.t1 is None or self.t2 is None:
            raise OneHeadException(
                "Expected to have valid references to teams prior to moving channels."
            )

        t1_names, t2_names = OneHeadCommon.get_player_names(self.t1, self.t2)
        self._set_discord_members(ctx, t1_names, t2_names)

        await ctx.send("Moving Players to IHL Discord Channels...")

        t1_channel, t2_channel = self.ihl_discord_channels

        for member in self.t1_discord_members:
            try:
                await member.move_to(t1_channel)
            except HTTPException:
                pass

        for member in self.t2_discord_members:
            try:
                await member.move_to(t2_channel)
            except HTTPException:
                pass
