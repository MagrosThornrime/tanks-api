from dotenv import load_dotenv
import os
from contextlib import asynccontextmanager

import aiohttp
from fastapi import FastAPI, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.grind import grind, Path
from src.alpha import alpha, MaxAlpha
from src.rate_limiter import RateLimiter
import src.exceptions as err


class Message(BaseModel):
    message: str


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
app.mount("/static", StaticFiles(directory="static",html=True), name="static")

responses_grind = {
    404: {"model": Message},
    502: {"model": Message}
}

responses_alpha = {
    404: {"model": Message},
    502: {"model": Message},
    422: {"model": Message}
}

@app.get("/grind_path", response_model=Path, responses=responses_grind)
async def grind_path(nation: str, start_tank: str, end_tank: str):
    try:
        return await grind(client, WOT_KEY, nation, start_tank, end_tank)
    except err.TankNotFoundError as e:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": str(e)})
    except err.GrindPathError as e:
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"message": str(e)})
    except err.ExternalAPIError as e:
        return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content={"message": str(e)})


@app.get("/max_alpha", response_model=MaxAlpha, responses=responses_alpha)
async def max_alpha(nation: str = None, tank_type: str = None, tier: int = None):
    try:
        return await alpha(client, WOT_KEY, nation=nation, tank_type=tank_type, tier=tier)
    except err.ExternalAPIError as e:
        return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content=str(e))
    except err.NoVehiclesError as e:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=str(e))
