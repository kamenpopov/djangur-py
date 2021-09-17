import time

from discord.player import FFmpegPCMAudio

async def ping(*args, msg, client):
    await msg.channel.send('pong')

async def play(*args, msg, client):
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