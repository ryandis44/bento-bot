import discord
import typing
from discord.ext import commands
from discord import app_commands
from Database.DatabaseConnector import Database

sc = Database("SlashCommands.py")

class SlashCommands(commands.Cog):
    def __init__(self, client):
        self.client: discord.Client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        self.tree = app_commands.CommandTree(self.client)


    '''
    Sync function code copied from discord.py API reference website and modified for
    Bento bot.

    Application commands ("Slash Commands") are similar to text commands in the sense the user runs the command and
    gets an output. However, that is it. App commands need to be synced to discord in order to be run by anyone.
    Running 'bsc *' will sync all slash commands to the current guild, and 'bsc G' will sync all (non private)
    slash commands to all guilds Bento bot is in. When changes are made to the function of the app command
    (i.e. slash_command(self, interaction) -> slash_command(self, interaction, song_name)), it will need
    to be re-synced using this command.

    The sync command is always a text command

    Additionally, application commands NEED to be responded to. Text commands can be ignored. This is done
    by using 'interaction.response.<...>'. The interaction object contains everything the ctx ("Context")
    object contains from Text Command and more, namely the client (Bento discord account [renamed client
    from bot]), and 'interaction.original_response()', which can be used to get the response from the
    'interaction_check' function, if one has been made (a response is not necessary from the
    interaction_check function).
    '''
    @commands.command(name='sync', aliases=['sc'])
    @commands.guild_only()
    async def sync(
      self, ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: typing.Optional[typing.Literal["~", "*", "^", "G"]] = None) -> None:
        
        # If not an admin, do nothing
        if not ctx.author.guild_permissions.administrator: return

        if spec is not None: await ctx.channel.send("Attempting to sync commands...")
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            elif spec == "G":
                synced = await ctx.bot.tree.sync()
            else:
                await ctx.channel.send(
                    "Please provide a modifier: `bsc <modifier>`\n"+
                    "`~` Locally syncs private guild commands to current guild (if they are listed on this server)\n"+
                    "`*` Syncs global commands to current guild\n"+
                    "`^` Clears all locally synced commands from current guild\n"+
                    "`G` Globally syncs all non-private commands to all guilds\n"
                )
                return

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


    @app_commands.command(name="test", description=f"Hello World command")
    @app_commands.guild_only
    async def slash_test(self, interaction: discord.Interaction):

        # Select will return a value if ONE is found, a list (array) if
        # multiple values are found, or [] (empty list) if nothing is
        # found.
        val = sc.exec(
            "SELECT val FROM STATISTICS WHERE "
            f"stat='TEST_COMMAND' AND user_id='{interaction.user.id}'"
        )
        if val == [] or val is None:
            # Insert does as it sounds, it will insert values
            # into the 'STATISTICS' table and can be referenced
            # using the select command.
            sc.exec(
                "INSERT INTO STATISTICS (user_id,stat,val) VALUES "
                f"('{interaction.user.id}', 'TEST_COMMAND', '0')"
            )
            val = 1
        
        # Update changes a value or values of an entry in the
        # referenced table (in this case statistics), based off
        # a search criteria. In this case, we are updating
        # 'val' where the user id is the id of the user
        # running this command and the stat=TEST_COMMAND
        sc.exec(
            f"UPDATE STATISTICS SET val='{val+1}' WHERE "
            f"user_id='{interaction.user.id}' AND stat='TEST_COMMAND'"
        )


        await interaction.response.send_message(
            content=(
                f"Hello World\n"
                f"You have run this command {val} times"
            )
        )


    '''
    Function run before every slash command. If this function returns 'True',
    the command being run will continue to run. If 'False', the calling command
    will not be run at all.
    '''
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True



async def setup(client: commands.Bot):
    await client.add_cog(SlashCommands(client))