
from discord.ext import commands

class MetaCog(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot

        @bot.event
        async def on_ready():
            assert bot.user is not None

            print(f'Logged in as {bot.user} (ID: {bot.user.id})')
            print('------')

