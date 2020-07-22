from discordToken import token
import discord
import sqlite3
import soundvoltex
import config
import re

client = discord.Client()

commands = {
    'search':soundvoltex.search,
    'songsearch':soundvoltex.search,
    'ss':soundvoltex.search,
    'searchdiff':soundvoltex.searchdiff,
    'sd':soundvoltex.searchdiff,
    'random':soundvoltex.random,
    }


async def handleReactions(payload):
    channel = client.get_channel(payload.channel_id)
    channelId = payload.channel_id
    guildId = payload.guild_id
    #message = await channel.fetch_message(payload.message_id)
    #Ignore reaction if created by the bot
    #print(payload.user_id)
    #print(client.user.id)
    if payload.user_id == client.user.id: 
        #print('passing through reaction')
        return
    emoji = str(payload.emoji)
    print(emoji)
    #Check what type of embed it is: either a song search or single song
    print(config.serverSongQueue)
    if guildId in config.serverSongQueue and channelId in config.serverSongQueue[guildId]:
        for songObject in config.serverSongQueue[guildId][channelId]:
            if songObject.messageId == payload.message_id:
                #Check what type of object, most likely a single song
                if isinstance(songObject,soundvoltex.SingleSong) and emoji in config.emojiToDifficultyLevel:
                    await songObject.changeInfo(config.emojiToDifficultyLevel[emoji])
                elif isinstance(songObject,soundvoltex.SongSearch) and emoji in config.pageChangeDictionary:
                    await songObject.changePage(config.pageChangeDictionary[emoji])
    #Assume that the embed is just a song then
    else:
        print(str(payload.emoji))
        #print('Invalid object to react to')
        await channel.send(str(payload.emoji) + ' received')
    return
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    request = message.content
    #Main control flow for commands
    if request.startswith('*'):
        #Just take it out, I don't want to have to deal with the asterisk
        request = request[1:]
        #Get the first word 
        command = request.split(' ')[0]
        print(command,'requested')
        if command in commands:
            await commands[command](message)
    else:
        #Handle page navigation or turn a songlist into a singlesong
        content = message.content
        #Check the number first because there's no point going farther 
        pageNumberRequested = isinstance(config.pageParser.match(content),re.Match)
        number = config.numberParser.match(content)
        if pageNumberRequested:
            number = config.numberParser.search(content)
        print(config.serverSongQueue)
        if isinstance(number,re.Match):
            number = int(number.group())
            #See if the user is requesting a page
            for index,songObject in enumerate(config.serverSongQueue[message.guild.id][message.channel.id]):
                if isinstance(songObject,soundvoltex.SongSearch): 
                    if pageNumberRequested:
                        await songObject.setPage(number)
                    else:
                        #Transform the songsearch into a single song
                        print('attempting to convert',config.serverSongQueue[message.guild.id][message.channel.id][index],'to single song')
                        #print(config.serverSongQueue)
                        config.serverSongQueue[message.guild.id][message.channel.id][index] = await songObject.convertToSingleSong(number)
                        await config.serverSongQueue[message.guild.id][message.channel.id][index].startCountdown(10)
                        #print(config.serverSongQueue)

            #See what number they request with the page (or the song number)
    return

@client.event
async def on_raw_reaction_add(payload):
    await handleReactions(payload)
    
@client.event
async def on_raw_reaction_remove(payload):
    await handleReactions(payload)

@client.event
async def on_ready():
    print("Logged in as",client.user)
    print('Currently a part of these servers:')
    for guild in client.guilds:
         print(guild,'id:',guild.id)
    print('Total guild total of',str(len(client.guilds)))
    
client.run(token)
