import time
from discord.player import FFmpegPCMAudio
from subprocess import run
import tempfile
from os import path

class Guild_Instance():
    def __init__(self, vc=None):
        self.vc = vc


    async def connect(self, channel):
        if channel is None:
            return

        if self.vc is None:
            self.vc = await channel.connect()
        elif channel.id != self.vc.channel.id:
            await self.vc.disconnect()
            self.vc = await channel.connect()


guild_instances = {}


async def ping(*args, msg, client):
    await msg.channel.send('pong')


async def play(*args, msg, client):
    global guild_instances

    if msg.guild.id not in guild_instances:
        guild_instances[msg.guild.id] = Guild_Instance()
    ginstance = guild_instances[msg.guild.id]

    await ginstance.connect(msg.author.voice.channel)

    link = ' '.join(args)

    tmpdir = tempfile.TemporaryDirectory()
    file = path.join(tmpdir.name, 'audio.opus')
    run(['youtube-dl', '-x', '--audio-format', 'opus', '--default-search', 'ytsearch', link, '-o', file])

    print(f'"{link}" downloaded!')

    ginstance.vc.play(FFmpegPCMAudio(file), after=lambda e: tmpdir.cleanup())
