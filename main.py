import aiohttp
import asyncio
import json
from collections import namedtuple
from dotenv import load_dotenv
import os


load_dotenv()
WOT_KEY = os.getenv("WOT_KEY")
Resources = namedtuple("Resources", ["credits", "exp"])

def find_tank(tanks: dict, name: str) -> dict:
    for params in tanks.values():
        if params["name"] == name:
            return params
    return None

def traverse_modules(tanks_found: dict, visited: dict, modules: dict, module_id: str, xp: int = 0, indent: int = 0):
    module = modules[module_id]

    if visited[module_id]:
        return
    visited[module_id] = True

    field = indent * 4 * " "
    print(field+f"module: {module_id}")
    print(field+f"xp: {xp}")
    if module["next_modules"]:
        for next_id in module["next_modules"]:
            next_id = str(next_id)
            next_xp = modules[next_id]["price_xp"]
            traverse_modules(tanks_found, visited, modules, next_id, xp + next_xp, indent+1)
    
    if module["next_tanks"]:
        for tank in module["next_tanks"]:
            print(field+f"tank: {tank}")
            tank = str(tank)
            tanks_found[tank] = xp
    print()


def resources_next_tanks(tanks: dict, current_tank_name: str) -> dict[str, Resources]:
    current_tank = find_tank(tanks, current_tank_name)
    if current_tank is None:
        raise ValueError("Tank not found")
    modules = current_tank["modules_tree"]
    visited = {module: False for module in modules}
    tanks_found = {}
    for module_id in modules:
        traverse_modules(tanks_found, visited, modules, module_id)
    for tank in tanks_found:
        # new_tank_xp = tanks[tank]["prices_xp"][current_tank]
        # tanks_found[tank] += tanks[tank][current_tank]
    return tanks_found


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.worldoftanks.eu/wot/encyclopedia/vehicles/?application_id={WOT_KEY}&nation=ussr&tier=9&type=mediumTank") as resp:
            print(resp.status)
            text = await resp.text()
            russian_tanks = json.loads(text)["data"]
            for tank_id in russian_tanks.keys():
                russian_tanks[tank_id]["provisions"] = []
            
            names = [tank["name"] for tank in russian_tanks.values()]
            print(names)
            print(resources_next_tanks(russian_tanks, "T-54"))


asyncio.run(main())

