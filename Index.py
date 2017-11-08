import discord
import asyncio
import Actions
import Music
import atexit
from discord.ext import commands

"""
The main class that handles running the bot and its methods
"""

# Creates a bot object and adds the classes that handle user input (cogs)
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), description="yes")
bot.add_cog(Music.Music(bot))
bot.add_cog(Actions.Action(bot))


@bot.event
@asyncio.coroutine
def on_ready():
    # Sets the status of the bot (visible to users)
    game = discord.Game()
    game.name = "Music"
    yield from bot.change_status(game)


print("Bot Starting...")

# Requires own key, runs the bot
bot.run("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")


# Handles safe closing of the bot
def exit_handler():
    bot.logout()
    bot.close()


atexit.register(exit_handler)

"""
Packages required for usaged
pip3
Discord.py[voice]
libxml2-dev
libxslt1-dev
libffi-dev
libopus-dev

pip install youtube_dl

find a better way to install ffmpeg
***Might be able to directly install ffmpeg on the ubuntu server now??***
sudo add-apt-reposstory ppa:mcman/trusty-media
suo apt-get update
sudo apt-get install ffmpeg gstreamer0.10-ffmpeg
"""
