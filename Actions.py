import discord
import asyncio
import random
import lists

from bs4 import BeautifulSoup
from urllib.request import urlopen
from discord.ext import commands

client = discord.Client()

"""
A class that handles all non-music related commands issued by the users of the bot
"""


class Action:
    
    def __init__(self, bot):  # Constructor
        print("Bot Started...")
        self.bot = bot

    @commands.command(pass_context=True, no_pm=True)
    @asyncio.coroutine
    def tester(self, context):  # Basic Test to check bot can receive and respond to commands
        author = context.message.author
        yield from self.bot.say("%s requested a test!" % author)

    # Returns a random value from a list from the Lists file
    @commands.command(pass_context=True, no_pm=True)
    @asyncio.coroutine
    def heist(self, context):
        author = context.message.author
        yield from self.bot.say("%s requested a heist!" % author)
        yield from self.bot.say("Time to play: %s" % random.choice(lists.heists))

    # Returns a random value from a subset of heists list
    @commands.command(pass_context=True, no_pm=True)
    @asyncio.coroutine
    def loud(self, context):
        author = context.message.author
        yield from self.bot.say("%s Requested a Loud heist!" % author)
        yield from self.bot.say("Time to play: %s" % random.choice(lists.loud))

    # Returns a random value from a subset of heists list
    @commands.command(pass_context=True, no_pm=True)
    @asyncio.coroutine
    def quiet(self, context):
        author = context.message.author
        yield from self.bot.say("%s Requested a quiet heist!" % author)
        yield from self.bot.say("Time to play: %s" % random.choice(lists.stealth))

    # Prints to the channel the result of a coin flip
    @commands.command(pass_context=True, no_pm=True)
    @asyncio.coroutine
    def coin(self, context):
        author = context.message.author
        num = random.random()
        out = "Tails"
        if num < 0.5:
            out = "Heads"
        yield from self.bot.say("%s Flipped a: %s" % (author, out))

    # 'Rolls' a 100-sided dice
    @commands.command(pass_context=True, no_pm=True)
    @asyncio.coroutine
    def d100(self, context):
        author = context.message.author
        yield from self.bot.say("%s Rolled a: \n%i" % (author, random.randint(0, 100)))

    # Provides a list of commands that the bot can handle
    @commands.command(pass_context=True, no_pm=True)
    @asyncio.coroutine
    def info(self, context):
        author = context.message.author
        string = "Below shows a list of available commands: \n"
        for i in lists.commands:
            string = string + i + "\n"
        yield from self.bot.say(string)

    # Prints the link to the first result of a youtube search query
    @commands.command(pass_context=True, no_pm=True)
    @asyncio.coroutine
    def youtube(self, context):
        link_list = []
        text = context.message.content.split(" ")[1:]  # Get the search queries (can be multiple words)

        yield from self.bot.say("Searching Youtube for: %s" % " ".join(text))
        text = "+".join(text)
        url = "https://www.youtube.com/results?search_query=" + text  # Youtube search query
        response = urlopen(url)
        html = response.read()  # Get the response from youtube
        soup = BeautifulSoup(html, "lxml")
        for vid in soup.findAll(attrs={"class": "yt-uix-tile-link"}):  # Parse the hml to find the video link sources
            link_list.append("https://www.youtube.com" + vid["href"])  # Add each video to a list
        yield from self.bot.say(link_list[1])   # Print the first non-advert response (usually index 1 in list)

    # A test method to practice taking multiple arguments as input
    # takes any number of numerical arguments and prints the sum out to the chat channel
    @commands.command(pass_context=True, no_pm=True)
    @asyncio.coroutine
    def add(self, context):
        author = context.message.author
        numbers = context.message.content.split(" ")[1:]
        numbs = []
        print(numbers)
        for s in numbers:
            a = float(s)
            numbs.append(a)
        print(numbs)
        total = sum(numbs)
        yield from self.bot.say("%s Requested a sum: %.2f" % (author, total))

    # A basic test (not callable by a channel member) to allow testing of each method's functionality
    def devTest(self, message):
        yield from self.client.send_message(message.channel, "A full Dev test has been requested")
        yield from self.info(message)
        yield from self.d100(message)
        yield from self.coin(message)
        yield from self.quiet(message)
        yield from self.loud(message)
        yield from self.heist(message)
