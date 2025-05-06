import asyncio
import random

from modules.logger import logger
from modules import scripts
from modules import orders
from modules.database.models import async_main
import settings


async def main() -> None:
    await async_main() 
    while True:
        await orders.start_orders()
        wait_time: int = 86_400 - scripts.get_seconds_since_midnight() 
        logger.info(f"Sleep {wait_time // 3600} hours")
        await asyncio.sleep(wait_time)


if __name__ == "__main__":
    try:
        logger.info('TGK start')
        asyncio.run(main())
    except KeyboardInterrupt:
        ...
