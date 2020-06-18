from discordToken import token
import discord
from discord.ext import commands
import sqlite3
from soundvoltex import SoundVoltexCommands

bot = commands.Bot(command_prefix='*')
#Main command for querying the sdvx database
#I think I will create optional arguments with either * or ^ or # (maybe !)?
@bot.command()
async def refresh(ctx):
    bot.remove_cog('SoundVoltexCommands')
    bot.add_cog(SoundVoltexCommands(bot))
    return await ctx.send("refreshed")


@bot.event
async def on_ready():
    bot.add_cog(SoundVoltexCommands(bot))
    return
#Query conditions:
#cursor.execute("SELECT * FROM songs WHERE title_name LIKE ?",("%"+query+"%",))
#cursor.execute("SELECT * FROM songs WHERE title_yomigana LIKE ?",("%"+query+"%",))
bot.run(token)
