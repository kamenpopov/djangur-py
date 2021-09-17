import discord
from commands import ping
import json

with open('config.json') as f:
    config = json.load(f)
print(config)

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(msg):
    if not msg.content.startswith(config['prefix']):
        return
    if msg.author == client.user:
        return

    no_prefix = msg.content[len(config['prefix']):]
    split = no_prefix.split(' ')
    cmd = split[0]
    args = split[1:]

    if cmd == 'ping':
        await ping(*args, msg=msg, client=client)

client.run(config['token'])
