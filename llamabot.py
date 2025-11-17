
import asyncio
import logging
import os

import discord
from discord.ext import commands
import dotenv

import sound_management_cog
import meta_cog
import voice_cog


async def bot_loop(bot, token):
    async with bot:
        await bot.add_cog(sound_management_cog.SoundManagementCog(bot))
        await bot.add_cog(meta_cog.MetaCog(bot))
        await bot.add_cog(voice_cog.VoiceCog(bot))
        await bot.start(token)


def main():
    if not dotenv.load_dotenv():
        print('You must create and populate a .env file')

    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)

    discord_token = os.getenv('DISCORD_TOKEN')

    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    intents.voice_states = True
    bot = commands.Bot(
        command_prefix=commands.when_mentioned_or('!'),
        intents=intents,
    )

    asyncio.run(bot_loop(bot, discord_token))


if __name__ == '__main__':
    main()
