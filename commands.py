import time
from discord.player import FFmpegPCMAudio, PCMVolumeTransformer
from discord import Embed
from subprocess import run
import tempfile
from os import path
from pymongo.collection import Collection
import youtube_dl
from contextlib import redirect_stdout
import datetime


class Commands():
    command_map = {}

    def add(alias=None):
        def wrap(f):
            Commands.command_map[f.__name__] = f
            if alias != None:
                Commands.command_map[alias] = f
        return wrap


class Song:
    def __init__(self, url, title=None, description=None, thumbnail=None, duration=None, v_id=None, played_by=None):
        self.url = url
        self.title = title
        self.description = description
        self.thumbnail= thumbnail
        self.duration = duration
        self.v_id = v_id
        self.played_by = played_by

    @staticmethod
    def from_youtube(query, played_by):
        ytdl_options = {
            'format': 'bestaudio',
            'prefer_ffmpeg': True,
        }
        with youtube_dl.YoutubeDL(ytdl_options) as ytdl:
            search = ytdl.extract_info(f'ytsearch:{query}', False)
            video = search['entries'][0]
            return Song(video['formats'][0]['url'], video['title'], video['description'], video['thumbnail'], video['duration'], video['id'], played_by)

    @staticmethod
    def from_url(url, played_by):
        with youtube_dl.YoutubeDL() as ytdl:
            video = ytdl.extract_info(url, False)
            url = None
            if 'formats' in video:
                url = video['formats'][0]['url']
            elif 'url' in video:
                url = video['url']
            return Song(
                    url,
                    video['title'] if 'title' in video else None,
                    video['description'] if 'description' in video else None,
                    video['thumbnail'] if 'thumbnail' in video else None,
                    video['duration'] if 'duration' in video else None,
                    video['id'] if 'id' in video else None,
                    played_by)


class Guild_Instance():
    _instances = {}

    @staticmethod
    def by_id(id):
        if id not in Guild_Instance._instances:
            Guild_Instance._instances[id] = Guild_Instance()
        return Guild_Instance._instances[id]

    def __init__(self):
        self.vc = None
        self.tc = None
        self.db = Collection
        self.audio_source = None
        self.queue = []
        self.searching = False
        self.song_search = []
        self.now_playing = Song(NotImplemented)
        self.time_playing = time.time()

    async def connect(self, channel):
        if channel is None:
            return

        if self.vc is None:
            self.vc = await channel.connect()
        elif channel.id != self.vc.channel.id:
            await self.vc.disconnect()
            self.vc = await channel.connect()

    async def enqueue(self, song):
        url = ''
        if song.v_id != None and song.duration != None:
            url = f'https://www.youtube.com/watch?v={song.v_id}'

        embed = Embed(title=song.title, description=song.description, url=f'{url}', color=0x00ffff)
        if song.thumbnail is not None:
            embed.set_thumbnail(url=song.thumbnail)
        await self.tc.send(embed=embed)

        self.queue.append(song)

    def dequeue(self):
        self.queue.pop(0)

    def play(self, song, after=None):
        ffmpeg_before_options = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 2'
        # self.tc.send(f'Now playing: {song.title}')
        self.audio_source = FFmpegPCMAudio(song.url, before_options=ffmpeg_before_options)

        self.vc.play(self.audio_source, after=after)
        self.audio_source = PCMVolumeTransformer(self.audio_source, 1)

        self.db_update(song)

    def play_next(self):
        self.now_playing = Song(NotImplemented)
        if len(self.queue) == 0:
            return
        self.play(self.queue[0], after=lambda e: self.play_next())
        self.now_playing = self.queue[0]
        self.time_playing = time.time()
        self.dequeue()

    def db_update(self, song):
        print(self.db.update_one({'_id': song.title}, {'$inc': {f'requested_by.{song.played_by}': 1, 'requested_by.total_plays': 1}}, upsert=True).raw_result)


