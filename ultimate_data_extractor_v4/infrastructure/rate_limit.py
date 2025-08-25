import asyncio
import time
from typing import Dict


class RateLimitManager:
    def __init__(self) -> None:
        self.last_request: Dict[str, float] = {}

    async def wait_if_needed(self, source_name: str, rate_limit: float) -> None:
        now = time.time()
        last = self.last_request.get(source_name)
        if last is not None:
            elapsed = now - last
            if elapsed < rate_limit:
                await asyncio.sleep(rate_limit - elapsed)
        self.last_request[source_name] = time.time()

