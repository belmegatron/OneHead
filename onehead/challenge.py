from datetime import datetime
from dataclasses import dataclass

from discord.member import Member
from discord.ext.commands import Cog, Context, command, has_role

from onehead.common import Roles, get_discord_member_from_name, play_sound, is_mention
from onehead.protocols.database import OneHeadDatabase


@dataclass
class Challenge:
    expires: datetime
    in_progress: bool = False
    challenger_id: int
    opponent_id: int


class OneHeadChallenge(Cog):
    
    def __init__(self, database: OneHeadDatabase) -> None:
        self.database: OneHeadDatabase = database
        self.challenges: dict[int, Challenge]

    
    @has_role(Roles.MEMBER)
    @command()
    async def challenge(self, ctx: Context, opponent: str) -> None:
        
        challenger: Member = ctx.author
        challengee: Member
        
        if is_mention(opponent):
            challengee = opponent
        else:
            challengee = get_discord_member_from_name(opponent)
        
        # TODO: Check if challenger already has an active challenge. Limit them to only making 1 challenge at a time.
        # TODO: Compare IHL ratings and/or MMR to see if it's a suitable challenge.
        # TODO: Limit the number of challenges that any one person can receive to 3. active_challenges field in db profile?
        # TODO: Persist challenges to database.
        # TODO: Calculate RBUCKS reward based on some base rate and then scaled based on difference in rating/MMR.
        
        await play_sound("gong.mp3")
        ctx.send(f"{challenger.mention} has challenged {challengee.mention} to a 1v1 Shadowfiend mid!")
        ctx.send(f"{challengee.mention} has 24 hours to accept this challenge, if they wish to accept, type `!accept {challenger.mention}`")
        # TODO: Start new task to handle expiration.
    
    
    @has_role(Roles.MEMBER)
    @command(aliases=["challenges"])
    async def list_active_challenges(self, ctx: Context) -> None:
        pass
        
    
    @has_role(Roles.MEMBER)
    @command(aliases=["accept"])
    async def accept_challenge(self, ctx: Context, opponent: str) -> None:
        pass
    
    @has_role(Roles.MEMBER)
    @command(aliases=["reject"])
    async def reject_challenge(self, ctx: Context, opponent: str) -> None:
        pass