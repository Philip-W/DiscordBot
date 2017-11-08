import asyncio
import discord
from discord import opus
from discord.ext import commands
import lists

"""
In this file all music handling code is held, it is managed by several small classes that hold the state of the
bot and it's music player
"""


if not discord.opus.is_loaded():  # Checks if necessary libraries are loaded
    discord.opus.load_opus("./usr/lib/x86_64-linux-gnu/libopus.so")

client = discord.Client()


class VoiceEntry:
    """
    Holds details about a song that was requested and by which member of the channel.
    """

    def __init__(self, message, player):
        self.requester = message.author  # Who requested the song
        self.channel = message.channel   # Which channel the request came from
        self.player = player             # The music player

    def __str__(self):
        fmt = '*{0.title}* uploaded by {0.uploader} and requested by {1.display_name}'
        duration = self.player.duration
        if duration:
            fmt = fmt + '[length: {0[0]}m {0[1]}s]'.format(divmod(duration, 60))
        return fmt.format(self.player, self.requester)


class VoiceState:
    """
    Used to control the state of the music player, maintain which song is playing, what's next, skipping of songs.
    """

    def __init__(self, bot):
        self.current = None
        self.voice = None
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs = asyncio.Queue()
        self.skip_votes = set()
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    """Returns true or false depending on if a song is playing """
    def is_playing(self):
        if self.voice is None or self.current is None:
            return False

        player = self.current.player
        return not player.is_done()

    @property
    def player(self):
        return self.current.player

    """ Skips the current song, does not start next song, just handles the refreshing of current song details"""
    def skip(self):
        self.skip_votes.clear()
        if self.is_playing():
            self.player.stop()

    """Starts the next song in the queue"""
    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    """This is the loop that continually manages the song being played"""
    @asyncio.coroutine
    def audio_player_task(self):
        while True:
            self.play_next_song.clear()
            self.current = yield from self.songs.get()
            yield from self.bot.send_message(self.current.channel, "Now playing: " + str(self.current))
            self.current.player.start()
            yield from self.play_next_song.wait()


