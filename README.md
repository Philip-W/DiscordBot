# DiscordBot

A program designed to provide music and various quality of life features to servers I am part of in the VoiP program Discord (https://discordapp.com/).

The main feature is the ability to play music and audio through a voice channel on the sever, it does this by managing requests to a library that retrieves audio from Youtube. The bot acts as a member of the server and listens for specific commands (e.g !play; !join; !stop) that control what the bot is doing. Users in the channel can make requests to the bot and it will join the voice channel that user is in and play the requested audio. Audio is requested either by providing a url or a search term to the bot, if a search term is provided the library will make a query to youtube and play the first result. 

I also added a few additional basic features as requested by the users such as random number generators and search functions. 
