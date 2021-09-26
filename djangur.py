import discord
from commands import Commands, Guild_Instance, play_search
import json
import os
#from pymongo import MongoClient
#import pymongo


#with open('config.json') as f:
#    config = json.load(f)

#CONNECTION_STRING = f"mongodb+srv://{config['mongo_user']}:{config['mongo_password']}@djangur.erogd.mongodb.net/djangur?retryWrites=true&w=majority"

#db_client = MongoClient(CONNECTION_STRING)

#print(db_client)



client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(msg):
    if msg.author == client.user:
        return

    ginst = Guild_Instance.by_id(msg.guild.id)
    ginst.tc = msg.channel

    if msg.content.isdigit() and ginst.searching:
       await play_search(msg.content, msg=msg, client=client, ginst=ginst)

    if not msg.content.startswith(os.environ['prefix']):
        return

    no_prefix = msg.content[len(os.environ['prefix']):]
    split = no_prefix.split(' ', 1)
    cmd = split[0]
    args = split[1] if (len(split) == 2) else ''

    if cmd in Commands.command_map:
        await Commands.command_map[cmd](args, msg=msg, client=client, ginst=ginst)
    else:
        await msg.channel.send(f'{cmd}: Command not found.')

#client.run(config['token'])
client.run(os.environ['token'])
