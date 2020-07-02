import discord,sqlite3,re
import math
import asyncio
import config

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
    """A class that generates a song list for the user to look through."""
    def __init__(self,channel,totalSongs,query,parameters):
        #Store the query that generates the songlist
        self.query = query
        #Store the message id on discord's end so we can identify the reaction
        #Get the channel so we can retrieve a message object from the api
        #Store the total amount of songs found
        self.totalSongs = totalSongs
        #Store the index the songlist takes at
        self.currentPage = 1
        #Store total pages the query has
        self.totalPages = math.ceil(totalSongs/10)
        self.parameters = parameters
        #Create the message object for the class
        self.message = None
        self.messageId = None
        self.channel = channel
        self.channelId = channel.id
    def __str__(self):
        string = 'SongList ID: '+str(self.messageId)+'CHANNEL' + str(self.channelId)
        return string
    def __repr__(self):
        string = 'SongList ID: '+str(self.messageId)+'CHANNEL' + str(self.channelId)
        return string
    async def getQuery(self):
        return self.query
    async def incrementPage(self,pages):
        """returns nothing, but increments the page that the songList represents"""
        if self.currentPage + pages >= self.totalPages:
            self.currentPage = self.totalPages
        else:
            self.currentPage += pages
        return
    async def decrementPage(self,pages):
        if self.currentPage - pages <= 1:
            self.currentPage = 1
        else:
            self.currentPage -= pages
        return
    async def createSongEmbed(self):
        with sqlite3.connect('sdvx.db') as db:
            cursor = db.cursor()
            cursor.execute(self.query + ' LIMIT 10 OFFSET ?',self.parameters + ((self.currentPage-1)*10,))
            results = cursor.fetchall()
            #Limit the row with LIMIT row_count, OFFSET offset
        embedBody = ''
        count = (self.currentPage-1)*10 + 1
        for song in results:
            embedBody += f'{count}) '
            embedBody += '**' + song[0] + '** | ' + song[1]
            embedBody += '\n'
            count += 1
        embedBody.rstrip('\n')
        embed = discord.Embed(title='**Song Search**',color=0x2abfe8)
        embed.add_field(name=str(self.totalSongs)+' songs found',value=embedBody,inline=True)
        embed.set_footer(text=f'Page {str(self.currentPage)}/{str(self.totalPages)}')
        return embed
    async def createSongMessage(self):
        assert self.message == None
        embed = await self.createSongEmbed()
        self.message = await self.channel.send(embed=embed)
        self.messageId = self.message.id
        #Attach the reactions to the thing
        await self.message.add_reaction('⬅️')
        await self.message.add_reaction('➡️')
        return
    async def updateSongPage(self):
        #Update the message with the next page.
        embed = await self.createSongEmbed()
        await self.message.edit(embed=embed)
        return


#Parsers to find what the user is asking for in searchdiff
difficultyParser = re.compile(r'nov|adv|exh|inf|ma?xi?m?u?m|gra?v|he?a?ve?n|vi?vi?d')
difficultyNumberParser = re.compile(r'\d{1,2}')

async def sanitize(commandString):
    """
    Returns the rest of the command without the command header.
    commandString: the string which calls the on_message command
    """
    #Strip any whitespace on the right side
    commandString = (commandString.strip()).rsplit(' ')
    #Check if just the commandString was supplied
    if len(commandString) == 1:
        #In this case just return an empty string
        return ''
    #If not, remove the first commandString and then return the rest
    commandString = commandString[1:]
    commandString = " ".join(commandString)
    return commandString

async def getSongInfo(title,message):
    """
    A function helper for search, random, and searchdiff, provided they only find one
    song.

    title: The database value of title_name, used to fetch more information in the
    database.

    message: The message that causes the whole on_message flow to occur, used
    to get the channel name and server of the message.
    """
    #Get all necessary information from the database
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
    #Create the embed 
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
    embed.set_footer(text=song['distribution_date'] + ' | ' + song['version'],icon_url=urls[song['version']])
    messageSent = await message.channel.send(embed=embed)
    messageSent.add_reaction('⬅️')
    print('Embed send todo')
    return
async def displayMultipleSongs(songs,message,query,parameters):
    """Given a list of songs, and the message, send an embed which allows users
    to go through the list through reaction commands."""
    #Create a music songList
    songlist = SongList(message.channel,len(songs),query,parameters)
    await songlist.createSongMessage()
    print(songlist.message.id)
    #Check if there is a dictionary for the current server 
    if message.guild.id in config.songListDictionary:
        #Insert the song into the dictionary
        config.songListDictionary[message.guild.id].append(songlist)
    else:
        #Create the song list
        config.songListDictionary[message.guild.id] = [songlist]
    print("Message sent, has id",songlist.messageId)
    return
