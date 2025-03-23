import time

import aiohttp
import asyncio

class RateLimiter:

    def __init__(self, client: aiohttp.ClientSession, max_tokens: int = 10, rate: int = 10):
        self.client = client
        self.max_tokens = max_tokens
        self.rate = rate
        self.tokens = max_tokens
        self.updated_at = time.monotonic()

    async def get(self, *args, **kwargs):
        await self.wait_for_token()
        return self.client.get(*args, **kwargs)
    
    async def wait_for_token(self):
        while self.tokens <= 1:
            self.add_new_tokens()
            await asyncio.sleep(1)
        self.tokens -= 1

    def add_new_tokens(self):
        now = time.monotonic()
        time_since_update = now - self.updated_at
        new_tokens = time_since_update * self.rate
        if self.tokens + new_tokens >= 1:
            self.tokens = min(self.tokens + new_tokens, self.max_tokens)
            self.updated_at = now
