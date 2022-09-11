import asyncio
import ATMOV3

loop = asyncio.get_event_loop()
loop.run_until_complete(ATMOV3.main())
loop.close()
