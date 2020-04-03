class OneHeadException(BaseException):
    pass


class OneHeadChannels(object):

    def __init__(self, t1, t2):

        self.channel_names = ['IGC IHL #1', 'IGC IHL #2']
        self.channels = []

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

        team_1 = [x for x in ctx.guild.members if x.display_name in self.t1]
        team_2 = [x for x in ctx.guild.members if x.display_name in self.t2]

        lobby = [x for x in ctx.guild.voice_channels if x.name == "LOBBY"]

        for member in team_1:
            member.move_to(lobby)
        for member in team_2:
            member.move_to(lobby)

    async def move_discord_channels(self, ctx):

        team_1 = [x for x in ctx.guild.members if x.display_name in self.t1]
        team_2 = [x for x in ctx.guild.members if x.display_name in self.t2]

        for member in team_1:
            member.move_to(self.channel_names[0])
        for member in team_2:
            member.move_to(self.channel_names[1])
