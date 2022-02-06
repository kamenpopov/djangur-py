import asyncio
import discord
from commands import Commands, Guild_Instance, leave, play_search
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

CONNECTION_STRING = f"mongodb+srv://{os.environ['mongo_user']}:{os.environ['mongo_pass']}@djangur.erogd.mongodb.net/djangur?retryWrites=true&w=majority"

db_client = MongoClient(CONNECTION_STRING)
db = db_client['djangur']

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))
    print(os.environ['prefix'])

@client.event
async def on_message(msg):
    if msg.author == client.user:
        return

    ginst = Guild_Instance.by_id(msg.guild.id)
    ginst.tc = msg.channel

    ginst.db = db[str(msg.guild.id)]

    if msg.content.isdigit() and ginst.searching:
       await play_search(msg.content, msg=msg, client=client, ginst=ginst)

    if not msg.content.startswith(os.environ['prefix']):
        return

    no_prefix = msg.content[len(os.environ['prefix']):]
    split = no_prefix.split(' ', 1)
    cmd = split[0]
    args = split[1] if (len(split) == 2) else ''

    if cmd in Commands.command_map:
        await Commands.command_map[cmd].fn(args, msg=msg, client=client, ginst=ginst)
    else:
        await msg.channel.send(f'{cmd}: Command not found.')


@client.event
async def on_voice_state_update(member, before, after):
    if not member.name == 'Джангър':
        return
    
    elif before.channel is None:
        ginst = Guild_Instance.by_id(after.channel.guild.id)
        voice = after.channel.guild.voice_client
        time = 0
        while True:
            await asyncio.sleep(1)
            time = time + 1
            if voice.is_playing() and not voice.is_paused():
                time = 0
            if time == 600:
                print(await Commands.command_map['leave'].fn(None, None, None, ginst))
            if not voice.is_connected():
                break
    elif before.channel is not None:
        if after.channel is None:
            ginst = Guild_Instance.by_id(before.channel.guild.id)
            await Commands.command_map['leave'].fn(None, None, None, ginst)


client.run(os.environ['token'])
