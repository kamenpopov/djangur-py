import time
from discord.player import FFmpegPCMAudio
from discord import Embed
from subprocess import run
import tempfile
from os import path
import youtube_dl

class Commands():
    command_map = {}

    def add(alias=None):
        def wrap(f):
            Commands.command_map[f.__name__] = f
            if alias != None:
                Commands.command_map[alias] = f
        return wrap


class Song:
    def __init__(self, url, title=None, description=None, thumbnail=None):
        self.url = url
        self.title = title
        self.description = description
        self.thumbnail= thumbnail

    @staticmethod
    def from_youtube(query):
        ytdl_options = {
            'format': 'bestaudio',
            'prefer_ffmpeg': True,
        }
        with youtube_dl.YoutubeDL(ytdl_options) as ytdl:
            search = ytdl.extract_info(f'ytsearch:{query}', False)
            video = search['entries'][0]
            return Song(video['formats'][0]['url'], video['title'], video['description'], video['thumbnail'])

    @staticmethod
    def from_url(url):
        with youtube_dl.YoutubeDL() as ytdl:
            video = ytdl.extract_info(url, False)
            print(video)
            return Song(
                    video['url'],
                    video['title'] if 'title' in video else None,
                    video['description'] if 'description' in video else None,
                    video['thumbnail'] if 'thumbnail' in video else None)


class Guild_Instance():
    def __init__(self, vc=None):
        self.vc = vc
        self.tc = None
        self.queue = []

    async def connect(self, channel):
        if channel is None:
            return

        if self.vc is None:
            self.vc = await channel.connect()
        elif channel.id != self.vc.channel.id:
            await self.vc.disconnect()
            self.vc = await channel.connect()

    async def enqueue(self, song):
        embed = Embed(title=song.title, description=song.description, color=0x00ffff)
        if song.thumbnail is not None:
            embed.set_thumbnail(url=song.thumbnail)
        await self.tc.send(embed=embed)

        self.queue.append(song)

    def dequeue(self):
        self.queue.pop(0)

    def play(self, song, after=None):
        ffmpeg_before_options = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 2'
        self.vc.play(FFmpegPCMAudio(song.url, before_options=ffmpeg_before_options), after=after)

    def play_next(self):
        if len(self.queue) == 0:
            return
        self.play(self.queue[0], after=lambda e: self.play_next())
        self.dequeue()


guild_instances = {}


# @Commands.add
@Commands.add()
async def ping(*args, msg, client):
    await msg.channel.send('pong')


@Commands.add(alias='p')
async def play(*args, msg, client):
    global guild_instances
    if msg.guild.id not in guild_instances:
        guild_instances[msg.guild.id] = Guild_Instance()
    ginst = guild_instances[msg.guild.id]

    ginst.tc = msg.channel
    await ginst.connect(msg.author.voice.channel)

    if len(args) == 0:
        if ginst.vc.is_paused():
            ginst.vc.resume()
    else:
        query = ' '.join(args)
        if query.startswith('https:'):
            song = Song.from_url(query)
        else:
            song = Song.from_youtube(query)

        await ginst.enqueue(song)
        if not ginst.vc.is_playing():
            ginst.play_next()

@Commands.add(alias='s')
async def stop(*args, msg, client):
    global guild_instances
    if msg.guild.id not in guild_instances:
        guild_instances[msg.guild.id] = Guild_Instance()
    ginst = guild_instances[msg.guild.id]

    if ginst.vc.is_playing():
        ginst.vc.stop()

@Commands.add()
async def pause(*args, msg, client):
    global guild_instances
    if msg.guild.id not in guild_instances:
        guild_instances[msg.guild.id] = Guild_Instance()
    ginst = guild_instances[msg.guild.id]

    if ginst.vc.is_playing():
        ginst.vc.pause()

@Commands.add()
async def resume(*args, msg, client):
    global guild_instances
    if msg.guild.id not in guild_instances:
        guild_instances[msg.guild.id] = Guild_Instance()
    ginst = guild_instances[msg.guild.id]
    
    if ginst.vc.is_paused():
        ginst.vc.resume()