import time

from discord.player import FFmpegPCMAudio
from subprocess import run
import tempfile
from os import path

async def ping(*args, msg, client):
    await msg.channel.send('pong')

async def play(*args, msg, client):
    def track_end(error):
        if error != None:
            print(error)
        else:
            print("Finished track")


    channel = msg.author.voice.channel

    link = args[0]
    from os import listdir
    # with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = tempfile.TemporaryDirectory()
    file = path.join(tmpdir.name, 'audio.opus')
    run(['youtube-dl', '-x', '--audio-format', 'opus', link, '-o', file])


    if channel != None:
        vc = await channel.connect()

        vc.play(FFmpegPCMAudio(file), after=lambda e: tmpdir.cleanup())



        
