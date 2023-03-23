'''
The Database class can be used to reference the database in any
file using the exec() function. Simply pass the SQL command to
this function and it will return the result, if there is one.

Each instance of the database class uses the same connection, but
each instance can initiate a "reconnect", if necessary.
'''


import aiomysql
import dns.resolver
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

db = None
cur = None
conn = None
resolve = dns.resolver.query(os.getenv('REMOTE_DOMAIN'), 'A')
ip = None
for ipval in resolve:
    ip = ipval.to_text()


pool = None
async def connect_pool():
    global pool

    try:
        print("\n\nAttempting local database pool connection...")
        if os.getenv('CONNECTION') == "REMOTE": raise Exception
        pool = await aiomysql.create_pool(
                host='192.168.0.12',
                port=3306,
                connect_timeout=2,
                user=os.getenv('DATABASE_USERNAME'),
                password=os.getenv('DATABASE_PASSWORD'),
                db=os.getenv('DATABASE'),
                loop=asyncio.get_event_loop(),
                autocommit=True
        )
        print("Database pool connected locally!\n")
    except Exception as e:
        print(f"Database server not running locally, attempting database pool connection via Cloudflare...")
        try:
            pool = await aiomysql.create_pool(
                    host=ip,
                    port=3306,
                    user=os.getenv('DATABASE_USERNAME'),
                    password=os.getenv('DATABASE_PASSWORD'),
                    db=os.getenv('DATABASE'),
                    loop=asyncio.get_event_loop(),
                    autocommit=True
            )
            # conn = await pool.acquire()
            # cursor = await conn.cursor()
            print("Database pool connected via Cloudflare!\n")
        except:
            print(f"\n##### FAILED TO CONNECT TO DATABASE! #####\n{e}\n")


async def check_pool():
    global pool
    if pool is None:
        await connect_pool()
    if pool.closed:
        print(f"\n\n####### DATABASE POOL CONNECTION LOST! Attempting to reconnect... #######")
        await connect_pool()


class AsyncDatabase:

    def __init__(self, file):
        global pool
        self.file = file
        self.pool = pool

    def __update_vars(self):
        global pool
        self.pool = pool

    async def execute(self, exec_cmd: str):
        for attempt in range(1,6):
            try:
                async with self.pool.acquire() as conn:
                    cursor = await conn.cursor()
                    await cursor.execute(exec_cmd)
            except Exception as e:
                if attempt < 5:
                    if os.getenv('DATABASE_DEBUG') != "1": await asyncio.sleep(5)
                    await check_pool()
                    self.__update_vars()
                    continue
                else:
                    print(f"\nASYNC DATABASE ERROR! [{self.file}] Could not execute: \"{exec_cmd}\"\n{e}")
            break
        
        if exec_cmd.startswith("SELECT"):
            val = await cursor.fetchall()
            if len(val) == 1:
                if len(val[0]) == 1:
                    return val[0][0]
            return val if val != () else [] # easier migration from old synchronous code
        return
    
    def exists(self, rows):
        return rows > 0