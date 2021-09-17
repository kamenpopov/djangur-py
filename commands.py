import time
from discord.player import FFmpegPCMAudio
from subprocess import run
import tempfile
from os import path

async def ping(*args, msg, client):
    await msg.channel.send('pong')

async def play(*args, msg, client):
    channel = msg.author.voice.channel
    if channel == None:
        return

    link = ' '.join(args)

    tmpdir = tempfile.TemporaryDirectory()
    file = path.join(tmpdir.name, 'audio.opus')
    run(['youtube-dl', '-x', '--audio-format', 'opus', '--default-search', 'ytsearch', link, '-o', file])

    print(f'"{link}" downloaded!')

    vc = await channel.connect()
    vc.play(FFmpegPCMAudio(file), after=lambda e: tmpdir.cleanup())
