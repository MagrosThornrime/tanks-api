from dotenv import load_dotenv
import os

import asyncio
import aiohttp

from grind import grind
from alpha import alpha
from rate_limiter import RateLimiter


load_dotenv()
WOT_KEY = os.getenv("WOT_KEY")            


async def main():
    async with aiohttp.ClientSession() as session:
        client = RateLimiter(session)
        print(await grind(client, WOT_KEY, "ussr", "BT-5", "T-10"))
        print(await alpha(client, WOT_KEY, tank_type="arty", tier=6))


asyncio.run(main())