async def search(message):
    """
    Given the message giving a song name in sound voltex, return the correct song.
    Message: The message generated through the on_message command.
    
    This may give some incorrect answers as we evaluate both the actual song name
    and the ascii name given to the song to help broaden the search for songs carrying
    special characters like Ego,Embryo, and maybe beta by yooh.
    """
    parameters = await sanitize(message.content)
    print(parameters)
    parameters = ('%'+parameters+'%','%'+parameters+'%')
    #Database parameters
    with sqlite3.connect('sdvx.db') as db:
        cursor = db.cursor()
        query = '''SELECT title_name,artist_name FROM songs 
            WHERE title_name LIKE ? OR ascii LIKE ?
            ORDER BY distribution_date DESC'''
        cursor.execute(query,parameters)
        results = cursor.fetchall()
    songsFound = len(results)
    print(songsFound)
    if songsFound == 1:
        await getSongInfo(results[0][0],message)
    elif songsFound >= 2:
        await displayMultipleSongs(results,message,query,parameters)
    elif not songsFound:
        await message.channel.send("I've got nothing.")
    return
async def searchdiff(message):
    """Return a list or song which contains the specified difficultyLevel and difficultyNumber."""
    """Message: The discord generated message, used to find the channel and send the message"""
    #Sanitize command to get query
    query = await sanitize(message.content)
    if len(query) == 0:
        return await message.channel.send('Usage: *searchdiff <difficultyType and/or difficultyNumber>')
    searchParameters = {}
    #Check what argument was supplied
    difficultyLevel = difficultyParser.search(query)
    difficultyNumber = difficultyNumberParser.search(query)
    #Check if the correct arguments were given
    difficultyLevelExists = isinstance(difficultyLevel,re.Match)
    difficultyNumberExists = isinstance(difficultyNumber,re.Match)
    if difficultyLevelExists:
        searchParameters['difficultyLevel'] = reToDifficulty[difficultyLevel.group()[0]]
    if difficultyNumberExists:
        difficultyNumber = int(difficultyNumber.group())
        if difficultyNumber >= 1 and difficultyNumber <= 20:
            #await ctx.send('You requested difficulty number ' + str(difficultyNumber))
            searchParameters['difficultyNumber'] = difficultyNumber
        else:
            return await message.channel.send('Invalid difficulty number: '+ str(difficultyNumber))
    if len(searchParameters.keys()) == 0:
        return await message.channel.send('Invalid parameters')
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
            query = """SELECT title_name,artist_name FROM songs 
                JOIN difficulties ON songs.id = difficulties.id
                WHERE """ + whereStatements
            cursor.execute(query)
            results = cursor.fetchall()
            print(results)
        if len(results) == 1:
            await getSongInfo(results[0][0],message)
        elif len(results) > 1:
            await displayMultipleSongs(results,message,query,tuple())
        else:
            await message.channel.send('No songs found with those parameters')
        return
async def random(message):
    """Return a random song in the database, or return a random song which falls
    within the difficulty number specified within the command"""
    arg = sanitize(message.content)
    print(arg)
    if len(arg) == 0:
        with sqlite3.connect('sdvx.db') as db:
            cursor = db.cursor()
            cursor.execute("SELECT title_name FROM songs ORDER BY random() LIMIT 1")
            title = cursor.fetchone()[0]
        await getSongInfo(title,message)
        return
    arg = arg[0]
    print(arg)
    if arg.isdigit() and int(arg) >= 1 and int(arg) <= 20:
        with sqlite3.connect('sdvx.db') as db:
            cursor = db.cursor()
            cursor.execute("SELECT title_name FROM songs JOIN difficulties ON songs.id = difficulties.id WHERE difficultyNumber = ? AND illustrator != 'dummy' ORDER BY random() LIMIT 1",(int(arg),))
            title = cursor.fetchone()[0]
        return await getSongInfo(title,message)
    elif len(arg.split('-')) == 2:
        arg = arg.split('-')
        print(arg)

        #Sanitize and check the values for the search
        for index,bound in enumerate(arg):
            if bound.strip().isdigit():
                arg[index] = int(bound)
                if arg[index] > 20 or arg[index] < 1:
                    return await message.channel.send('Invalid Level: '+ bound)
            else:
                return await message.channel.send('Usage: *random <1-20> or *random lowerLevel-UpperLevel')
        #Special case if someone is dumb enough to do maximum-minimum (or is testing the bot)
        if arg[0] > arg[1]:
            arg = [arg[1],arg[0]]
        #Perform random search
        print(arg)
        with sqlite3.connect('sdvx.db') as db:
            cursor = db.cursor()
            cursor.execute("SELECT title_name FROM songs JOIN difficulties ON songs.id = difficulties.id WHERE difficultyNumber >= ? AND difficultyNumber <= ? AND illustrator != 'dummy' ORDER BY random() LIMIT 1",(arg[0],arg[1]))
            title = cursor.fetchone()[0]
        return await getSongInfo(title,message)
    else:
        return await message.channel.send('Usage: *random <1-20> or *random lowerLevel-UpperLevel')


