import json

import aiohttp
import asyncio

from src.rate_limiter import RateLimiter
import src.exceptions as err

tank_types = {
    "td": "AT-SPG",
    "ht": "heavyTank",
    "mt": "mediumTank",
    "lt": "lightTank",
    "arty": "SPG"
}


async def get_alpha(session: RateLimiter, wot_key: str, gun_id: str) -> int:
    uri = "https://api.worldoftanks.eu/wot/encyclopedia/modules/?"
    uri += f"application_id={wot_key}&extra=default_profile&module_id={gun_id}"
    async with await session.get(uri) as resp:
        if resp.status != 200:
            raise err.ExternalAPIError(f"WoT modules request status: '{resp.status}'")
        text = await resp.text()
    guns = json.loads(text)["data"]
    gun = guns[gun_id]["default_profile"]["gun"]
    ammo = gun["ammo"]
    alpha_values = []
    for ammo_type in ammo:
        mean_damage = ammo_type["damage"][1]
        alpha_values.append(mean_damage)
    return max(alpha_values)
    

async def get_max_alpha(session: RateLimiter, wot_key: str, tanks: dict) -> tuple[int, str]:
    max_alpha, max_tank_id = None, None
    for tank_id, tank in tanks.items():
        guns = tank["guns"]
        results = await asyncio.gather(
            *[get_alpha(session, wot_key, str(gun_id)) for gun_id in guns]
        )
        max_result = max(results)
        if max_alpha is None or max_result > max_alpha:
            max_alpha = max_result
            max_tank_id = tank_id
    return max_alpha, max_tank_id


async def alpha(session: aiohttp.ClientSession, wot_key: str, nation: str = None,
                tier: int = None, tank_type: str = None) -> dict:
    uri = f"https://api.worldoftanks.eu/wot/encyclopedia/vehicles/?application_id={wot_key}"
    if nation is not None:
        uri += f"&nation={nation}"
    if tier is not None:
        uri += f"&tier={tier}"
    if tank_type is not None:
        real_type = tank_types[tank_type]
        uri += f"&type={real_type}"
    async with await session.get(uri) as resp:
        if resp.status != 200:
            raise err.ExternalAPIError(f"WoT vehicles request status: '{resp.status}'")
        text = await resp.text()
    tanks = json.loads(text)["data"]
    max_alpha, max_tank_id = await get_max_alpha(session, wot_key, tanks)
    try:
        max_tank_name = tanks[max_tank_id]["name"]
    except KeyError:
        raise err.NoVehiclesError(f"The group has no vehicles")
    return {
        "tank": max_tank_name,
        "max_alpha": max_alpha
        }
