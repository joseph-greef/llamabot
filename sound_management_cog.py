
import typing
import os
import pathlib
import traceback

import discord
from discord.ext import commands
import pydub
import yt_dlp


class SoundManagementCog(commands.Cog):
    MAX_SOUND_MS = 6000.0
    def __init__(self, bot):
        self.__bot = bot

    ########################
    # add_sound_attachment #
    ########################
    @commands.command(
        help="""This command adds an attached audio file to your sound list with the specified name and weight.

        If the audio file is longer than 6 seconds, it is sped up chipmunk style to meet the time limit. All files are given a 250ms fade in/fade out to prevent unintentional speaker clipping.

        If run in a server this command will add the sound to your list for that server, if run in DMs you must specify the server. See !list_servers for a list of valid servers.""",
        brief="""[name] [weight] [server]""",
        aliases=['asa'])
    async def add_sound_attached(self, ctx,
            sound_name=commands.parameter(
                description='A name for the sound, must be alphanumeric + "-" or "_"'),
            sound_weight=commands.parameter(
                description='Probability that this sound is chosen compared to the others'),
            attachment: typing.Optional[discord.Attachment]=commands.parameter(
                description='Audio file attached to the message'),
            guild_identifier=commands.parameter(default=None,
                description='Server name or server ID'),
           ):

        async with ctx.typing():
            if not attachment or 'audio' not in attachment.content_type:
                await ctx.reply('Must attach audio file')
                return

            extension = ''.join(pathlib.Path(attachment.filename).suffixes)
            work_path = pathlib.Path('./work/attachment{}'.format(extension))

            work_path.parent.mkdir(parents=True, exist_ok=True)
            await attachment.save(work_path)

            await ctx.reply(self.__add_sound_common(ctx,
                                                    sound_name,
                                                    sound_weight,
                                                    guild_identifier,
                                                    work_path))
            work_path.unlink()


    #####################
    # add_sound_youtube #
    #####################
    @commands.command(
        help="""This command downloads audio from a Youtube video and crops it to the given start and end time before adding it to your sound list with the specified name and weight.

        If the audio file is longer than 6 seconds, it is sped up chipmunk style to meet the time limit. All files are given a 250ms fade in/fade out to prevent unintentional speaker clipping.

        If run in a server this command will add the sound to your list for that server, if run in DMs you must specify the server. See !list_servers for a list of valid servers.""",
        brief="""[url] [start_time] [end_time] [name] [weight] [guild_identifier]""",
        aliases=['asy'])
    async def add_sound_youtube(self, ctx,
            url=commands.parameter(
                description='The youtube URL to download'),
            start_time=commands.parameter(
                description='Start timestamp of the clip in seconds, decimals allowed'),
            end_time=commands.parameter(
                description='End timestamp of the clip in seconds, decimals allowed'),
            sound_name=commands.parameter(
                 description='A name for the sound, must be alphanumeric + "-" or "_"'),
            sound_weight=commands.parameter(
                 description='Probability that this sound is chosen compared to others'),
            guild_identifier=commands.parameter(default=None,
                 description='Server name or server ID'),
           ):

        try:
            start_time = float(start_time)
            end_time = float(end_time)
            if end_time <= start_time:
                raise Exception('End time before start time')
        except Exception as e:
            await ctx.reply('Start/end time invalid: ' + str(e))
            return

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

                await ctx.reply(self.__add_sound_common(ctx,
                                                        sound_name,
                                                        sound_weight,
                                                        guild_identifier,
                                                        work_path))
                work_path.unlink()

            except Exception as e:
                print(e)
                traceback.print_exc()
                await ctx.reply(str(e))

    ################
    # delete_sound #
    ################
    @commands.command(
        help="""This command deletes the specified command from your sound list

        If run in a server this command will add the sound to your list for that server, if run in DMs you must specify the server. See !list_servers for a list of valid servers.""",
        brief="""[sound_name] [guild_identifier]""",
        aliases=['ds'])
    async def delete_sound(self, ctx,
            sound_name=commands.parameter(
                description='The sound to delete, must be alphanumeric + "-" or "_"'),
            guild_identifier=commands.parameter(default=None,
                description='Server name or server ID'),
           ):
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


    ################
    # list_servers #
    ################
    @commands.command(
        help="""This command lists your mutual servers with llamabot and their IDs. These are the valid options for the guild_identifier arguments.""",
        brief="""No arguments""",
        aliases=['lsrv'])
    async def list_servers(self, ctx):
        #List server names/ids of servers that are shared
        lines = (['Here is a list of our shared servers and their internal IDs'] +
                 ['name - id'] +
                 ['{} - {}'.format(g.name, g.id) for g in ctx.author.mutual_guilds])

        await ctx.reply('\n'.join(lines))

    ###############
    # list_sounds #
    ###############
    @commands.command(
        help="""This command lists your registered sounds.

        If you give it a guild identifer it will show you the sounds for that guild, otherwise it will show you all of your sound lists.""",
        brief="""[guild_identifier]""",
        aliases=['lsnd'])
    async def list_sounds(self, ctx,
                          guild_identifier=commands.parameter(default=None,
                              description='Server name or server ID'),
                         ):
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


    ##############
    # test_sound #
    ##############
    @commands.command(
        help="""This command triggers the bot to send you a copy of one of your sound files for listening/testing.

        This command only works in DMs.""",
        brief="""[sound_name] [guild_identifier]""",
        aliases=['ts'])
    async def test_sound(self, ctx,
            sound_name=commands.parameter(
                description='The sound to test, must be alphanumeric + "-" or "_"'),
            guild_identifier=commands.parameter(default=None,
                description='Server name or server ID'),
           ):
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


    def __add_sound_common(self,
                           ctx,
                           sound_name,
                           sound_weight,
                           guild_identifier,
                           work_path,
                          ):
        try:
            guild = self.__parse_guild(ctx, guild_identifier)
            (sound_name, sound_weight) = self.__parse_sound_info(sound_name,
                                                                 sound_weight)
        except Exception as e:
            return str(e)

        file_path = pathlib.Path('./sounds/{}/{}/{}.mp3'.format(ctx.author.name,
                                                                guild.name,
                                                                sound_name,
                                                               ))

        try:
            self.__process_sound(work_path, file_path, sound_weight)
            return 'Successfully added sound {} to server {}'.format(
                        sound_name, guild.name)
        except Exception as e:
            return 'Could not convert audio file: ' + str(e)


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

        speedup_factor = len(sound) / self.MAX_SOUND_MS

        if speedup_factor > 1:
            new_frame_rate = int(sound.frame_rate * speedup_factor)
            sound = sound._spawn(sound.raw_data,
                                 overrides={'frame_rate': new_frame_rate})

        #discord takes in 48kHz sound, so preprocess sound files to match
        sound = sound.set_frame_rate(48000)
        sound = sound.set_channels(2)
        sound = sound.set_sample_width(2)
        sound = sound.fade_in(250)
        sound = sound.fade_out(250)
        sound = pydub.effects.normalize(sound)

        save_path.parent.mkdir(parents=True, exist_ok=True)
        sound.export(save_path, tags={'weight':sound_weight})