class Music:
    """
    Handles all interaction with channel users such as input/requests, then handles adding them to the voice state.
    Also handles voice states across however many channels the bot is being used on.
    """

    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}

    """Returns the 'voice state' for that server (can only play one time per server)"""
    def get_voice_state(self, server):
        state = self.voice_states.get(server.id)
        if state is None:
            state = VoiceState(self.bot)
            self.voice_states[server.id] = state
        return state

    """Joins a voice channel and gets the object that allows audio playing [voice]"""
    @asyncio.coroutine
    def create_voice_client(self, channel):
        voice = yield from self.bot.join_voice_channel(channel)
        state = self.get_voice_state(channel.server)
        state.voice = voice

    """User request: joins a given audio channel, handles invalid requests by providing info to the caller"""
    @commands.command(pass_context=True, no_pm=True)
    @asyncio.coroutine
    def join(self, ctx, *, channel: discord.Channel):
        try:
            yield from self.create_voice_client(channel)
        except discord.ClientException:
            yield from self.bot.say("Already in a voice channel...")
        except discord.InvalidArgument:
            yield from self.bot.say("Not a voice channel...")
        else:
            yield from self.bot.say("Ready to play audio in " + channel.name)

    """Joins the channel that the requester is currently in"""
    @commands.command(pass_context=True, no_pm=True)
    @asyncio.coroutine
    def summon(self, ctx):
        summond_channel = ctx.message.author.voice_channel
        if summond_channel is None:
            yield from self.bot.say("No Voice Channel")
            return False

        state = self.get_voice_state(ctx.message.server)
        if state.voice is None:
            state.voice = yield from self.bot.join_voice_channel(summond_channel)

        return True

    """
        User Request: play the provided song
        Can take either a link or a name (which will be searched in youtube)
    """
    @commands.command(pass_context=True, no_pm=False)
    @asyncio.coroutine
    def play(self, ctx, *, song: str):
        opts = {
            'default_search': 'auto',
            'quiet': True,
        }

        # This was added to allow users to send a personal message to the bot, allowing users to hide what song
        # they had added to the queue for their channel
        if ctx.message.channel.is_private:
            for chan in self.bot.get_all_channels():          # Checks all the channels the bot is a part of to find
                if ctx.message.author in chan.voice_members:  # which voice channel the user is currently a part of
                    state = self.get_voice_state(chan.server)

        else:
            # if the message is not private just use the channel it was posted in
            state = self.get_voice_state(ctx.message.server)

        if state is None:
            # Checks for a null  state
            print("Error: state not available")
            return

        # This makes it so a user can play a song before the bot is in a voice channel
        # if the bot is not currently in the channel it will attempt to join the channel the user is currently in
        if state.voice is None:
            success = yield from ctx.invoke(self.summon)
            if not success:
                return

        # Finally invoke the ytdl method that gets the song ready for playing
        try:
            player = yield from state.voice.create_ytdl_player(song, ytdl_options=opts, after=state.toggle_next)
        except Exception as e:
            # Catch an appropriate errors when invoking ytdl lib
            fmt = "Error happened while processing: '''py\n{}: {}\n'''"
            yield from self.bot.send_message(ctx.message.channel, fmt.format(type(e).__name__, e))
        else:
            # Create a song entry and add it to the player queue.
            player.volume = 0.6
            entry = VoiceEntry(ctx.message, player)
            yield from self.bot.say("Enqueued: " + str(entry))
            yield from state.songs.put(entry)

    """User Request: alters the current music volume"""
    @commands.command(pass_context=True, no_pm=True)
    @asyncio.coroutine
    def volume(self, ctx, value: int):
        state = self.get_voice_state(ctx.message.server)
        if value > 120:  # Place upper limit on volume
            return
        if state.is_playing():
            player = state.player
            player.volume = value / 100
            yield from self.bot.say("Volume set to: " + str(player.volume))

    """User Request: pause audio playback"""
    @commands.command(pass_context=True, no_pm=True)
    @asyncio.coroutine
    def pause(self, ctx):
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.pause()

    """User Request: resumes audio playback after being paused"""
    @commands.command(pass_context=True, no_pm=True)
    @asyncio.coroutine
    def resume(self, ctx):
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.resume()

    """User Request: Stops audio playback, Leaves the audio channel and empties the song queue"""
    @commands.command(pass_context=True, no_pm=True)
    @asyncio.coroutine
    def stop(self, ctx):
        server = ctx.message.server
        state = self.get_voice_state(server)
        if state.is_playing():
            player = state.player
            player.stop()
        try:
            state.audio_player.cancel()
            del self.voice_states[server.id]
            yield from state.voice.disconnect()
        except:
            pass

    """
    User Request: Adds a vote to skip the current song, if the vote is called by the song requester, it
    will be skipped immediately.
    Non-requester users require 3 different votes to skip the current song.
    """
    @commands.command(pass_context=True, no_pm=True)
    @asyncio.coroutine
    def skip(self, ctx):
        state = self.get_voice_state(ctx.message.server)
        if not state.is_playing():
            yield from self.bot.say("Nothing is playing right now!")
            return

        voter = ctx.message.author
        if voter == state.current.requester:  # Skip if requester was the one to skip
            yield from self.bot.say("Requester skipped song")
            state.skip()

        elif voter.id not in state.skip_votes:
            state.skip_votes.add(voter.id)
            total = len(state.skip_votes)
            if total >= 3:
                yield from self.bot.say("Vote to skip passed")
                state.skip()

            else:
                yield from self.bot.say("Skip vote added, current number: %i / 3" % total)
        else:
            yield from self.bot.say("Vote to skip has passed")

    """Allows a user to find out what is currently being played"""
    @commands.command(pass_context=True, no_pm=True)
    @asyncio.coroutine
    def playing(self, ctx):
        state = self.get_voice_state(ctx.message.server)
        if not state.is_playing():
            yield from self.bot.say("Nothing playing right now")
            return
        else:
            skip_count = len(state.skip_votes)
            yield from self.bot.say("Now PLaying {}  [Skips: {}/3]".format(state.current, skip_count))

    """Shows the user how to use the bot and it's commands."""
    @commands.command(pass_context=True, no_pm=True)
    @asyncio.coroutine
    def playinfo(self, ctx):
        string = "Below shows the commands for the video player: \n"
        for value in lists.playinfo:
            string = string + value + "\n"

        yield from self.bot.say(string)

