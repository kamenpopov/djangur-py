import time

from discord.player import FFmpegPCMAudio
from subprocess import run
import tempfile
from os import path

async def ping(*args, msg, client):
    await msg.channel.send('pong')

async def play(*args, msg, client):
    link = args[0]
    with tempfile.TemporaryDirectory() as tmpdir:
        file = path.join(tmpdir, 'audio.opus')
        run(['youtube-dl', '-x', '--audio-format', 'opus', link, '-o', file])

    channel = msg.author.voice.channel

    if channel != None:
        vc = await channel.connect()
        # player = await vc.FFmpegPCMAudio('a_nightmare.opus')
        # player.start()
        # while not player.is_done():
            # await time.sleep(1)
        # player.stop()

        vc.play(FFmpegPCMAudio('a_nightmare.mp3'))

        # await client.voice_client.disconnect()            
