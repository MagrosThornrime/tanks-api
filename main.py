import aiohttp
import asyncio
import json
from dotenv import load_dotenv
import os

from grind import get_grind_path


load_dotenv()
WOT_KEY = os.getenv("WOT_KEY")

async def grind(wot_key: str, nation: str, start_tank: str, goal_tank: str) -> dict:
    uri = f"https://api.worldoftanks.eu/wot/encyclopedia/vehicles/?application_id={wot_key}&nation={nation}"
    async with aiohttp.ClientSession() as session:
        async with session.get(uri) as resp:
            print(resp.status)
            text = await resp.text()
            russian_tanks = json.loads(text)["data"]
            for tank_id in russian_tanks.keys():
                russian_tanks[tank_id]["provisions"] = []
            return get_grind_path(russian_tanks, start_tank, goal_tank)


async def main():
    return print(await grind(WOT_KEY, "ussr", "BT-5", "T-10"))


asyncio.run(main())

