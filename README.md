# snugglebot
A simple discord-bot written in python for creating and managing game events. Uses discord.py. 
It is developed as a hobby project by ostropunk.

# Functionality
The bot enables the members of a discord-server to create events. All members can then join, reserve or decline the event. 
The bot will remind members who have signed up as attending or reserves when the events starts.
It is advised to set up a bashscript and cronjob to restart the bot in case of crashes.  

# Requirements
The bot uses discord.py (not rebuild) to communicate with the Discord API.
The bot stores information about members and events in sqlite3.
The bot currently uses pyjokes, however this may change soon.
