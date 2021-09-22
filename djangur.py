import discord
from commands import Commands, Guild_Instance, play_search
import json

from os import listdir, getcwd
print(listdir())
print(getcwd())

print([os.path.join(dp, f) for dp, dn, fn in os.walk(os.path.expanduser("~/files")) for f in fn])


with open('config.json') as f:
    config = json.load(f)

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

    if not msg.content.startswith(config['prefix']):
        return

    no_prefix = msg.content[len(config['prefix']):]
    split = no_prefix.split(' ', 1)
    cmd = split[0]
    args = split[1] if (len(split) == 2) else ''

    if cmd in Commands.command_map:
        await Commands.command_map[cmd](args, msg=msg, client=client, ginst=ginst)
    else:
        await msg.channel.send(f'{cmd}: Command not found.')

client.run(config['token'])