#TODO Figure out a more clever way to do this
async def play_search(id, msg, client, ginst):

    ginst.searching = False
    await ginst.connect(msg.author.voice.channel)
    id_r = int(id) - 1

    query = ginst.song_search[int(id_r)]
    song = Song.from_youtube(query, msg.author.name)

    await ginst.enqueue(song)
    if not ginst.vc.is_playing():
        ginst.play_next()

@Commands.add()
async def ping(args, msg, client, ginst):
    await ginst.tc.send('pong')
@Commands.add()
async def np(args, msg, client, ginst):
    now_playing_title = ginst.now_playing.title
    if (now_playing_title == None):
        embed = Embed(title='Not playing anything!', description='Use command play to add a song!')
        await msg.channel.send(embed=embed);
        return
    if (ginst.now_playing.duration == None):
        embed = Embed(title=f'Now playing: {now_playing_title}')
        await msg.channel.send(embed=embed);
        return
    timestamp = (time.time() - ginst.time_playing)
    display_timestamp = round((timestamp / ginst.now_playing.duration) * 30)
    display_timestamp_emoji = ''
    for emoji in range(30):
        if emoji == display_timestamp:
            display_timestamp_emoji += '🔴'
        else:
            display_timestamp_emoji += '▬'
    timestamp = str(datetime.timedelta(seconds=timestamp))[:-7]
    video_timestamp = str(datetime.timedelta(seconds=ginst.now_playing.duration))
    url = ''
    if ginst.now_playing.v_id != None:
        url = f'https://www.youtube.com/watch?v={ginst.now_playing.v_id}'
    embed = Embed(title=f'{now_playing_title}', url=url)
    embed.add_field(name=f'```{display_timestamp_emoji}\n```', value=f'```{timestamp}/{video_timestamp}```')
    embed.set_thumbnail(url=ginst.now_playing.thumbnail)
    await msg.channel.send(embed=embed)
@Commands.add()
async def search(args, msg, client, ginst):

    ginst.song_search = []
    search = args
    with youtube_dl.YoutubeDL() as ytdl:
        search_results = ytdl.extract_info(f"ytsearch10:{search}", download=False)['entries']
    search_str = ""
    for index, video in enumerate(search_results):
        search_str += f"{index + 1} - {video['title']}\n"
        ginst.song_search.append(video['id'])
    results_embed = Embed(title=f'Search results for {search}')
    results_embed.add_field(name='Results:', value=search_str)
    await ginst.tc.send(embed=results_embed)
    ginst.searching = True

@Commands.add(alias='p')
async def play(args, msg, client, ginst):

    await ginst.connect(msg.author.voice.channel)

    if len(args) == 0:
        if ginst.vc.is_paused():
            ginst.vc.resume()
    else:
        query = args
        if query.startswith('https:'):
            song = Song.from_url(query, msg.author.name)
        else:
            song = Song.from_youtube(query, msg.author.name)
        await ginst.enqueue(song)
        if not ginst.vc.is_playing():
            ginst.play_next()

@Commands.add(alias='s')
async def skip(args, msg, client, ginst):

    if ginst.vc.is_playing():
        ginst.vc.stop()

@Commands.add()
async def pause(args, msg, client, ginst):

    if ginst.vc.is_playing():
        ginst.vc.pause()

@Commands.add()
async def resume(args, msg, client, ginst):
    if ginst.vc.is_paused():
        ginst.vc.resume()

@Commands.add(alias='q')
async def queue(args, msg, client, ginst):
    queue_str = ""
    if (args == 'clear'):
        ginst.queue = []
        return
    if len(ginst.queue) == 0:
        queue_embed = Embed(title='Queue is empty!', description='Use command play to add a song!')
        await ginst.tc.send(embed=queue_embed)
    else:
        for i in range(len(ginst.queue)):
            queue_str += f"{i+ 1} - {ginst.queue[i].title}\n"
        queue_embed = Embed(title='Song queue')
        queue_embed.add_field(name="Songs:", value=queue_str)
        await ginst.tc.send(embed=queue_embed)

@Commands.add()
async def leave(args, msg, client, ginst):
    await ginst.vc.disconnect()
    ginst.vc = None
    ginst.queue = []
    ginst.time_playing = time.time()
