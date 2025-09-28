import asyncio
import threading
from typing import Awaitable, Any

class AsyncRunner:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._start_loop, daemon=True)
        self.thread.start()
        self.initialized = False

    def _start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run_coroutine(self, coro: Awaitable[Any]):
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    def shutdown(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()
