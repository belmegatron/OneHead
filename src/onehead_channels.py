import discord
from src.onehead_common import OneHeadException, OneHeadCommon


class OneHeadChannels(object):

    def __init__(self, config):

        channel_config_settings = config["discord"]["channels"]
        self.channel_names = ["{} #{}".format(channel_config_settings["match"], x) for x in (1, 2)]
        self.lobby_name = channel_config_settings["lobby"]

        self.ihl_discord_channels = []
        self.t1 = []
        self.t2 = []
        self.t1_discord_members = []
        self.t2_discord_members = []

    def set_teams(self, t1, t2):
        """
        To be called by an object that has instantiated a OneHeadChannels object.

        :param t1: Players in Team 1
        :type t1: List of Player Objects.
        :param t2: Players in Team 2
        :type t2: List of Player Objects.
        """

        self.t1 = t1
        self.t2 = t2

    def _get_discord_members(self, ctx, t1_names, t2_names):
        """
        Obtains Discord Member objects for corresponding list of names.

        :param ctx: Discord Context
        :param t1_names: Names of players in Team 1
        :type t1_names: List of Strings
        :param t2_names: Names of players in Team 2
        :type t2_names: List of Strings
        """

        self.t1_discord_members = [x for x in ctx.guild.members if x.display_name in t1_names]
        self.t2_discord_members = [x for x in ctx.guild.members if x.display_name in t2_names]

    async def create_discord_channels(self, ctx):
        """
        We check if the channels already exist, if not we create them.

        :param ctx: Discord Context
        """

        expected_ihl_channels = [x.name for x in ctx.guild.voice_channels if
                                 x.name in self.channel_names]  # List of Strings

        for channel in self.channel_names:
            if channel not in expected_ihl_channels:
                await ctx.send("Creating {} channel".format(channel))
                await ctx.guild.create_voice_channel(channel)

        self.ihl_discord_channels = [x for x in ctx.guild.voice_channels if
                                     x.name in self.channel_names]  # List of Discord Voice Channel Objects

    async def move_back_to_lobby(self, ctx):
        """
        Move players back from IHL Team Channels to a communal channel.

        :param ctx: Discord Context
        """

        lobby, = [x for x in ctx.guild.voice_channels if x.name == self.lobby_name]

        for member in self.t1_discord_members:
            try:
                await member.move_to(lobby)
            except discord.errors.HTTPException:
                pass

        for member in self.t2_discord_members:
            try:
                await member.move_to(lobby)
            except discord.errors.HTTPException:
                pass

    async def move_discord_channels(self, ctx):
        """
        Move players to IHL Team Channels.

        :param ctx: Discord Context
        """

        channel_count = len(self.ihl_discord_channels)
        if channel_count != 2:
            raise OneHeadException("Expected 2 Discord Channels, Identified {}.".format(channel_count))

        t1_names, t2_names = OneHeadCommon.get_player_names(self.t1, self.t2)
        self._get_discord_members(ctx, t1_names, t2_names)

        await ctx.send("Moving Players to IHL Discord Channels...")

        t1_channel, t2_channel = self.ihl_discord_channels

        for member in self.t1_discord_members:
            try:
                await member.move_to(t1_channel)
            except discord.errors.HTTPException:
                pass

        for member in self.t2_discord_members:
            try:
                await member.move_to(t2_channel)
            except discord.errors.HTTPException:
                pass
