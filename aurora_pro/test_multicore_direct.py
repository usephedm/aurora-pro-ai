"""Direct test of multicore manager."""
import asyncio
from multicore_manager import get_multicore_manager

async def test():
    m = get_multicore_manager(2)
    await m.start()
    print("Status:", m.get_status())
    print("Statistics:", m.get_statistics())
    await m.stop()

asyncio.run(test())