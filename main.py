from dotenv import load_dotenv
import os
from contextlib import asynccontextmanager

import aiohttp
from fastapi import FastAPI

from grind import grind
from alpha import alpha
from rate_limiter import RateLimiter


load_dotenv()
WOT_KEY = os.getenv("WOT_KEY")            
session = None
client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global session
    global client
    session = aiohttp.ClientSession()
    client = RateLimiter(session)
    yield
    await session.close()


app = FastAPI(lifespan=lifespan)


@app.get("/grind_path")
async def grind_path(nation: str, start_tank: str, end_tank: str):
    return await grind(client, WOT_KEY, nation, start_tank, end_tank)


@app.get("/max_alpha")
async def max_alpha(nation: str = None, tank_type: str = None, tier: int = None):
    return await alpha(client, WOT_KEY, nation=nation, tank_type=tank_type, tier=tier)
