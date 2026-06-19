import asyncio


class RequestLane:
    def __init__(self):
        self._condition = asyncio.Condition()
        self._next_ticket = 0
        self._serving = 0

    async def join(self):
        async with self._condition:
            ticket = self._next_ticket
            self._next_ticket += 1
            position = ticket - self._serving + 1
            return ticket, position

    async def wait_turn(self, ticket):
        async with self._condition:
            await self._condition.wait_for(lambda: ticket == self._serving)

    async def leave(self, ticket):
        async with self._condition:
            if ticket == self._serving:
                self._serving += 1
                self._condition.notify_all()


LANES = {
    "subscriber": RequestLane(),
    "general": RequestLane(),
}


def lane_for_tier(tier):
    if tier.key in {"lifetime", "supporter"}:
        return None
    if tier.key == "subscriber":
        return LANES["subscriber"]
    return LANES["general"]
