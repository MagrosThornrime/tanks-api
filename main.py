import aiohttp
import asyncio
import json
from dotenv import load_dotenv
import os

from grind import get_grind_path


load_dotenv()
WOT_KEY = os.getenv("WOT_KEY")


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.worldoftanks.eu/wot/encyclopedia/vehicles/?application_id={WOT_KEY}&nation=ussr") as resp:
            print(resp.status)
            text = await resp.text()
            russian_tanks = json.loads(text)["data"]
            for tank_id in russian_tanks.keys():
                russian_tanks[tank_id]["provisions"] = []
            

            print(get_grind_path(russian_tanks, "BT-5", "T-10"))



asyncio.run(main())

