
import asyncio
import functools
import pathlib
import random
import traceback

import discord
from discord.ext import commands
import pydub

import mixed_audio


class VoiceCog(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__upcoming_duties = {}

        @bot.event
        async def on_voice_state_update(member, before, after):
          try:
            #Do not do anything for our own events
            if member.id == 1439452220700622878:
                return

            #options for when a user joins a channel:
            #   * Bot not in any channel - join the channel and play a sound
            #   * Bot already in the channel - add the sound to the source
            #   * Bot in a another channel - queue up join noises for the new channel

            #user entering a channel
            if after.channel and after.channel != before.channel:
                guild = member.guild
                channel = after.channel
                sound_path = self.__get_sound_path(member.name, guild)
                if sound_path:
                    voice_client = self.__get_voice_client_by_guild(guild)
                    #bot not in any channel here
                    if not voice_client:
                        #connect to the channel and start playing a sound
                        voice_client = await channel.connect()
                        source = mixed_audio.MixedAudio(sound_path)
                        after = functools.partial(self.__post_sound_cleanup,
                                                  voice_client)
                        voice_client.play(source, after=after)
                    #bot already in this channel
                    elif voice_client.channel == channel:
                        voice_client.source.add_sound(sound_path) 
                    #bot in another channel
                    else:
                        if guild not in self.__upcoming_duties:
                            self.__upcoming_duties[guild] = {}
                        if channel in self.__upcoming_duties[guild]:
                            self.__upcoming_duties[guild][channel].append(sound_path)
                        else:
                            self.__upcoming_duties[guild][channel] = [sound_path]

          except Exception as e:
            print(e)


    @commands.command()
    async def leave(self, ctx):
        await ctx.voice_client.disconnect()


    async def __play_next_channel_intros(self, voice_client, channel, sounds):
        await voice_client.move_to(channel)

        source = mixed_audio.MixedAudio(sounds[0])
        for sound in sounds[1:]:
            source.add_sound(sound)

        after = functools.partial(self.__post_sound_cleanup,
                                  voice_client)
        voice_client.play(source, after=after)


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
        try:
            if (voice_client.guild not in self.__upcoming_duties or
                    not self.__upcoming_duties[voice_client.guild]):
                fut = asyncio.run_coroutine_threadsafe(
                            voice_client.disconnect(force=False),
                            self.__bot.loop)
            else:
                channel, sounds = self.__upcoming_duties[voice_client.guild].popitem()
                fut = asyncio.run_coroutine_threadsafe(
                            self.__play_next_channel_intros(voice_client,
                                                            channel,
                                                            sounds),
                            self.__bot.loop)
            fut.result()

        except Exception as e:
            traceback.print_exc()
            print(e)
            raise



