import discord
from discord.ext import commands
import sqlite3

bot = commands.Bot(command_prefix='*')
url = "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fi.warosu.org%2Fdata%2Fjp%2Fimg%2F0157%2F50%2F1472280879855.png&f=1&nofb=1"
url2 = "http://remywiki.com/images/thumb/a/aa/Daiuchuu_stage.png/200px-Daiuchuu_stage.png"
#Main command for querying the sdvx database
#I think I will create optional arguments with either * or ^ or # (maybe !)?
@bot.command()
async def search(ctx,*arg):
    #arg is a parameter which loads each word into a tuple
    message = arg
    await ctx.send(message)
    query = " ".join(message) 
    db = sqlite3.connect('sdvx.db')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    cursor.execute('''SELECT 
            title_name FROM songs WHERE title_name LIKE ? ORDER BY distribution_date''',("%"+query+"%",))
    results = cursor.fetchall()
    songsFound = len(results)
    if songsFound == 1:
        #Reopen db
        #PLEASE PUT THIS INTO ANOTHER FILE WHEN THE TIME COMES
        with sqlite3.connect('sdvx.db') as db:
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            song = cursor.execute('''SELECT title_name,
                    artist_name,
                    bpm_min,
                    bpm_max,
                    distribution_date,
                    genre,
                    version FROM songs WHERE title_name = ?''',results[0]).fetchone()
            #execute another query for exact info
            embed=discord.Embed(title=song['title_name'], description=song['distribution_date'], color=0x21ff20)
            embed.set_author(name=song['version'],icon_url=url)
            embed.set_thumbnail(url=url2)
            embed.add_field(name='Artist',value=song['artist_name'],inline=False)
            if song['bpm_min'] == song['bpm_max']:
                embed.add_field(name='BPM',value=song['bpm_min'],inline=True)
            else:
                embed.add_field(name='BPM',value=song['bpm_min']+song['bpm_max'],inline=True)
        return await ctx.send(embed=embed)
    elif songsFound > 2:
        await ctx.send(f'{len(results)} song(s) found')
        db.close()
        if songsFound > 20:
            return await ctx.send('Too many songs, please use a different search.')
        return await ctx.send('\n'.join(x['title_name'] for x in results))
        
    elif not songsFound:
        await ctx.send('searching harder...')
        results = cursor.execute("SELECT title_name FROM songs WHERE title_yomigana LIKE ?",("%"+query+"%",)).fetchall()
        songsFound = len(results)
        if not songsFound:
            db.close()
            return await ctx.send("I've got nothing.")
    #return await ctx.send(embed=embed)

#Query conditions:
#cursor.execute("SELECT * FROM songs WHERE title_name LIKE ?",("%"+query+"%",))
#cursor.execute("SELECT * FROM songs WHERE title_yomigana LIKE ?",("%"+query+"%",))
bot.run('NTk2NDkzNjU3NDI3ODA0MTgy.XufiYA.hvBaRtC76i4Cslwv70_J9aP7MAI')
