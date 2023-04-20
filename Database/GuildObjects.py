import discord
import asyncio
import time
from Database.DatabaseConnector import AsyncDatabase
from misc.misc import sanitize_name
db = AsyncDatabase("Database.GuildObjects.py")


CHECK_LOCK = {}

def check_lock(key) -> asyncio.Lock:
        val = CHECK_LOCK.get(key)
        
        if val is None:
            lock = asyncio.Lock()
            CHECK_LOCK[key] = {
                'at': int(time.time()),
                'lock': lock
            }
            return lock
        
        val['at'] = int(time.time())
        return val['lock']

def lock_status(key) -> bool:
    val = CHECK_LOCK.get(key)
    if val is None: return False
    return val['lock'].locked()
    
class BentoGuild():

    def __init__(self, guild: discord.Guild, client: discord.Client, guild_id: int = None, check_exists=True, check_exists_guild=True):
        if guild_id is None: self.guild = guild
        else: self.guild = client.get_guild(int(guild_id))
        self.client = client
        self.log_channel = client.get_channel(1073509692363517962) # miko-logs channel in The Boys Hangout

    async def ainit(self, check_exists: bool = True):
        if check_exists:
            async with check_lock(key=self.guild.id): # avoid duplicates
                await self.__exists()

    def __str__(self):
        return f"{self.guild} | BentoGuild Object"

    async def __exists(self) -> None:
        sel_cmd = f"SELECT cached_name,owner_name,owner_id,total_members FROM SERVERS WHERE server_id='{self.guild.id}'"
        rows = await db.execute(sel_cmd)

        # If guild exists in database, update cache and return
        if db.exists(len(rows)):
            await self.__update_cache(rows)
            return


        # If guild does not exist in database, create it
        ins_cmd = (
            "INSERT INTO SERVERS (server_id, cached_name, owner_name, owner_id, total_members) VALUES "
            f"('{self.guild.id}', '{sanitize_name(self.guild.name)}', '{sanitize_name(self.guild.owner.name)}', "
            f"'{self.guild.owner.id}', '{self.guild.member_count}')"
        )
        await db.execute(ins_cmd)
        print(f"Added server {self.guild.name} ({self.guild.id}) to database")
        await self.add_all_members()

    async def add_all_members(self) -> None:
        for member in self.guild.members:
            u = BentoMember(user=member, client=self.client)
            print(u)
            await u.ainit(check_exists_guild=False, skip_if_locked=True)
        await self.set_member_numbers()

    async def set_member_numbers(self) -> None:
        member_ids = await db.execute(
            "SELECT user_id FROM USERS WHERE "
            f"server_id='{self.guild.id}' "
            "ORDER BY original_join_time ASC"
        )
        for i, db_member in enumerate(member_ids):
            await db.execute(
                f"UPDATE USERS SET unique_number='{i+1}' WHERE "
                f"user_id='{db_member[0]}' AND server_id='{self.guild.id}'"
            )

    async def __update_cache(self, rows) -> None:
        params_temp = []
        params_temp.append("UPDATE SERVERS SET ")

        updating = False
        if self.guild.name != rows[0][0]:
            updating = True
            params_temp.append(f"cached_name='{sanitize_name(self.guild.name)}'")
        
        if str(self.guild.owner) != rows[0][1]:
            if updating: params_temp.append(",")
            updating = True
            params_temp.append(f"owner_name='{sanitize_name(self.guild.owner)}'")
        
        if self.guild.owner.id != rows[0][2]:
            if updating: params_temp.append(",")
            updating = True
            params_temp.append(f"owner_id=\"{self.guild.owner.id}\"")

        if self.guild.member_count != rows[0][3]:
            if updating: params_temp.append(",")
            updating = True
            params_temp.append(f"total_members=\"{self.guild.member_count}\"")
        
        if updating:
            params_temp.append(f" WHERE server_id=\"{self.guild.id}\"")
            upd_cmd = f"{''.join(params_temp)}"
            await db.execute(upd_cmd)
        return


class BentoMember(BentoGuild):
    def __init__(self, user: discord.Member, client: discord.Client, guild_id: int = None, check_exists=True, check_exists_guild=True):
        if guild_id is None: super().__init__(guild=user.guild, client=client)
        else: super().__init__(guild=None, client=client, guild_id=guild_id)
        self.user = user
    
    async def ainit(self, check_exists: bool = True, check_exists_guild: bool = True, skip_if_locked: bool = False):
        if (check_exists and not self.user.pending) and \
            not (skip_if_locked and lock_status(key=self.user.id)):
            async with check_lock(key=self.user.id):
                await super().ainit(check_exists=check_exists_guild)
                await self.__exists()

    def __str__(self):
        return f"{self.user} - {self.guild} | BentoMember Object"
    
    async def __exists(self) -> None:
        sel_cmd = f"SELECT cached_username,latest_join_time FROM USERS WHERE user_id='{self.user.id}' AND server_id='{self.guild.id}'"
        rows = await db.execute(sel_cmd)

        if db.exists(len(rows)):
            await self.__update_cache(rows)
            return
        

        latest_join_time = int(self.user.joined_at.timestamp())
        ins_cmd = (
            "INSERT INTO USERS (server_id,user_id,original_join_time,latest_join_time,cached_username) VALUES "
            f"('{self.guild.id}', '{self.user.id}', '{latest_join_time}', '{latest_join_time}',"
            f"\"{self.user}\")"
        )
        await db.execute(ins_cmd)
        print(f"Added user {self.user.id} ({self.user}) in guild {self.guild} ({self.guild.id}) to database")


        # Unique number handling
        val = await db.execute(
            "SELECT unique_number FROM USERS WHERE "
            f"server_id='{self.guild.id}' ORDER BY unique_number DESC LIMIT 1"
        )
        if val == [] or val is None: return
        await db.execute(
            f"UPDATE USERS SET unique_number={int(val)+1} WHERE user_id='{self.user.id}' "
            f"AND server_id='{self.guild.id}'"
        )

    async def __update_cache(self, rows) -> None:
        params_temp = []
        params_temp.append("UPDATE USERS SET ")

        updating = False
        if str(self.user) != rows[0][0]:
            updating = True
            params_temp.append(f"cached_username='{sanitize_name(str(self.user))}'")

        latest_join_time = int(self.user.joined_at.timestamp())
        if latest_join_time != rows[0][1]:
           if updating: params_temp.append(",")
           updating = True
           params_temp.append(f"latest_join_time='{latest_join_time}'")
        
        if updating:
            params_temp.append(f" WHERE user_id=\"{self.user.id}\" AND server_id=\"{self.guild.id}\"")
            upd_cmd = f"{''.join(params_temp)}"
            await db.execute(upd_cmd)