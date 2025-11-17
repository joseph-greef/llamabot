
import asyncio
import functools
import pathlib
import random

import discord
from discord.ext import commands
import pydub


class VoiceCog(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot

        @bot.event
        async def on_voice_state_update(member, before, after):
          try:
            #print(before)
            #print(after)


            #user entering a channel
            if after.channel and after.channel != before.channel:
                sounds = pathlib.Path('./sounds') / member.name / after.channel.guild.name
                if sounds.exists():
                    sound_choices = []
                    for sound in sounds.iterdir():
                        sound_choices += [sound] * int(pydub.utils.mediainfo(sound)['TAG']['weight'])
                    
                    sound_path = random.choice(sound_choices)
                    voice_client = await after.channel.connect()
                    source = discord.FFmpegPCMAudio(sound_path)
                    #source = discord.PCMVolumeTransformer(source)
                    after_func = functools.partial(self.post_sound_cleanup,
                                                   voice_client)
                    voice_client.play(source, after=after_func)

            
            #user exiting channel
            if before.channel and not after.channel:
                #if the bot is the only one left in the channel
                if (len(before.channel.members) == 1 and
                        before.channel.members[0].id == 1439452220700622878):
                    for voice_client in self.__bot.voice_clients:
                        if voice_client.channel == before.channel:
                            await voice_client.disconnect(force=False)



          except Exception as e:
            print(e)



    @commands.command()
    async def leave(self, ctx):
        await ctx.voice_client.disconnect()

    def post_sound_cleanup(self, voice_client, error):
        print(voice_client.source)
        try:
            fut = asyncio.run_coroutine_threadsafe(voice_client.disconnect(force=False),
                                                   self.__bot.loop)
            fut.result()
        except Exception as e:
            print(e)
            raise



