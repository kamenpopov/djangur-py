import time
from discord.player import FFmpegPCMAudio
from discord import Embed
from subprocess import run
import tempfile
from os import path
import youtube_dl

class Commands():
    command_map = {}
    @staticmethod
    def add(f):
        Commands.command_map[f.__name__] = f
        return f

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


@Commands.add
async def ping(*args, msg, client):
    await msg.channel.send('pong')


@Commands.add
async def play(*args, msg, client):
    global guild_instances

    if msg.guild.id not in guild_instances:
        guild_instances[msg.guild.id] = Guild_Instance()
    ginstance = guild_instances[msg.guild.id]

    await ginstance.connect(msg.author.voice.channel)

    link = ' '.join(args)

    ytdl_options = {
        'format': 'bestaudio'
    }

    with youtube_dl.YoutubeDL(ytdl_options) as ytdl:
        search = ytdl.extract_info(f'ytsearch:{link}', False)

        print(search['entries'][0])

        embed = Embed(title="Gosho", description="SEXY SEX WITH MY COCK AND YOUR BUSSY", color=0x00ffff)
        await msg.channel.send(embed=embed)


    ginstance.vc.play(FFmpegPCMAudio(search['entries'][0]['formats'][0]['url']), after=lambda e: print("krai"))
