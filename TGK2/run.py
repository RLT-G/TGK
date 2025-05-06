import asyncio
import random
from datetime import datetime, timedelta

from apscheduler.triggers.date import DateTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from modules.database.models import async_main
from modules.database.queries import (
    get_all_orders,
    get_all_channels,
    get_all_telegram_accounts,
    deactivate_order_by_channel_address,
    link_account_to_order,
    activate_order_by_id,
    unlink_account_to_order,
    get_order_by_id,
    get_all_telegram_accounts_by_order_id
)
from modules.settings import TZ, DEBUG
from modules.telegram import post_comment_for_order
from modules.log_handler import logger
from modules import settings


def get_seconds_since_midnight():
    """Возвращает количество секунд с полуночи в Московском часовом поясе."""
    now = datetime.now(TZ)
    midnight = datetime.combine(now.date(), datetime.min.time(), tzinfo=TZ)
    seconds_since_midnight = (now - midnight).seconds
    return int(seconds_since_midnight)


def seconds_to_time(seconds):
    """Преобразует количество секунд в формат HH:MM."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:02}:{minutes:02}"


async def run_order(order_id, scheduler):
    order = await get_order_by_id(order_id=order_id)
    # list of channels
    channels = await get_all_channels() 
    # list of order categories 
    categories = [category.get('name') for category in order.get('channel_category')]
    # list of channels with order categories 
    channels_to_comment = [
        channel for channel in channels if channel.get('category').get('name') in categories
    ]
    # list of accounts on current order
    accounts = await get_all_telegram_accounts_by_order_id(order_id=order_id)
    for account in accounts:
        # Decreased activity in the first days
        created_at = datetime.fromisoformat(account.get('created_at')).replace(tzinfo=TZ)
        now = datetime.now(TZ)
        days_passed = (now - created_at).days
        ab = settings.DAYS_ACTIVE.get(str(days_passed), None)
        if not ab:
            ab = settings.DAYS_ACTIVE.get('6')
        
        run_timies = []
        for _ in range(random.randint(*ab)):
            random.shuffle(channels_to_comment)

            # Calculate time to comment
            seconds_since_midnight = get_seconds_since_midnight()
            remaining_seconds = 86400 - seconds_since_midnight
            delay = random.gauss(
                remaining_seconds // 2,  
                remaining_seconds // 4,
            )
            # Checks
            delay = max(0, min(remaining_seconds, delay))

            if DEBUG:
                delay = 1

            run_time = datetime.now(TZ) + timedelta(seconds=delay)

            if run_time.strftime('%H:%M') == '00:00':
                continue
            
            if run_time.strftime('%H:%M') in run_timies:
                continue

            run_timies.append(run_time.strftime('%H:%M'))

            logger.debug(
                f"{account.get('username')} started at {run_time.strftime('%Y-%m-%d %H:%M')}"
            )
            # Add job to scheduler 
            scheduler.add_job(
                post_comment_for_order, 
                args=[channels_to_comment, order, account], 
                trigger=DateTrigger(run_date=run_time), 
            )


async def orders_handler():
    scheduler = AsyncIOScheduler()
    orders = await get_all_orders() 

    active_orders = [order for order in orders if order.get('ordered_status') == 'active'] # all acive orders
    for order in active_orders:
        channel_address = order.get('channel_address')
        order_id = order.get('id')

        # Check count of completed comments and unlink accounts from orders
        if order.get('ordered_comment_posts') != None:
            if order.get('completed_comment_posts') >=\
                order.get('ordered_comment_posts'):
                await deactivate_order_by_channel_address(channel_address=channel_address)
                await unlink_account_to_order(order_id=order_id)
                continue

        # Check count of completed days and unlink accounts from orders
        if order.get('ordered_ad_days') != None:
            if order.get('completed_ad_days') >=\
                order.get('ordered_ad_days'):
                await deactivate_order_by_channel_address(channel_address=channel_address)
                await unlink_account_to_order(order_id=order_id)
                continue
        
        # Add to scheduler active order
        await run_order(order_id, scheduler)

    # all pending orders
    pending_orders = sorted(
        [order for order in orders if order.get('ordered_status') == 'pending'], 
        key=lambda x: x['id']
    )
    for order in pending_orders:
        accounts = await get_all_telegram_accounts()
        order_accounts_count = order.get('accounts_count')
        order_id = order.get('id')

        # if count of free accounts >= accounts count to order linked accs to order (list of order not sorted)
        free_accounts = [account for account in accounts if account.get('current_order_id') == None]
        if len(free_accounts) < order_accounts_count:
            break
        
        for index, account in enumerate(free_accounts):
            if index + 1 == int(order_accounts_count):
                break

            await link_account_to_order(account_id=account.get('id'), order_id=order_id)
        
        # Activate and add to scheduler pending order
        await activate_order_by_id(id=order_id)
        await run_order(order_id, scheduler)

    # Run all active orders
    scheduler.start()


async def main():
    logger.info('DB init.')
    await async_main() # init database
    while True:
        logger.info('Init scheduler for orders.')
        await orders_handler() # start order handler
        seconds_since_midnight = get_seconds_since_midnight() # culc time since midnight to sleep
        remaining_seconds = 86400 - seconds_since_midnight
        logger.info(
            f'Current time: {datetime.now(TZ).strftime("%H:%M")}. Sleeping: {round(remaining_seconds / 3600, 2)} hours.'
        )
        await asyncio.sleep(remaining_seconds) # sleep to 0:00


if __name__ == '__main__':
    logger.info('TGK start.')
    try:
        # run main handler
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info('TGK stop')
