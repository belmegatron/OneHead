import discord


class OneHeadException(BaseException):
    pass


class OneHeadChannels(object):

    def __init__(self):

        self.channel_names = ['IGC IHL #1', 'IGC IHL #2']
        self.channels = []

        self.t1 = None
        self.t2 = None

    def set_teams(self, t1, t2):

        self.t1 = t1
        self.t2 = t2

    async def create_discord_channels(self, ctx):

        expected_ihl_channels = [x for x in ctx.guild.voice_channels if x.name in self.channel_names]

        for channel in self.channel_names:
            if channel not in expected_ihl_channels:
                await ctx.send("Creating {} channel".format(channel))
                await ctx.guild.create_voice_channel(channel)

        self.channels = [x for x in ctx.guild.voice_channels if x.name in self.channel_names]

    async def move_back_to_lobby(self, ctx):

        t1_names = [x['name'] for x in self.t1]
        t2_names = [x['name'] for x in self.t2]
        team_1 = [x for x in ctx.guild.members if x.display_name in t1_names]
        team_2 = [x for x in ctx.guild.members if x.display_name in t2_names]

        lobby = [x for x in ctx.guild.voice_channels if x.name == "DOTA 2"][0]

        for member in team_1:
            try:
                await member.move_to(lobby)
            except discord.errors.HTTPException:
                pass

        for member in team_2:
            try:
                await member.move_to(lobby)
            except discord.errors.HTTPException:
                pass

    async def move_discord_channels(self, ctx):

        n_channels = len(self.channels)
        if n_channels != 2:
            raise OneHeadException("Expected 2 Discord Channels, Identified {}.".format(n_channels))

        t1_names = [x['name'] for x in self.t1]
        t2_names = [x['name'] for x in self.t2]
        team_1 = [x for x in ctx.guild.members if x.display_name in t1_names]
        team_2 = [x for x in ctx.guild.members if x.display_name in t2_names]

        await ctx.send("Moving Players to IHL Discord Channels...")

        for member in team_1:
            try:
                await member.move_to(self.channels[0])
            except discord.errors.HTTPException:
                pass

        for member in team_2:
            try:
                await member.move_to(self.channels[1])
            except discord.errors.HTTPException:
                pass
