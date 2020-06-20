from discordToken import token
import discord
from discord.ext import commands
import sqlite3
from soundvoltex import SoundVoltexCommands

bot = commands.Bot(command_prefix='*')
#Main command for querying the sdvx database
#I think I will create optional arguments with either * or ^ or # (maybe !)?
#Should use on_reaction_add
#And add_reaction()
@bot.command()
async def refresh(ctx):
    bot.remove_cog('SoundVoltexCommands')
    bot.add_cog(SoundVoltexCommands(bot))
    return await ctx.send("refreshed")


@bot.event
async def on_ready():
    #Load cogs for each respective game
    bot.add_cog(SoundVoltexCommands(bot))
    return
bot.run(token)
