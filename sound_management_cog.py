
import typing
import os
import pathlib
import traceback

import discord
from discord.ext import commands
import pydub
import yt_dlp


class SoundManagementCog(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot



    @commands.command()
    async def add_sound_attached(self,
                                 ctx,
                                 sound_name,
                                 sound_weight,
                                 attachment: typing.Optional[discord.Attachment],
                                 guild_identifier=None,
                                ):
        try:
            guild = self.__parse_guild(ctx, guild_identifier) 
            (sound_name, sound_weight) = self.__parse_sound_info(sound_name,
                                                                 sound_weight) 
        except Exception as e:
            print(e)
            traceback.print_exc()
            await ctx.reply(str(e))
            return

        if not attachment or 'audio' not in attachment.content_type:
            await ctx.reply('Must attach audio file')
            return


        file_path = pathlib.Path('./sounds/{}/{}/{}.mp3'.format(ctx.author.name,
                                                                guild.name,
                                                                sound_name,
                                                               ))

        extension = ''.join(pathlib.Path(attachment.filename).suffixes)
        work_path = pathlib.Path('./work/attachment{}'.format(extension))

        work_path.parent.mkdir(parents=True, exist_ok=True)
        await attachment.save(work_path)

        try:
            self.__process_sound(work_path, file_path, sound_weight)
            await ctx.reply('Successfully added sound {} to server {}'.format(
                                sound_name, guild.name))
        except Exception as e:
            await ctx.reply('Could not convert audio file: ' + str(e))
            print(e)
            raise


    @commands.command()
    async def add_sound_youtube(self,
                                ctx,
                                url,
                                start_time,
                                end_time,
                                sound_name,
                                sound_weight,
                                guild_identifier=None,
                               ):
        try:
            guild = self.__parse_guild(ctx, guild_identifier) 
            (sound_name, sound_weight) = self.__parse_sound_info(sound_name,
                                                                 sound_weight) 
            start_time = float(start_time)
            end_time = float(end_time)
        except Exception as e:
            print(e)
            traceback.print_exc()
            await ctx.reply(str(e))

        async with ctx.typing():
            try:
                yt_opts = {
                    'verbose': True,
                    'download_ranges': 
                        yt_dlp.utils.download_range_func(None, [(start_time,
                                                                 end_time)]),
                    'force_keyframes_at_cuts': True,
                    'format':'ba.2', #2nd best audio only format
                    'outtmpl':'work/youtube.%(ext)s',
                    'noplaylist':True,
                }


                with yt_dlp.YoutubeDL(yt_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=True)
                    work_path = pathlib.Path(ydl.prepare_filename(info_dict))


                file_path = pathlib.Path('./sounds/{}/{}/{}.mp3'.format(ctx.author.name,
                                                                        guild.name,
                                                                        sound_name,
                                                                       ))
                    
            except Exception as e:
                traceback.print_exc()
                print(e)


            try:
                self.__process_sound(work_path, file_path, sound_weight)
                await ctx.reply('Successfully added sound {} to server {}'.format(
                                    sound_name, guild.name))
            except Exception as e:
                await ctx.reply('Could not convert audio file: ' + str(e))
                print(e)
                raise



    @commands.command()
    async def delete_sound(self,
                           ctx,
                           sound_name,
                           guild_identifier=None):
        try:
            guild = self.__parse_guild(ctx, guild_identifier) 
            (sound_name, _) = self.__parse_sound_info(sound_name) 
        except Exception as e:
            print(e)
            traceback.print_exc()
            await ctx.reply(str(e))

        sound_path = (pathlib.Path('./sounds') /
                      ctx.author.name /
                      guild.name /
                      sound_name
                     ).with_suffix('.mp3')
        
        if not sound_path.is_file():
            await ctx.reply('Sound file does not exist')
        else:
            sound_path.unlink()
            await ctx.reply('Successfully deleted sound {} from server {}'.format(
                                sound_name, guild.name))


    @commands.command()
    async def list_servers(self, ctx):
        #List server names/ids of servers that are shared
        lines = (['Here is a list of our shared servers and their internal IDs'] +
                 ['name - id'] +
                 ['{} - {}'.format(g.name, g.id) for g in ctx.author.mutual_guilds])

        await ctx.reply('\n'.join(lines))


    @commands.command()
    async def list_sounds(self,
                          ctx,
                          guild_identifier=None):

        #If no guild info and in DM list all sounds
        if guild_identifier == None and ctx.guild == None:
            sounds_path = pathlib.Path('./sounds') / ctx.author.name
            lines = ['Here are your sounds for all servers']
        else:
            try:
                guild = self.__parse_guild(ctx, guild_identifier) 
            except Exception as e:
                print(e)
                traceback.print_exc()
                await ctx.reply(str(e))
                return
            sounds_path = pathlib.Path('./sounds') / ctx.author.name / guild.name
            lines = ['Here are your sounds for server "{}"'.format(guild.name)]

        lines += ['Server - Sound name']
        lines += [p.parent.name + ' - ' + p.stem
                    for p in filter(lambda p: p.is_file(),  #only take files
                                    sounds_path.rglob('*')) #from all nodes
                 ]

        await ctx.reply('\n'.join(lines))
        

    @commands.command()
    async def test_sound(self, ctx, sound_name, guild_identifier=None):
        try:
            guild = self.__parse_guild(ctx, guild_identifier) 
            (sound_name, _) = self.__parse_sound_info(sound_name) 
        except Exception as e:
            print(e)
            traceback.print_exc()
            await ctx.reply(str(e))

        if ctx.guild == None:
            sound_path = (pathlib.Path('./sounds') /
                          ctx.author.name /
                          guild.name /
                          sound_name
                         ).with_suffix('.mp3')
            try:
                file = discord.File(sound_path)
            except Exception as e:
                print(e)
            await ctx.reply(file=file, content='Here is {}'.format(sound_name))

    def __add_sound_common(self, arg):
        pass


    def __parse_guild(self, ctx, guild_identifier):
        if ctx.guild:
            guild = ctx.guild
        else:
            if not guild_identifier:
                error = 'No server specified'
                raise Exception(error)

            guild = None
            for g in ctx.author.mutual_guilds:
                if guild_identifier == g.name or guild_identifier == str(g.id):
                    guild = g
                    break

            if not guild:
                error = 'Invalid server specified'
                raise Exception(error)

        return guild


    def __parse_sound_info(self, sound_name, sound_weight='0'):
        sound_name = ''.join(filter(lambda p: str.isalnum(p) or p in '-_', sound_name))
        try:
            sound_weight = int(sound_weight)
        except ValueError as e:
            error = 'Sound weight must be an integer'
            raise Exception(error)

        return sound_name, sound_weight

    
    def __process_sound(self, sound_path, save_path, sound_weight):
        sound = pydub.AudioSegment.from_file(sound_path)

        speedup_factor = len(sound) / 5000.0

        if speedup_factor > 1:
            new_frame_rate = int(sound.frame_rate * speedup_factor)
            sound = sound._spawn(sound.raw_data,
                                 overrides={'frame_rate': new_frame_rate})
            sound = sound.set_frame_rate(44100)

        sound = sound.fade_in(250)
        sound = sound.fade_out(250)

        save_path.parent.mkdir(parents=True, exist_ok=True)
        sound.export(save_path, tags={'weight':sound_weight})
