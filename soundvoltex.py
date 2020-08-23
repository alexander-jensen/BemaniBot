import discord,sqlite3,re
import math
import asyncio
import config


class SongSearch():
    """A class that generates a song list for the user to look through."""
    def __init__(self,totalSongs,query,parameters,jump='general'):
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
        self.channelId = None
        self.guildId = None
        #The jump required for converting a song search into a single song directly instead of directing towards general
        self.jump = jump
    def __str__(self):
        string = 'SongSearch ID: '+str(self.messageId)
        return string
    def __repr__(self):
        string = 'SongSearch ID: '+str(self.messageId)
        return string
    def __len__(self):
        return self.totalPages*10
    async def getQuery(self):
        return self.query
    async def changePage(self,pages):
        """Changes the page the songlist is currently on."""
        #Handle page increase
        if pages > 0:
            if self.currentPage + pages >= self.totalPages:
                self.currentPage = self.totalPages
            else:
                self.currentPage += pages
        else:
        #Handle page decrease
            if self.currentPage + pages < 1:
                self.currentPage = 1
            else:
                self.currentPage += pages
        await self.updateSongPage()
    async def setPage(self,page):
        if page <= self.totalPages and page > 0:
            self.currentPage = page
            await self.updateSongPage()
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
    async def createSongMessage(self,channel):
        assert self.message == None
        embed = await self.createSongEmbed()
        self.message = await channel.send(embed=embed)
        self.messageId = self.message.id
        self.channelId = channel.id
        self.guildId = self.message.guild.id
        #Attach the reactions to the thing
        if self.totalPages != 1:
            await self.message.add_reaction('⬅️')
            await self.message.add_reaction('➡️')
        return
    async def updateSongPage(self):
        #Update the message with the next page.
        embed = await self.createSongEmbed()
        await self.message.edit(embed=embed)
        return
    async def convertToSingleSong(self,number):
        #print('Number',number,'requested')
        #print('SongSearch has total of',self.totalSongs,'pages')
        if number > self.totalSongs:
            #print('Number is higher than total, returning')
            return self
        with sqlite3.connect('sdvx.db') as db:
            cursor = db.cursor()
            #print(self.query)
            #print(self.parameters)
            #print(number)
            cursor.execute(self.query + ' LIMIT 1 OFFSET ?',self.parameters + (number-1,))
            song = cursor.fetchone()
            #print(song)
            #print(song[0])
            #print(song[2])
            song = SingleSong(song[0],song[2],self.message,self.jump)
            await song.createSongMessage(self.channelId)
            #print(song)
            return song

    async def startCountdown(self,time):
        print(config.serverSongQueue[self.guildId])
        await asyncio.sleep(time)
        try:
            config.serverSongQueue[self.guildId][self.channelId].remove(self)
        except ValueError:
            pass
        print(config.serverSongQueue[self.guildId])

