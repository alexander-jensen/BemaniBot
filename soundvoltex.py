import discord
import math
from discord.ext import commands
import sqlite3
import re
url = "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fi.warosu.org%2Fdata%2Fjp%2Fimg%2F0157%2F50%2F1472280879855.png&f=1&nofb=1"
url2 = "https://cdn.vox-cdn.com/thumbor/bqASZI3uKDGxAP3mTAX1TiGuuSg=/0x0:800x800/1200x0/filters:focal(0x0:800x800)/cdn.vox-cdn.com/uploads/chorus_asset/file/10838085/4head.jpg"

urls = {
        'SOUND VOLTEX BOOTH':'https://i.imgur.com/iuQDSqu.jpg',
        'SOUND VOLTEX II -infinite infection-':'https://i.imgur.com/qfQr5Yc.jpg',
        'SOUND VOLTEX III GRAVITY WARS':'https://i.imgur.com/rJfdDKU.png',
        'SOUND VOLTEX IV HEAVENLY HAVEN':'https://i.imgur.com/wz0SIvo.png',
        'SOUND VOLTEX VIVID WAVE':'https://i.imgur.com/poqcuPt.png'
        }

reToDifficulty = {
        'n':'novice',
        'a':'advanced',
        'e':'exhaust',
        'i':'infinite',
        'm':'maximum',
        'g':'gravity',
        'h':'heavenly',
        'v':'vivid'
        }
class SongList():
    def __init__(self,query,index,messageId):
        #Store the query that generates the songlist
        self.query = query
        #Store the index the songlist takes at
        self.index = index
        #Store the message id on discord's end so we can identify the reaction
        self.messageId = messageId
    def getSongList
