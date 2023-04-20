from random import randint
import discord
from discord.ext import commands
from discord.ext.commands import Context
from Database.GuildObjects import BentoMember
from Database.DatabaseConnector import AsyncDatabase

db = AsyncDatabase("cogs.TextCommands.py")


'''
Basic command class for text commands
'''
class TextCommands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.client.user} has connected to Discord!')

    @commands.command(name='test', aliases=['t'])
    @commands.guild_only() # Cannot run this command via DMs with Bento
    async def text_test(self, ctx: Context):
        u = BentoMember(user=ctx.author, client=self.client)
        await u.ainit()
        
        '''
        ctx ("context") contains all the contextual information
        needed to run this command, including (but not limited to):
        member, guild, channel, and other objects.
        '''

        await ctx.channel.send( # or ctx.send()
            content="hello world"
        )


    @commands.command(name='inspire', aliases=['i'])
    @commands.guild_only() # Cannot run this command via DMs with Bento
    async def inspirational_quote(self, ctx: Context):
        u = BentoMember(user=ctx.author, client=self.client)
        await u.ainit()
        
        quotes: str = await db.execute(
            "SELECT val FROM INFO WHERE variable='INSPIRATIONAL_QUOTES'"
        )
        if quotes == [] or quotes is None:
            await ctx.send(
                content="❗ Error: Could not find INSPIRATIONAL_QUOTES in database!"
            )
            return
        
        quotes = quotes.split("\n")
        
        await ctx.send(
            content=quotes[randint(0, len(quotes)-1)]
        )



async def setup(client: commands.Bot):
    await client.add_cog(TextCommands(client))
