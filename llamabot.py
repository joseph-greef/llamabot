#!/usr/bin/python

import asyncio
import os

import discord
from discord.ext import commands
import dotenv

import sound_management_cog

dotenv.load_dotenv()
discord_token = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or('!'),
    intents=intents,
)

@bot.event
async def on_ready():
    assert bot.user is not None

    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


async def main():
    async with bot:
        await bot.add_cog(sound_management_cog.SoundManagementCog(bot))
        await bot.start(discord_token)

asyncio.run(main())
