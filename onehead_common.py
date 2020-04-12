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

        for channel in self.channel_names:
            await ctx.guild.create_voice_channel(channel)

        self.channels = [x for x in ctx.guild.voice_channels if x.name in self.channel_names]

    async def teardown_discord_channels(self):

        for channel in self.channels:
            await channel.delete()
        self.channels = []

    async def move_back_to_lobby(self, ctx):

        t1_names = [x['name'] for x in self.t1]
        t2_names = [x['name'] for x in self.t2]
        team_1 = [x for x in ctx.guild.members if x.display_name in t1_names]
        team_2 = [x for x in ctx.guild.members if x.display_name in t2_names]

        lobby = [x for x in ctx.guild.voice_channels if x.name == "LOBBY"][0]

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

        t1_names = [x['name'] for x in self.t1]
        t2_names = [x['name'] for x in self.t2]
        team_1 = [x for x in ctx.guild.members if x.display_name in t1_names]
        team_2 = [x for x in ctx.guild.members if x.display_name in t2_names]

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
