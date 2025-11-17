
import asyncio
import functools
import pathlib
import random
import traceback

import discord
from discord.ext import commands
import pydub


class VoiceCog(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot

        @bot.event
        async def on_voice_state_update(member, before, after):
          try:
            #Do not do anything for our own events
            if member.id == 1439452220700622878:
                return
            #print(before)
            #print(after)

            #options for when a user joins a channel:
            #   * Bot not in any channel - join the channel and play a sound
            #   * Bot already in the channel - add the sound to the source
            #   * Bot in a another channel - queue up join noises for the new channel

            #user entering a channel
            if after.channel and after.channel != before.channel:
                sound_path = self.__get_sound_path(member.name, member.guild)
                if sound_path:
                    voice_client = self.__get_voice_client_by_guild(member.guild)
                    #bot not in any channel here
                    if not voice_client:
                        #connect to the channel and start playing a sound
                        voice_client = await after.channel.connect()
                        source = discord.FFmpegPCMAudio(sound_path)
                        #source = discord.PCMVolumeTransformer(source)
                        after_func = functools.partial(self.__post_sound_cleanup,
                                                       voice_client)
                        voice_client.play(source, after=after_func)
                    #bot already in this channel
                    elif voice_client.channel == after.channel:
                        #Add the sound to the audio mixer
                        pass
                    #bot in another channel
                    else:
                        #TODO: Make a queue for it to to play sounds on another channel
                        pass

            
            #user exiting channel
            if False and before.channel and not after.channel:
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

    def __get_sound_path(self, name, guild):
        try:
            sounds = pathlib.Path('./sounds') / name / guild.name
            if sounds.exists():
                sound_choices = []
                for sound in sounds.iterdir():
                    weight = int(pydub.utils.mediainfo(sound)['TAG']['weight'])
                    sound_choices += [sound] * weight
                return random.choice(sound_choices)

        except Exception as e:
            traceback.print_exc()
            print('gsp: {}'.format(e))

        return None

    def __get_voice_client_by_guild(self, guild):
        for voice_client in self.__bot.voice_clients:
            if voice_client.guild == guild:
                return voice_client
        return None

    def __post_sound_cleanup(self, voice_client, error):
        print(voice_client.source)
        try:
            fut = asyncio.run_coroutine_threadsafe(voice_client.disconnect(force=False),
                                                   self.__bot.loop)
            fut.result()
        except Exception as e:
            print(e)
            raise



