from discordToken import token
import discord
import sqlite3
import soundvoltex
import config

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
    message = await channel.fetch_message(payload.message_id)
    #Ignore reaction if created by the bot
    if payload.user_id == client.user.id: 
        print('passing through reaction')
        return
    emoji = str(payload.emoji)
    #Check what type of embed it is: either a song search or single song
    if payload.guild_id in config.serverSongQueue:
        for songObject in config.serverSongQueue[payload.guild_id]:
            if songObject.messageId == payload.message_id:
                #Check what type of object, most likely a single song
                if isinstance(songObject,soundvoltex.SingleSong) and emoji in config.emojiToDifficultyLevel:
                    await songObject.changeInfo(config.emojiToDifficultyLevel[emoji])
                elif isinstance(songObject,soundvoltex.SongSearch):
                    if emoji in config.pageChangeDictionary:
                        await songObject.changePage(config.pageChangeDictionary[emoji])
    #Assume that the embed is just a song then
    else:
        print(str(payload.emoji))
        print('Invalid object to react to')
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
