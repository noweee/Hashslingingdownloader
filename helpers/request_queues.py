import asyncio
from dataclasses import dataclass


@dataclass(frozen=True)
class QueueTicket:
    lane: "RequestLane"
    ticket: int


class RequestLane:
    def __init__(self):
        self._condition = asyncio.Condition()
        self._next_ticket = 0
        self._tickets = []
        self._callbacks = {}

    def _position_map(self):
        return {ticket: index + 1 for index, ticket in enumerate(self._tickets)}

    async def _broadcast(self):
        async with self._condition:
            callbacks = []
            positions = self._position_map()
            for ticket in self._tickets:
                callback = self._callbacks.get(ticket)
                if callback:
                    callbacks.append((callback, positions[ticket]))
        if callbacks:
            await asyncio.gather(*(callback(position) for callback, position in callbacks), return_exceptions=True)

    async def join(self, on_update=None):
        async with self._condition:
            ticket = self._next_ticket
            self._next_ticket += 1
            self._tickets.append(ticket)
            if on_update:
                self._callbacks[ticket] = on_update
            position = self._tickets.index(ticket) + 1
        await self._broadcast()
        return QueueTicket(self, ticket), position

    async def wait_turn(self, queue_ticket):
        ticket = queue_ticket.ticket if isinstance(queue_ticket, QueueTicket) else queue_ticket
        async with self._condition:
            await self._condition.wait_for(lambda: bool(self._tickets) and self._tickets[0] == ticket)

    async def leave(self, queue_ticket):
        ticket = queue_ticket.ticket if isinstance(queue_ticket, QueueTicket) else queue_ticket
        async with self._condition:
            if ticket in self._tickets:
                self._tickets.remove(ticket)
            self._callbacks.pop(ticket, None)
            self._condition.notify_all()
        await self._broadcast()


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
