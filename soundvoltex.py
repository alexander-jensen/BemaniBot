import discord
from discord.ext import commands
import sqlite3
url = "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fi.warosu.org%2Fdata%2Fjp%2Fimg%2F0157%2F50%2F1472280879855.png&f=1&nofb=1"
url2 = "http://remywiki.com/images/thumb/a/aa/Daiuchuu_stage.png/200px-Daiuchuu_stage.png"

urls = {
        'SOUND VOLTEX BOOTH':'https://i.imgur.com/iuQDSqu.jpg',
        'SOUND VOLTEX II -infinite infection-':'https://i.imgur.com/qfQr5Yc.jpg',
        'SOUND VOLTEX III GRAVITY WARS':'https://i.imgur.com/rJfdDKU.png',
        'SOUND VOLTEX IV HEAVENLY HAVEN':'https://i.imgur.com/wz0SIvo.png',
        'SOUND VOLTEX VIVID WAVE':'https://i.imgur.com/poqcuPt.png'
        }
class SoundVoltexCommands(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    @commands.command()
    async def search(self,ctx,*arg):
        #Search for the song
        #arg is a parameter which loads each word into a tuple
        message = arg
        query = " ".join(message) 
        print(query)
        #Database query
        with sqlite3.connect('sdvx.db') as db:
            cursor = db.cursor()
            cursor.execute('''SELECT title_name FROM songs 
                WHERE title_name LIKE :search OR ascii LIKE :search
                ORDER BY distribution_date DESC''',{'search':"%"+query+"%"})
            results = cursor.fetchall()
        songsFound = len(results)
        print(songsFound)
        if songsFound == 1:
            return await self.getSongInfo(results[0][0],ctx)
        elif songsFound >= 2:
            await ctx.send(f'{len(results)} songs found')
            #TODO: Allow the user to see the list through reaction commands
            if songsFound > 20:
                return await ctx.send('Too many songs, please use a different search.')
            return await ctx.send('\n'.join(x[0] for x in results))
        elif not songsFound:
            return await ctx.send("I've got nothing.")
    async def getSongInfo(self,title,ctx):
        with sqlite3.connect('sdvx.db') as db:
            print('attempting to search with title',title)
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            song = cursor.execute('''SELECT title_name,
                    artist_name,
                    bpm_min,
                    bpm_max,
                    distribution_date,
                    genre,
                    version FROM songs WHERE title_name = ?''',(title,)).fetchone()
        #execute another query for exact info
        embed=discord.Embed(title=song['title_name'], description=song['distribution_date'], color=0x21ff20)
        embed.set_author(name=song['version'],icon_url=urls[song['version']])
        embed.set_thumbnail(url=url2)
        embed.add_field(name='Artist',value=song['artist_name'],inline=False)
        #Show both bpms if needed
        bpmString = str(song['bpm_min']) 
        if song['bpm_min'] != song['bpm_max']:
            bpmString += ' - '+str(song['bpm_max'])
        embed.add_field(name='BPM',value=bpmString + ' BPM',inline=False)
        #Show categories
        embed.add_field(name='Categories',value=song['genre'],inline = False)
        #Send and attach 1-5 emotes depending on how many difficulties there are
        return await ctx.send(embed=embed)
    @commands.command()
    async def random(self,ctx,arg):
        with sqlite3.connect('sdvx.db') as db:
            cursor = db.cursor()
            cursor.execute("SELECT title_name FROM songs JOIN difficulties ON songs.id = difficulties.id WHERE difficultyNumber = ? AND illustrator != 'dummy' ORDER BY random() LIMIT 1",(int(arg),))
            title = cursor.fetchone()[0]
            print(title)

        return await self.getSongInfo(title,ctx)
