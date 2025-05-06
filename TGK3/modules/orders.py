import random
from pprint import pprint
from datetime import datetime, timedelta

from apscheduler.triggers.date import DateTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from modules.database import queries 
from modules import account as acc
from modules import scripts
import settings
from modules.logger import logger


async def start_orders():
    scheduler = AsyncIOScheduler()
    orders = await queries.get_all_orders()
    accounts = await queries.get_all_telegram_accounts()

    active_orders = []
    for order in orders:
        if order.get('ordered_status') == 'active':
            active_orders.append(order)
    
    pending_orders = []
    for order in orders:
        if order.get('ordered_status') == 'pending':
            pending_orders.append(order)
    pending_orders = sorted(pending_orders, key=lambda x: x['id'])

    free_accounts = []
    for account in accounts:
        if account.get('current_order_id') == None:
            free_accounts.append(account)
    random.shuffle(free_accounts)

    for order in active_orders:
        channel_address = order.get('channel_address')
        order_id = order.get('id')

        if order.get('ordered_comment_posts') != None:
            if order.get('completed_comment_posts') >=\
                order.get('ordered_comment_posts'):
                await queries.deactivate_order_by_order_id(order_id=order_id)
                await queries.unlink_account_to_order(order_id=order_id)
                continue

        if order.get('ordered_ad_days') != None:
            if order.get('completed_ad_days') >=\
                order.get('ordered_ad_days'):
                await queries.deactivate_order_by_order_id(order_id=order_id)
                await queries.unlink_account_to_order(order_id=order_id)
                continue
        
        await queries.increment_completed_ad_days(order_id=order_id)
        await add_order_to_scheduler(order, scheduler)

    for order in pending_orders:
        if order.get('accounts_count') > len(free_accounts):
            continue

        for index, account in enumerate(free_accounts):
            if index + 1 > order.get('accounts_count'):
                break
            await queries.link_account_to_order(account_id=account.get('id'), order_id=order.get('id'))

        await queries.activate_order_by_id(order.get('id')) 
        await queries.increment_completed_ad_days(order_id=order.get('id'))
        await add_order_to_scheduler(order, scheduler)

    scheduler.start()


async def add_order_to_scheduler(order: dict, scheduler: AsyncIOScheduler):
    channels = await queries.get_all_channels() 

    order_categories = []
    for category in order.get('channel_category'):
        order_categories.append(category.get('name'))

    channels_to_comment = []
    for channel in channels:
        if channel.get('category').get('name') in order_categories:
            channels_to_comment.append(channel)

    accounts = await queries.get_all_telegram_accounts_by_order_id(order_id=order.get("id")) 
    for account in accounts:
        created_at = datetime.fromisoformat(account.get('created_at')).replace(tzinfo=settings.TZ)
        now = datetime.now(settings.TZ)
        days_passed = (now - created_at).days
        ab = settings.DAYS_ACTIVE.get(str(days_passed), None)
        if not ab:
            ab = settings.DAYS_ACTIVE.get('6')
        
        run_timies = []
        for _ in range(random.randint(*ab)):
            random_channels_to_comment = channels_to_comment.copy()
            random.shuffle(random_channels_to_comment)

            seconds_until_next_iteration = 86_400 - scripts.get_seconds_since_midnight()
            delay = random.gauss(
                seconds_until_next_iteration // 2,
                seconds_until_next_iteration // 4
            )

            if settings.DEBUG:
                delay = 1
            
            run_time = datetime.now(settings.TZ) + timedelta(seconds=delay)

            if run_time.strftime('%H:%M') in run_timies:
                continue
            
            run_timies.append(run_time.strftime('%H:%M'))

            scheduler.add_job(
                acc.init_account, 
                args=[random_channels_to_comment, order, account],
                trigger=DateTrigger(run_date=run_time)
            )
