
class StateCtx:
    def __init__(self, state, name, coro):
        self.state = state
        self.name = name
        self.coro = coro

    async def __aenter__(self):
        await self.state.clean_status(self.name)

    async def __aexit__(self, exc, exc_type, tb):
        await self.state.clean_status(self.name)
        await self.coro