class SoundVoltexCommands(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.difficultyParser = re.compile(r'nov|adv|exh|inf|ma?xi?m?u?m|gra?v|he?a?ve?n|vi?vi?d')
        self.difficultyNumberParser = re.compile(r'\d{1,2}')
    
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
            cursor.execute('''SELECT title_name,artist_name FROM songs 
                WHERE title_name LIKE :search OR ascii LIKE :search
                ORDER BY distribution_date DESC''',{'search':"%"+query+"%"})
            results = cursor.fetchall()
        songsFound = len(results)
        print(songsFound)
        if songsFound == 1:
            return await self.getSongInfo(results[0][0],ctx)
        elif songsFound >= 2:
            await self.displayMultipleSongs(results,ctx)
        elif not songsFound:
            return await ctx.send("I've got nothing.")

    @commands.command()
    async def searchdiff(self,ctx,*arg):
        query = ' '.join(arg)
        searchParameters = {}
        if len(arg) == 0:
            return await ctx.send('Usage: *searchdiff <difficultyType and/or difficultyNumber>')
        else:
            #Check what argument was supplied
            difficultyLevel = self.difficultyParser.search(query)
            difficultyNumber = self.difficultyNumberParser.search(query)
            #Check if the correct arguments were given
            difficultyLevelExists = isinstance(difficultyLevel,re.Match)
            difficultyNumberExists = isinstance(difficultyNumber,re.Match)
            if difficultyLevelExists:
                #await ctx.send('You requested difficulty ' + reToDifficulty[difficultyLevel.group()[0]])
                searchParameters['difficultyLevel'] = reToDifficulty[difficultyLevel.group()[0]]
            if difficultyNumberExists:
                difficultyNumber = int(difficultyNumber.group())
                if difficultyNumber >= 1 and difficultyNumber <= 20:
                    #await ctx.send('You requested difficulty number ' + str(difficultyNumber))
                    searchParameters['difficultyNumber'] = difficultyNumber
                else:
                    return await ctx.send('Invalid difficulty number: '+ str(difficultyNumber))
        if len(searchParameters.keys()) == 0:
            return await ctx.send('Invalid difficulty')
        else:
            #This is the actual query for songs
            #Create condition for each parameter given
            whereStatements = ''
            for key in searchParameters.keys():
                if len(whereStatements) > 0:
                    whereStatements += ' AND '
                if searchParameters[key] in ['infinite','gravity','heavenly','vivid']:
                    whereStatements += 'infinite_version' + " = '" + searchParameters[key] + "'"
                else:
                    whereStatements += key + " = '" + str(searchParameters[key]) + "'"
            print(whereStatements)
            #Perform search on database joining the two
            with sqlite3.connect('sdvx.db') as db:
                cursor = db.cursor()
                cursor.execute("""SELECT title_name,artist_name FROM songs 
                    JOIN difficulties ON songs.id = difficulties.id
                    WHERE 
                        """ + whereStatements)
                results = cursor.fetchall()
                print(results)
            if len(results) == 1:
                return await self.getSongInfo(results[0][0],ctx)
            elif len(results) > 1:
                await self.displayMultipleSongs(results,ctx)
            else:
                await ctx.send('No songs found with those parameters')
            return



    async def getSongInfo(self,title,ctx):
        with sqlite3.connect('sdvx.db') as db:
            print('attempting to search with title',title)
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            song = cursor.execute("""SELECT title_name,
                    artist_name,
                    bpm_min,
                    bpm_max,
                    distribution_date,
                    genre,
                    version FROM songs WHERE title_name = ?""",(title,)).fetchone()
        #execute another query for exact info
        embed=discord.Embed(title='**' + song['title_name'] + '**', description='\t'*(len(song['title_name'])//4) + song['artist_name'], color=0xffa500)
        embed.set_author(name='\t'*8)
        embed.set_thumbnail(url=url2)
        #Show both bpms if needed
        bpmString = str(song['bpm_min']) 
        if song['bpm_min'] != song['bpm_max']:
            bpmString += ' - '+str(song['bpm_max'])
        embed.add_field(name='BPM',value=bpmString + ' BPM',inline=False)
        #Show categories
        embed.add_field(name='Categories',value=song['genre'],inline = False)
        embed.set_footer(text=song['distribution_date']+ ' | ' + song['version'],icon_url=urls[song['version']])
        #Send and attach 1-5 emotes depending on how many difficulties there are
        await ctx.send(embed=embed)


        return
    async def displayMultipleSongs(self,songs,ctx):
        #Assumes that songs are called by songs and artist tuples, with song title being in 0 and artist in 1
        #Assumes songs is also has > 1 item
        #Find what command calls this search
        #Create embed
        #Limit songs for now to see if it actually works
        total = str(math.ceil((len(songs)/10)))
        start = 0
        end = start + 10 if len(songs) > 10 else len(songs)
        current = "1"
        message = ''
        count = start + 1
        for song in songs[start:end]:
            message += f'{count}) '
            message += '**' + song[0] + '** | ' + song[1]
            message += '\n'
            count += 1
        message.rstrip('\n')
        embed = discord.Embed(color=0x2abfe8)
        embed.add_field(name='**Song Search**',value=message,inline=True)
        embed.set_footer(text=f'Page {current}/{total}')
        #Grab the first 10 songs
        await ctx.send(embed=embed)
        #Add reactions to control left and right
        return

    @commands.command()
    async def on_reaction_add(reaction,user):
        await print(user)
        await print('This on_reaction_add command works?')
    @commands.command()
    async def random(self,ctx,*arg):
        if len(arg) == 0:
            with sqlite3.connect('sdvx.db') as db:
                cursor = db.cursor()
                cursor.execute("SELECT title_name FROM songs ORDER BY random() LIMIT 1")
                title = cursor.fetchone()[0]
            return await self.getSongInfo(title,ctx)
        arg = arg[0]
        print(arg)
        if arg.isdigit() and int(arg) >= 1 and int(arg) <= 20:
            with sqlite3.connect('sdvx.db') as db:
                cursor = db.cursor()
                cursor.execute("SELECT title_name FROM songs JOIN difficulties ON songs.id = difficulties.id WHERE difficultyNumber = ? AND illustrator != 'dummy' ORDER BY random() LIMIT 1",(int(arg),))
                title = cursor.fetchone()[0]
            return await self.getSongInfo(title,ctx)
        elif len(arg.split('-')) == 2:
            arg = arg.split('-')
            print(arg)

            #Sanitize and check the values for the search
            for index,bound in enumerate(arg):
                if bound.strip().isdigit():
                    arg[index] = int(bound)
                    if arg[index] > 20 or arg[index] < 1:
                        return await ctx.send('Invalid Level: '+ bound)
                else:
                    return await ctx.send('Usage: *random <1-20> or *random lowerLevel-UpperLevel')
            #Special case if someone is dumb enough to do maximum-minimum (or is testing the bot)
            if arg[0] > arg[1]:
                arg = [arg[1],arg[0]]
            #Perform random search
            print(arg)
            with sqlite3.connect('sdvx.db') as db:
                cursor = db.cursor()
                cursor.execute("SELECT title_name FROM songs JOIN difficulties ON songs.id = difficulties.id WHERE difficultyNumber >= ? AND difficultyNumber <= ? AND illustrator != 'dummy' ORDER BY random() LIMIT 1",(arg[0],arg[1]))
                title = cursor.fetchone()[0]
            return await self.getSongInfo(title,ctx)
        else:
            return await ctx.send('Usage: *random <1-20> or *random lowerLevel-UpperLevel')
