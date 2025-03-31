import asyncio
import aiohttp
import time
import random
import logging
from datetime import datetime, timedelta

from apscheduler.triggers.date import DateTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from modules.database.models import async_main
from modules.database.queries import (
    save_proxy_data, 
    get_searcher_data, 
    sync_channels_from_json, 
    get_non_searcher_data,
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
from modules import proxy
from modules.settings import TZ
from modules.telegram import post_comment_for_order
from modules.log_handler import logger
from modules import settings
from pprint import pprint


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

    channels = await get_all_channels()

    categories = order.get('channel_category')

    categories = categories.split(',') if ',' in categories else [categories, ]
    
    channels_to_comment = [_ for _ in channels if _.get('category') in categories]

    accounts = await get_all_telegram_accounts_by_order_id(order_id=order_id)
    for account in accounts:

        created_at = datetime.fromisoformat(account.get('created_at')).replace(tzinfo=TZ)
        now = datetime.now(TZ)
        days_passed = (now - created_at).days
        ab = settings.DAYS_ACTIVE.get(str(days_passed), None)
        if not ab:
            ab = settings.DAYS_ACTIVE.get('6')
        
        run_timies = []
        for _ in range(random.randint(*ab)):
            random.shuffle(channels_to_comment)

            seconds_since_midnight = get_seconds_since_midnight()
            remaining_seconds = 86400 - seconds_since_midnight
            delay = random.gauss(
                remaining_seconds // 2,  # Среднее
                remaining_seconds // 4,  # Стандартное отклонение
            )

            delay = max(0, min(remaining_seconds, delay))

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
            
            scheduler.add_job(
                post_comment_for_order, 
                args=[channels_to_comment, order, account], 
                trigger=DateTrigger(run_date=run_time), 
            )


async def orders_handler():
    scheduler = AsyncIOScheduler()
    orders = await get_all_orders()

    active_orders = [order for order in orders if order.get('ordered_status') == 'active']
    for order in active_orders:
        channel_address = order.get('channel_address')
        order_id = order.get('id')

        if order.get('ordered_comment_posts') != None:
            if order.get('completed_comment_posts') >=\
                order.get('ordered_comment_posts'):
                await deactivate_order_by_channel_address(channel_address=channel_address)
                await unlink_account_to_order(order_id=order_id)
                continue

        if order.get('ordered_ad_days') != None:
            if order.get('completed_ad_days') >=\
                order.get('ordered_ad_days'):
                await deactivate_order_by_channel_address(channel_address=channel_address)
                await unlink_account_to_order(order_id=order_id)
                continue

        await run_order(order_id, scheduler)

    pending_orders = sorted(
        [order for order in orders if order.get('ordered_status') == 'pending'], 
        key=lambda x: x['id']
    )
    for order in pending_orders:
        accounts = await get_all_telegram_accounts()
        order_accounts_count = order.get('accounts_count')
        order_id = order.get('id')

        free_accounts = [account for account in accounts if account.get('current_order_id') == None]
        if len(free_accounts) < order_accounts_count:
            break
        
        for account in free_accounts:
            await link_account_to_order(account_id=account.get('id'), order_id=order_id)
        
        await activate_order_by_id(id=order_id)
        await run_order(order_id, scheduler)

    scheduler.start()


async def main():
    logger.info('DB init.')
    await async_main()
    while True:
        logger.info('Init scheduler for orders.')
        await orders_handler()
        seconds_since_midnight = get_seconds_since_midnight()
        remaining_seconds = 86400 - seconds_since_midnight

        logger.info(
            f'Current time: {datetime.now(TZ).strftime("%H:%M")}. Sleeping: {round(remaining_seconds / 3600, 2)} hours.'
        )
        
        await asyncio.sleep(remaining_seconds)


if __name__ == '__main__':
    logger.info('TGK start.')
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info('TGK stop')
