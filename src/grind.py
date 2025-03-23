from dataclasses import dataclass
import json

from src.rate_limiter import RateLimiter
import src.exceptions as err
from pydantic import BaseModel

class Path(BaseModel):
    path: list[str]
    credits: str
    xp: str

@dataclass
class Cost:
    credits: int = 0
    xp: int = 0

    def __add__(self, other):
        return Cost(self.credits + other.credits, self.xp + other.xp)

    def __eq__(self, other):
        return self.xp == other.xp and self.credits == other.credits

    def __gt__(self, other):
        if self.xp > other.xp:
            return True
        return self.xp == other.xp and self.credits > other.credits

    def __lt__(self, other):
        if self.xp < other.xp:
            return True
        return self.xp == other.xp and self.credits < other.credits

    def __ge__(self, other):
        return self.__gt__(other.xp) or self.__eq__(other.xp)

    def __le__(self, other):
        return self.__lt__(other.xp) or self.__eq__(other.xp)


def find_tank(tanks: dict, name: str) -> dict:
    for params in tanks.values():
        if params["name"] == name:
            return params
    return None


def traverse_modules(tanks_found: dict, visited: dict, modules: dict, module_id: str, xp: int = 0):
    if visited[module_id]:
        return
    visited[module_id] = True
    module = modules[module_id]
    if module["next_modules"]:
        for next_id in module["next_modules"]:
            next_id = str(next_id)
            next_xp = modules[next_id]["price_xp"]
            traverse_modules(tanks_found, visited, modules, next_id, xp + next_xp)
    if module["next_tanks"]:
        for tank_id in module["next_tanks"]:
            tank_id = str(tank_id)
            tanks_found[tank_id] = xp


def tank_research_price(tanks: dict, current_tank_id: str, next_tank_id: str) -> Cost:
    next_tank = tanks[next_tank_id]
    prices_xp = next_tank["prices_xp"]
    xp = prices_xp[current_tank_id]
    credits = next_tank["price_credit"]
    return Cost(credits, xp)


def get_next_tank_costs(tanks: dict, current_tank_name: str) -> dict[str, Cost]:
    current_tank = find_tank(tanks, current_tank_name)
    if current_tank is None:
        raise err.TankNotFoundError(f"Tank not found: '{current_tank_name}'")
    modules = current_tank["modules_tree"]
    visited = {module: False for module in modules}
    tanks_found = {}
    for module_id in modules:
        traverse_modules(tanks_found, visited, modules, module_id)
    current_tank_id = str(current_tank["tank_id"])
    tanks_found_costs = {}
    for tank_id, xp in tanks_found.items():
        research_price = tank_research_price(tanks, current_tank_id, tank_id)
        tanks_found_costs[tank_id] = Cost(research_price.credits, research_price.xp + xp)
    return tanks_found_costs


def traverse_tanks(tanks: dict, current_tank_id: str, goal_tank_id: str, 
                    current_path: tuple[str], current_cost: Cost) -> Cost:
    if current_tank_id == goal_tank_id:
        return current_cost, current_path

    goal_tank = tanks[goal_tank_id]
    current_tank = tanks[current_tank_id]
    if int(current_tank["tier"]) >= int(goal_tank["tier"]):
        return None, None

    next_tanks = get_next_tank_costs(tanks, current_tank["name"])

    min_cost, min_path = None, None
    for next_tank_id, research_cost in next_tanks.items():
        next_cost, next_path = traverse_tanks(tanks, next_tank_id, goal_tank_id,
                                              current_path + (next_tank_id,),
                                              current_cost + research_cost)
        if next_cost is None:
            continue
        if min_cost is None or next_cost < min_cost:
            min_cost = next_cost
            min_path = next_path
    return min_cost, min_path


def get_grind_path(tanks: dict, current_tank_name: str, goal_tank_name: str) -> Cost:
    current_tank = find_tank(tanks, current_tank_name)
    if current_tank is None:
        raise err.TankNotFoundError(f"Tank not found: '{current_tank_name}'")
    goal_tank = find_tank(tanks, goal_tank_name)
    if goal_tank is None:
        raise err.TankNotFoundError(f"Tank not found: '{goal_tank_name}'")
    
    current_tank_id = str(current_tank["tank_id"])
    goal_tank_id = str(goal_tank["tank_id"])
    cost, path = traverse_tanks(tanks, current_tank_id, goal_tank_id, (), Cost())
    if cost is None:
        raise err.GrindPathError(f"Path from '{current_tank_name}' to '{goal_tank_name}' not found")
    path = (current_tank_id,) + path
    path_names = [tanks[tank_id]["name"] for tank_id in path]
    return {
        "path": path_names,
        "xp": cost.xp,
        "credits": cost.credits
    }


async def grind(session: RateLimiter, wot_key: str, nation: str,
                start_tank: str, goal_tank: str) -> dict:
    uri = f"https://api.worldoftanks.eu/wot/encyclopedia/vehicles/?application_id={wot_key}&nation={nation}"
    async with await session.get(uri) as resp:
        if resp.status != 200:
            raise err.ExternalAPIError(f"WoT vehicles request status: '{resp.status}'")
        text = await resp.text()
    tanks = json.loads(text)["data"]
    return get_grind_path(tanks, start_tank, goal_tank)
