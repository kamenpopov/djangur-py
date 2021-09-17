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
        # PLAY FILE HERE
