
# Discord.py library. Has everything we need to 
# interact with discord. Asyncio is a python
# library and it enables discord.py to run
# asynchronously and is required.
import discord
import asyncio
from discord.ext import commands

# dpyConsole allows us to run console commands
# so we can interact with the bot directly
# (if we want). It is here because the panel
# this bot will run on terminates programs
# using a keyword instead of sigint.
from dpyConsole import Console

# dotenv allows us to keep our bot token and
# any other sensitive information in a file
# that is not synced to github. 'os' allows
# us to interact with dotenv using 'os.getenv()'
import os
from dotenv import load_dotenv
load_dotenv()

# Signal allows us to gracefully shutdown our bot
# upon receiving ^C (sigint) instead of killing
# everything and not updating the database
# (if we implement one)
import signal

'''
Intents are the way we will tell discord what our
bot needs access to: Member presences (online status),
message content, and other privledged information.
'''
intents = discord.Intents.all()

'''
Client ("bot") is the account object (bot account) that
will interact with discord (Bento)
'''
client = discord.Client(intents=intents)
client = commands.Bot(
    command_prefix=['b'],
    help_command=None,
    intents=intents
)
console = Console(client=client)

# Catch and handle sigint (Ctrl + C).
# Variables 'one' and 'two' are needed
# for some reason ¯\_(ツ)_/¯
def terminate(one=None, two=None):
    print("Shutting down...")
    # any functions that need to be
    # run before shutdown would go here
    print("Graceful shutdown complete. Goodbye.")
    os._exit(0)
signal.signal(signal.SIGINT, terminate)


'''
Catches 'shutdown' sent from Pterodactyl Panel
running this bot.
'''
@console.command()
async def shutdown(): terminate()


'''
The @client.event decorator tells Bento to listen for the
following event function. List of event functions
available here:
https://discordpy.readthedocs.io/en/stable/api.html?highlight=event#discord-api-events
'''
@client.event
async def on_member_join(member: discord.Member) -> None:

    # Can also use member.guild.get_role() if you want to use a role ID instead
    role = discord.utils.get(member.guild.roles, name="bento dev")
    await member.add_roles(role)











# Spaces implying these functions must remain
# at the bottom of the file
'''
This function loads all extensions (commands) in the
'cogs' folder and gives the client object access
to them
'''
async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await client.load_extension(f'cogs.{filename[:-3]}')


'''
Main function that starts the bot and connects it to discord
'''
async def main():
    print('bot online') # for control panel to know bot is running
    async with client:
        await load_extensions()
        console.start()
        TOKEN = os.getenv('DISCORD_API_TOKEN')
        await client.start(TOKEN)

asyncio.run(main())