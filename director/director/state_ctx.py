from . import state

class StateCtx:
    def __init__(self, name, coro):
        self.name = name
        self.coro = coro

    async def __aenter__(self):
        state.clear_status(self.name)

    async def __aexit__(self, exc, exc_type, tb):
        state.clear_status(self.name)
        await self.coro