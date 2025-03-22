from dotenv import load_dotenv
import os

import asyncio

from grind import grind


load_dotenv()
WOT_KEY = os.getenv("WOT_KEY")            



async def main():
    return print(await grind(WOT_KEY, "ussr", "BT-5", "T-10"))
    # await alpha(WOT_KEY, nation="poland", tank_type="heavyTank")


asyncio.run(main())

