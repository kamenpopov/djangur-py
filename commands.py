import time
from discord.player import FFmpegPCMAudio, PCMVolumeTransformer
from discord import Embed
import youtube_dl
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
        self.db = None
        self.loop = 0
        self.queue = []
        self.loop_index = 0
        self.song_search = []
        self.searching = False
        self.audio_source = None
        self.time_playing = time.time()
        self.now_playing = None
        self.timestamp = 0

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
        desc = (song.description[:500] + '...') if len(song.description) > 500 else song.description
        embed = Embed(title=song.title, description=desc, url=f'{url}', color=0x00ffff)
        dur = str(datetime.timedelta(seconds=song.duration))
        play_count = self.db.find_one({'_id': song.title})
        if play_count is not None:
            play_count = play_count['total_plays']
            msg = f'This song has been played {play_count} times before!'
        else:
            msg = 'You are playing this for the first time!'
        embed.set_footer(text=f'Duration: {dur}\n{msg}') 
        if song.thumbnail is not None:
            embed.set_thumbnail(url=song.thumbnail)
        await self.tc.send(embed=embed)
        self.queue.append(song)

    def dequeue(self):
        self.queue.pop(0)

    def play(self, song, after=None):
        ffmpeg_before_options = f'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 2 -ss {self.timestamp}'
        # self.tc.send(f'Now playing: {song.title}')
        self.audio_source = FFmpegPCMAudio(song.url, before_options=ffmpeg_before_options)

        self.vc.play(self.audio_source, after=after)
        self.audio_source = PCMVolumeTransformer(self.audio_source, 1)

        self.now_playing = song
        if self.timestamp == 0:
            self.db_update(song)
            self.time_playing = time.time()
        
    def after_play(self):
        if self.loop == 2 and self.loop_index <= len(self.queue)-1:
            self.loop_index += 1
            self.play_next()
        elif self.loop_index == len(self.queue):
            self.loop_index = 1
            self.play_next()
        elif self.loop == 0:
            self.loop_index = 0
            self.play_next()
            self.dequeue()
        else:
            self.loop_index = 0
            self.play_next()

    def play_next(self):
        if self.loop == 0:
            self.now_playing = None
            if len(self.queue) == 0:
                return
            self.play(self.queue[0], after=lambda e: self.after_play())
            self.now_playing = self.queue[0]
            # self.dequeue()
        elif self.loop == 1:
            self.play(self.now_playing, after=lambda e: self.after_play())
            if self.timestamp != 0:
                self.dequeue()
        elif self.loop == 2:
            print(self.loop_index)
            print(len(self.queue))
            self.play(self.queue[self.loop_index-1], after=lambda e: self.after_play())
            print(self.queue)
        self.timestamp = 0

    def db_update(self, song):
        self.db.update_one({'_id': song.title}, {'$inc': {f'requested_by.{song.played_by}': 1, 'total_plays': 1}}, upsert=True)


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
    if (ginst.now_playing == None):
        embed = Embed(title='Not playing anything!', description='Use command play to add a song!')
        await ginst.tc.send(embed=embed);
        return
    if (ginst.now_playing.duration == None):
        embed = Embed(title=f'Now playing: {now_playing_title}')
        await ginst.tc.send(embed=embed);
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
    await ginst.tc.send(embed=embed)
@Commands.add()
async def seek(args, msg, client, ginst):
    if ginst.now_playing == None:
        embed = Embed(title='Not playing anything!', description='Use command play to add a song!')
        await ginst.tc.send(embed=embed);
        return
    if args.count(':') > 3:
        embed = Embed(title='Invalid argument!')
        await ginst.tc.send(embed=embed);
        return
    timestamp = args.split(':')
    if 2 > len(timestamp):
        timestamp.insert(0, 0)
    if 3 > len(timestamp):
        timestamp.insert(0, 0)
    def switch(x):
        switcher = {
            3: int(timestamp[0]) * 1200 + (int(timestamp[1])) * 60 + int(timestamp[2]),
            2: int(timestamp[0]) * 60 + int(timestamp[1]),
            1: int(timestamp[0]),
        }
        return switcher.get(x, 0)
    timestamp_seconds = switch(len(timestamp))
    if timestamp_seconds < 0 or timestamp_seconds > ginst.now_playing.duration:
        embed = Embed(title='Invalid timestamp!')
        await ginst.tc.send(embed=embed);
        return
    ginst.timestamp = timestamp_seconds
    ginst.time_playing = time.time() - timestamp_seconds
    ginst.queue.insert(0, ginst.now_playing)
    ginst.vc.stop()
    await ginst.tc.send(f'⏩Set position to `{args}`')
    ginst.loop_index -= 1
    ginst.queue.pop(0)
    
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

    if msg.author.voice is not None:
        await ginst.connect(msg.author.voice.channel)
    else:
        await ginst.tc.send('Join a voice channel to use this command!')
        return

    if len(args) == 0:
        if ginst.vc.is_paused():
            ginst.vc.resume()
    else:
        if ginst.loop_index == 0:
            ginst.loop_index += 1
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

@Commands.add()
async def clear(args, msg, client, ginst):
    ginst.queue = []
    await ginst.tc.send("Cleared queue!")

@Commands.add(alias='q')
async def queue(args, msg, client, ginst):
    queue_str = ""
    if (args == 'clear'):
        ginst.queue = []
        await ginst.tc.send("Cleared queue!")
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
    ginst.loop_index = 1
    ginst.time_playing = time.time()

@Commands.add()
async def stats(args, msg, client, ginst):
    most_played = ginst.db.find_one(sort=[('total_plays', -1)])
    embed = Embed(title="Most Played Song")
    embed.add_field(name="Title: ", value=most_played['_id'], inline=False)
    embed.add_field(name="Count: ", value=most_played['total_plays'], inline=False)
    await ginst.tc.send(embed=embed)

@Commands.add()
async def loop(args, msg, client, ginst):
    # 0 -> no loop; 1 -> loop current; 2 -> loop queue; 
    if ginst.loop == 0:
        ginst.loop = 1
        await ginst.tc.send("🔂 Looping current track!")
    elif ginst.loop == 1:
        ginst.loop = 2
        await ginst.tc.send("🔁 Looping current queue!")
    elif ginst.loop == 2:
        ginst.loop = 0
        await ginst.tc.send("❌ Disabled looping!")

@Commands.add(alias='r')
async def remove(args, msg, client, ginst):
    if len(ginst.queue) == 0:
        queue_embed = Embed(title='Queue is empty!', description='Use command play to add a song!')
        await ginst.tc.send(embed=queue_embed)
        return
    args = int(args)
    if args > len(ginst.queue) or args <= 0:
        await ginst.tc.send("Invalid remove index!")
    else: 
        song = ginst.queue[args-1]   
        ginst.queue.pop(args-1)
        await ginst.tc.send(f"❎ Removed {song.title}!")