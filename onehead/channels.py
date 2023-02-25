from typing import TYPE_CHECKING

from discord import VoiceChannel
from discord.errors import HTTPException
from discord.ext.commands import Bot, Cog, Context
from discord.guild import Guild
from discord.member import Member

from onehead.common import OneHeadException, get_bot_instance, get_player_names
from onehead.game import Game

if TYPE_CHECKING:
    from onehead.core import Core


class Channels(Cog):
    def __init__(self, config: dict) -> None:
        channel_config_settings: dict = config["discord"]["channels"]
        self.channel_names: list[str] = [f"{channel_config_settings['match']} #{x}" for x in (1, 2)]
        self.lobby_name: str = channel_config_settings["lobby"]
        self.ihl_discord_channels: list[VoiceChannel]

    def get_discord_members(self, ctx) -> tuple[list[Member], list[Member]]:
        bot: Bot = get_bot_instance()
        core: Core = bot.get_cog("Core")  # type: ignore[assignment]
        current_game: Game | None = core.current_game

        if current_game is None or current_game.radiant is None or current_game.dire is None:
            raise OneHeadException("Unable to get discord members due to invalid game state.")

        t1_names, t2_names = get_player_names(current_game.radiant, current_game.dire)

        t1_discord_members: list[Member] = [x for x in ctx.guild.members if x.display_name in t1_names]
        t2_discord_members: list[Member] = [x for x in ctx.guild.members if x.display_name in t2_names]

        return t1_discord_members, t2_discord_members

    async def create_discord_channels(self, ctx: Context) -> None:
        """
        We check if the channels already exist, if not we create them.

        :param ctx: Discord Context
        """

        guild: Guild | None = ctx.guild
        if guild is None:
            raise OneHeadException("No Guild associated with Discord Context")

        expected_ihl_channels: list[str] = [x.name for x in guild.voice_channels if x.name in self.channel_names]

        for channel in self.channel_names:
            if channel not in expected_ihl_channels:
                await ctx.send(f"Creating {channel} channel")
                await guild.create_voice_channel(channel)

        self.ihl_discord_channels = [x for x in guild.voice_channels if x.name in self.channel_names]

    async def move_back_to_lobby(self, ctx: Context) -> None:
        """
        Move players back from IHL Team Channels to a communal channel.

        :param ctx: Discord Context
        """

        guild: Guild | None = ctx.guild
        if guild is None:
            raise OneHeadException("No Guild associated with Discord Context")

        lobby: VoiceChannel = [x for x in guild.voice_channels if x.name == self.lobby_name][0]

        t1_discord_members, t2_discord_members = self.get_discord_members(ctx)

        for team in (t1_discord_members, t2_discord_members):
            for player in team:
                try:
                    await player.move_to(lobby)
                except HTTPException:
                    pass

    async def move_discord_channels(self, ctx: Context) -> None:
        """
        Move players to IHL Team Channels.

        :param ctx: Discord Context
        """

        channel_count: int = len(self.ihl_discord_channels)
        if channel_count != 2:
            raise OneHeadException(f"Expected 2 Discord Channels, Identified {channel_count}.")

        await ctx.send("Moving Players to IHL Discord Channels...")

        t1_discord_members, t2_discord_members = self.get_discord_members(ctx)
        t1_channel, t2_channel = self.ihl_discord_channels

        for team, channel in (t1_discord_members, t1_channel), (
            t2_discord_members,
            t2_channel,
        ):
            for member in team:
                try:
                    await member.move_to(channel)
                except HTTPException:
                    pass
