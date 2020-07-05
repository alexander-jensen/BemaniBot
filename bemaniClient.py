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

pageChangeDictionary = {
        '➡️':1,
        '⬅️':-1
        }

async def handleReactions(payload):
    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    #Ignore reaction if created by the bot
    print(payload.user_id)
    print(client.user.id)
    if payload.user_id == client.user.id: 
        print('passing through reaction')
        return
    #Check what type of embed it is: either a song search or single song
    print(message.embeds[0].title)
    if message.embeds[0].title == '**Song Search**':
        print('Song Search found')
        #Fetch the channel so we can fetch the message object
        #Check if server has a song list dictionary (which it should)
        print(config.serverSongQueue)
        if payload.guild_id in config.serverSongQueue:
            for songList in config.serverSongQueue[payload.guild_id]:
                if songList.messageId == payload.message_id:
                    #Finally, we find what reaction was passed
                    print(payload.emoji)
                    #Call the song to be updated
                    if str(payload.emoji) in pageChangeDictionary:
                        await songList.changePage(pageChangeDictionary[str(payload.emoji)])
                        await songList.updateSongPage()
                    return
    #Assume that the embed is just a song then
    else:
        print(str(payload.emoji))
        print('Reaction received on single song')
        await channel.send(str(payload.emoji) + ' received')
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
