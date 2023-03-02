
# Discord.py library. Has everything we need to 
# interact with discord
import discord
from discord.ext import commands

# dotenv allows us to keep our bot token and
# any other sensitive information in a file
# that is not synced to github
from dotenv import load_dotenv
load_dotenv()


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