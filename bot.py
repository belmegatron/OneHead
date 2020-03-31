import os
import time
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='!')


@bot.command()
async def join(ctx):
    channel = ctx.author.voice.channel
    await channel.connect()
    await ctx.send("1Head IGC IHL Bot reporting for duty sir...")


@bot.command()
async def leave(ctx):
    await ctx.voice_client.disconnect()


@bot.command()
async def start(ctx):
    await ctx.send("Game starting in ...")
    for second in range(3, 0, -1):
        await ctx.send("{}".format(second))
        time.sleep(1)
    await ctx.send("Go!")


@bot.command()
async def stop(ctx):
    await ctx.send("Game stopped.")


@bot.command()
async def balance(ctx):
    await ctx.send("Balancing teams...")


@bot.command()
async def result(ctx, side):
    sides = ["Radiant", "Dire"]

    if side not in sides:
        await ctx.send("Invalid Value - Must be either 'Radiant' or 'Dire'.")
        return

    await ctx.send("{} Victory!".format(side))
    await ctx.send("Updating Scores...")


@bot.command()
async def leaderboard(ctx):
    await ctx.send("Current IGC Leaderboard:")


bot.run(TOKEN)