class SingleSong():
    #An object used to handle single song searches. 
    def __init__(self,songTitle,songId,message=None,info='general'):
        self.songTitle = songTitle
        self.songId = songId
        self.message = message
        if message:
            self.guildId = message.guild.id
            self.messageId = self.message.id
            self.channelId = self.message.channel.id
            #print('guild id set as',self.guildId)
        #Fetch what difficulties this song has
        self.info = info
        #Default infinite version for dummy
        self.infiniteVersion = 0
        with sqlite3.connect('sdvx.db') as db:
            cursor = db.cursor()
            difficulties = cursor.execute(
                    """SELECT difficultyLevel FROM difficulties 
                    WHERE id = ? AND difficultyNumber != 0""",
                    (self.songId,)).fetchall()
            #print(difficulties)
            self.difficulties = [x[0] for x in difficulties] 
            #Check if there's an infinite, search the infinite version for the song
            if 'infinite' in self.difficulties:
                infiniteVersion = cursor.execute(
                    """SELECT infinite_version FROM songs WHERE id = ?"""
                    ,(self.songId,)
                    ).fetchone()[0]
                self.difficulties[self.difficulties.index('infinite')] = infiniteVersion
            additionalInfo = cursor.execute('SELECT artist_name,distribution_date,version FROM songs WHERE id = ?',(self.songId,)).fetchone()
            self.songArtist,self.uploadDate,self.version = additionalInfo
            #Convert the difficultyNumber into difficultyLevel
            #print(self.info)
            #print(type(self.info))
            
            if isinstance(self.info,int):
                cursor.execute("""SELECT difficultyLevel FROM songs JOIN difficulties ON songs.id = difficulties.id WHERE songs.id = ? AND difficultyNumber = ?""",(self.songId,self.info))
                #print('converting info to difficulty')
                self.info = cursor.fetchone()[0]
                if self.info == 'infinite':
                    self.info = infiniteVersion
        #print(self.difficulties)
    def __str__(self):
        string = 'SingleSong ID: '+str(self.messageId)
        return string
    def __repr__(self):
        string = 'SingleSong ID: '+str(self.messageId)
        return string
    def __len__(self):
        return 10*len(self.difficulties)
    async def createSongMessage(self,channel):
        """Creates the message and allows the song to have a message to handle itself"""
        embed = await self.generateEmbed()
        if self.message == None:
            self.message = await channel.send(embed=embed)
            self.messageId = self.message.id
            self.channelId = channel.id
            self.guildId = self.message.guild.id
        else:
            try:
                await self.message.clear_reactions()
                await self.message.edit(embed=embed)
            except discord.Forbidden:
                await self.message.channel.send('Clearing Reactions Failed. Please give me a role that can manage messages please!')
        await self.message.add_reaction('🏘️')
        for difficulty in self.difficulties:
            await self.message.add_reaction(config.difficultyLevelToEmoji[difficulty])
        return
    async def generateEmbed(self):
        db = sqlite3.connect('sdvx.db')
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        #print('Creating embed for',self.info)
        #print(self.songTitle)
        if self.info == 'general':
            #Select the highest placing jacket art?
            #If doesn't exist, use the current one
            song = cursor.execute("""SELECT 
                    bpm_min,
                    bpm_max,
                    distribution_date,
                    genre,
                    noviceJacketURL,
                    exhaustJacketURL,
                    advancedJacketURL,
                    infiniteJacketURL,
                    maximumJacketURL,
                    version FROM songs JOIN jacketImages ON songs.id = jacketImages.id
                    WHERE title_name = ?""",(self.songTitle,)).fetchone()
            #print(song.keys())
            url = 'https://i.imgur.com/PXu2ARI.png'
            for table in ['maximumJacketURL','infiniteJacketURL','exhaustJacketURL','advancedJacketURL','noviceJacketURL']:
                #print(table)
                if song[table] != None:
                    url = 'https://i.imgur.com/' +  song[table] + '.png'
                    break
                
            #Create the embed 
            embed=discord.Embed(title='**' + self.songTitle + '**',
                   description='\t'*(len(self.songTitle)//4) + self.songArtist,
                   color=config.difficultyToColor[self.info])
            embed.set_author(name='\t'*8)
            embed.set_thumbnail(url=url)
            #Show both bpms if needed
            bpmString = str(song['bpm_min']) 
            if song['bpm_min'] != song['bpm_max']:
                bpmString += ' - '+str(song['bpm_max'])
            embed.add_field(name='BPM',value=bpmString + ' BPM',inline=True)
            #Show categories728323422492557518CHANNEL590611437785710624
            embed.add_field(name='Categories',value=song['genre'],inline =False)
        else:
            #print(self.info)
            #print(self.difficulties)
            assert self.info in self.difficulties
            difficultyLevel = 'infinite' if self.info in ['gravity','heavenly','vivid'] else self.info
            difficultyInfo = cursor.execute(f"""SELECT difficultyLevel,
                difficultyNumber,
                illustrator,
                effector,noviceJacketURL,{difficultyLevel}JacketURL 
                FROM difficulties JOIN jacketImages ON difficulties.id = jacketImages.id 
                WHERE difficulties.id = ? AND difficultyLevel = ?""",(self.songId,difficultyLevel)).fetchone()
            jacketQuery = difficultyLevel + 'JacketURL'
            url = 'https://i.imgur.com/'
            if difficultyInfo[jacketQuery]:
                url += difficultyInfo[jacketQuery]
            else:
                url += difficultyInfo['noviceJacketURL']
            url += '.png'
            #print(difficultyInfo)
            #Create the embed
            #print(self.info)
            embed = discord.Embed(title = '**' + self.songTitle + '**',
                    description = self.songArtist,
                    color=config.difficultyToColor[self.info])
            embed.set_thumbnail(url=url)
            embed.add_field(name='Level',value=self.info.title() + ' ' + str(difficultyInfo['difficultyNumber']),inline=False)
            embed.add_field(name='Illustrator',value=difficultyInfo['illustrator'],inline=True)
            embed.add_field(name='Effector',value=difficultyInfo['effector'],inline=True)
            #Assume that the current info is a difficulty
        #Close the database and return
        embed.set_footer(text = self.uploadDate + ' | ' + self.version,
                icon_url = config.urls[self.version])
        db.close()
        return embed
    async def changeInfo(self,info):
        """Change the mode to either general information or a specific difficulty,
        This function is fairly voltile if changed incorrectly."""
        #Change the mode
        self.info = info
        await self.updateSongPage()
    async def updateSongPage(self):
        embed = await self.generateEmbed()
        await self.message.edit(embed=embed)
        return
    async def startCountdown(self,time):
        #print(config.serverSongQueue[self.guildId])
        await asyncio.sleep(time)
        try:
            config.serverSongQueue[self.guildId][self.channelId].remove(self)
        except:
            pass
        #print(config.serverSongQueue[self.guildId])
            


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

async def loadIntoSongQueue(message,songObject):
    channelId = message.channel.id
    guildId = message.guild.id
    #print(config.serverSongQueue)
    if guildId not in config.serverSongQueue:  
        config.serverSongQueue[guildId] = {}
    if channelId not in config.serverSongQueue[guildId]:
        config.serverSongQueue[guildId][channelId] = []
    config.serverSongQueue[guildId][channelId].append(songObject)
    #print(config.serverSongQueue)
    await songObject.startCountdown(len(songObject))
async def getSongInfo(title,titleId,message):
    """
    A function helper for search, random, and searchdiff, provided they only find one
    song.

    title: The database value of title_name, used to fetch more information in the
    database.

    message: The message that causes the whole on_message flow to occur, used
    to get the channel name and server of the message.
    """
    #Create the singlesong class 
    song = SingleSong(title,titleId)
    await song.createSongMessage(message.channel)
    #Load the song into the dictionary
    await loadIntoSongQueue(message,song)
    return
async def displayMultipleSongs(songs,message,query,parameters,jump='general'):
    """Given a list of songs, and the message, send an embed which allows users
    to go through the list through reaction commands."""
    #Create a music songList
    songList = SongSearch(len(songs),query,parameters,jump)
    await songList.createSongMessage(message.channel)
    await loadIntoSongQueue(message,songList)
    ##print("Message sent, has id",songlist.messageId)
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
    #print(parameters)
    parameters = ('%'+parameters+'%','%'+parameters+'%')
    #Database parameters
    with sqlite3.connect('sdvx.db') as db:
        cursor = db.cursor()
        query = '''SELECT title_name,artist_name,id FROM songs 
            WHERE title_name LIKE ? OR ascii LIKE ?
            ORDER BY distribution_date DESC'''
        cursor.execute(query,parameters)
        results = cursor.fetchall()
    songsFound = len(results)
    #print(songsFound)
    if songsFound == 1:
        await getSongInfo(results[0][0],results[0][2],message)
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
    if not difficultyLevelExists and not difficultyNumberExists:
        return await message.channel.send('Usage: *searchdiff <difficultyType and/or difficultyNumber>')
    if difficultyNumberExists:
        difficultyNumber = int(difficultyNumber.group())
        if difficultyNumber >= 1 and difficultyNumber <= 20:
            #await ctx.send('You requested difficulty number ' + str(difficultyNumber))
            searchParameters['difficultyNumber'] = difficultyNumber
            jump = difficultyNumber
        else:
            return await message.channel.send('Invalid difficulty number: '+ str(difficultyNumber))
    #Catch if one of the three common levels are requested, present nothing for these
    if difficultyLevelExists:
        if 'difficultyNumber' not in searchParameters and difficultyLevel.group()[0] in ['n','a','e']:
            return await message.channel.send('Difficulty number is required for this difficulty level.')
        searchParameters['difficultyLevel'] = config.reToDifficulty[difficultyLevel.group()[0]]
        jump = searchParameters['difficultyLevel']
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
        ##print(whereStatements)
        #Perform search on database joining the two
        with sqlite3.connect('sdvx.db') as db:
            cursor = db.cursor()
            query = """SELECT DISTINCT title_name,artist_name,songs.id FROM songs 
                JOIN difficulties ON songs.id = difficulties.id
                WHERE """ + whereStatements
            cursor.execute(query)
            results = cursor.fetchall()
            ##print(results)
        if len(results) == 1:
            await getSongInfo(results[0][0],results[0][2],message)
        elif len(results) > 1:
            await displayMultipleSongs(results,message,query,tuple(),jump)
        else:
            await message.channel.send('No songs found with those parameters')
        return
async def random(message):
    """Return a random song in the database, or return a random song which falls
    within the difficulty number specified within the command"""
    arg = await sanitize(message.content)
    #print('random command used')
    #print(arg)
    if len(arg) == 0:
        with sqlite3.connect('sdvx.db') as db:
            cursor = db.cursor()
            cursor.execute("SELECT title_name,songs.id FROM songs ORDER BY random() LIMIT 1")
            query = cursor.fetchone()
        await getSongInfo(query[0],query[1],message)
        return
    #print(arg)
    if arg.isdigit() and int(arg) >= 1 and int(arg) <= 20:
        with sqlite3.connect('sdvx.db') as db:
            cursor = db.cursor()
            cursor.execute("SELECT title_name,songs.id FROM songs JOIN difficulties ON songs.id = difficulties.id WHERE difficultyNumber = ? AND illustrator != 'dummy' ORDER BY random() LIMIT 1",(int(arg),))
            query = cursor.fetchone()
        return await getSongInfo(query[0],query[1],message)
    #See if there is a lower and upper bound
    elif len(arg.split('-')) == 2:
        arg = arg.split('-')
        #print(arg)

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
        #print(arg)
        with sqlite3.connect('sdvx.db') as db:
            cursor = db.cursor()
            cursor.execute("SELECT title_name,songs.id FROM songs JOIN difficulties ON songs.id = difficulties.id WHERE difficultyNumber >= ? AND difficultyNumber <= ? AND illustrator != 'dummy' ORDER BY random() LIMIT 1",(arg[0],arg[1]))
            query = cursor.fetchone()
        return await getSongInfo(query[0],query[1],message)
    else:
        return await message.channel.send('Usage: *random <1-20> or *random lowerLevel-UpperLevel')


async def help(message):
    embed = discord.Embed(title='**Bemani Bot Commands**',description="You asked for help, so I'm here!",color=0x111111)
    #thumbnail = 'https://pbs.twimg.com/profile_images/1144135580948631552/YFph2-V6_400x400.jpg'
    #print(thumbnail)
    #embed.set_thumbnail(url=thumbnail)
    embed.add_field(name='**Suggestions**',value="If you have suggestions, please ask! I've run out of what else to do with this bot!",inline=True)
    embed.add_field(name='**Commands**',value='''
    ```<*ss|*search|*songsearch> [Song Name] \n\t[Search for a song using title name (or artist).]\n<*sd|*searchdiff> [Difficulty and/or Number] \n\t[Use level and/or number (ex: exh 18) to find a song.]\n<*random> [lowerNumber - upperNumber]\n\t[Provides a random song for you to play!]\n*help: \n\tYou're already here!```
    ''',inline=False)
    embed.set_footer(text='Created by Scarlex | Source Code: https://github.com/Scarlex-git/BemaniBot',
                    icon_url='https://pbs.twimg.com/profile_images/1144135580948631552/YFph2-V6_400x400.jpg')
    return await message.channel.send(embed=embed)