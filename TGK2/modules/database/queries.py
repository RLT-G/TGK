from datetime import datetime
import json

from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select as future_select
from sqlalchemy.exc import NoResultFound
from sqlalchemy import and_

from modules.database.models import async_session
from modules.database.models import (
    Proxy, 
    TelegramAccount,
    Channel,
    Comment,
    PhoneNumber,
    Order
)


async def get_searcher_data():
    async with async_session() as session:
        stmt = future_select(TelegramAccount).filter(TelegramAccount.is_searcher == True).limit(1).options(
            selectinload(TelegramAccount.phone_number),
            selectinload(TelegramAccount.proxy)
        )
        
        result = await session.execute(stmt)
        telegram_account = result.scalars().first()  
        
        if telegram_account:
            return {
                'id': telegram_account.id,
                'username': telegram_account.username,
                'gender': telegram_account.gender,
                'api_id': telegram_account.api_id,
                'api_hash': telegram_account.api_hash,
                'phone_number': {
                    'id': telegram_account.phone_number.id,
                    'number': telegram_account.phone_number.number,
                    'country': telegram_account.phone_number.country,
                    'is_used': telegram_account.phone_number.is_used,
                    'received_code': telegram_account.phone_number.received_code,
                } if telegram_account.phone_number else None,
                'proxy': {
                    'id': telegram_account.proxy.id,
                    'version': telegram_account.proxy.version,
                    'ip': telegram_account.proxy.ip,
                    'host': telegram_account.proxy.host,
                    'port': telegram_account.proxy.port,
                    'user': telegram_account.proxy.user,
                    'password': telegram_account.proxy.password,
                    'date': telegram_account.proxy.date,
                    'date_end': telegram_account.proxy.date_end,
                    'active': telegram_account.proxy.active,
                    'country': telegram_account.proxy.country,
                    'is_linked': telegram_account.proxy.is_linked
                } if telegram_account.proxy else None
            }
        return





async def get_non_searcher_data():
    async with async_session() as session:
        # Запрос на получение всех аккаунтов с is_searcher=False
        stmt = select(TelegramAccount).filter(TelegramAccount.is_searcher == False).options(
            selectinload(TelegramAccount.phone_number),
            selectinload(TelegramAccount.proxy)
        )
        
        result = await session.execute(stmt)
        telegram_accounts = result.scalars().all()
        
        # Возвращаем список данных для всех аккаунтов
        accounts_data = []
        for telegram_account in telegram_accounts:
            account_data = {
                'id': telegram_account.id,
                'username': telegram_account.username,
                'gender': telegram_account.gender,
                'api_id': telegram_account.api_id,
                'api_hash': telegram_account.api_hash,
                'phone_number': {
                    'id': telegram_account.phone_number.id,
                    'number': telegram_account.phone_number.number,
                    'country': telegram_account.phone_number.country,
                    'is_used': telegram_account.phone_number.is_used,
                    'received_code': telegram_account.phone_number.received_code,
                } if telegram_account.phone_number else None,
                'proxy': {
                    'id': telegram_account.proxy.id,
                    'version': telegram_account.proxy.version,
                    'ip': telegram_account.proxy.ip,
                    'host': telegram_account.proxy.host,
                    'port': telegram_account.proxy.port,
                    'user': telegram_account.proxy.user,
                    'password': telegram_account.proxy.password,
                    'date': telegram_account.proxy.date,
                    'date_end': telegram_account.proxy.date_end,
                    'active': telegram_account.proxy.active,
                    'country': telegram_account.proxy.country,
                    'is_linked': telegram_account.proxy.is_linked
                } if telegram_account.proxy else None
            }
            accounts_data.append(account_data)

        return accounts_data


async def save_proxy_data(proxy_data: dict, proxy_country: str):
    async with async_session() as session:
        async with session.begin():
            for proxy in proxy_data.values():
                existing_proxy = await session.get(Proxy, proxy['id'])
                if existing_proxy:
                    existing_proxy.version = proxy['version']
                    existing_proxy.ip = proxy['ip']
                    existing_proxy.host = proxy['host']
                    existing_proxy.port = proxy['port']
                    existing_proxy.user = proxy['user']
                    existing_proxy.password = proxy['pass']
                    existing_proxy.date = datetime.strptime(proxy['date'], '%Y-%m-%d %H:%M:%S')
                    existing_proxy.date_end = datetime.strptime(proxy['date_end'], '%Y-%m-%d %H:%M:%S')
                    existing_proxy.port = proxy_country,
                    existing_proxy.active = proxy['active'] == '1'
                else:
                    new_proxy = Proxy(
                        id=proxy['id'],
                        version=proxy['version'],
                        ip=proxy['ip'],
                        host=proxy['host'],
                        port=proxy['port'],
                        user=proxy['user'],
                        password=proxy['pass'],
                        date=datetime.strptime(proxy['date'], '%Y-%m-%d %H:%M:%S'),
                        date_end=datetime.strptime(proxy['date_end'], '%Y-%m-%d %H:%M:%S'),
                        country=proxy_country,
                        active=proxy['active'] == '1'
                    )
                    session.add(new_proxy)
        await session.commit()


async def get_all_channels():
    async with async_session() as session:
        stmt = select(Channel)
        result = await session.execute(stmt)
        channels = result.scalars().all()

        channels_list = [
            {
                'id': channel.id,
                'telegram_link': channel.telegram_link,
                'category': channel.category,
            }
            for channel in channels
        ]
        
    return channels_list


async def sync_channels_from_json(file_path: str):
    with open(file_path, 'r') as file:
        new_channels_data = json.load(file)

    async with async_session() as session:
        async with session.begin():
            # Шаг 1: Получаем все текущие каналы из базы данных
            stmt = select(Channel)
            result = await session.execute(stmt)
            existing_channels = result.scalars().all()

            # Шаг 2: Преобразуем текущие каналы в словарь для быстрой проверки
            existing_channels_dict = {channel.telegram_link: channel for channel in existing_channels}

            # Шаг 3: Сверяем каналы
            for new_channel_data in new_channels_data:
                # Проверка, если канал уже существует в базе
                existing_channel = existing_channels_dict.get(new_channel_data['telegram_link'])

                if existing_channel:
                    # Если канал существует, проверяем, нужно ли его обновлять
                    if (existing_channel.category != new_channel_data['category']):
                        # Обновляем канал
                        existing_channel.category = new_channel_data['category']
                        print(f"Updated channel: {existing_channel.telegram_link}")
                else:
                    # Если канала нет в базе данных, добавляем новый
                    new_channel = Channel(
                        telegram_link=new_channel_data['telegram_link'],
                        category=new_channel_data.get('category', None),
                    )
                    session.add(new_channel)
                    print(f"Added new channel: {new_channel.telegram_link}")

            # Шаг 4: Удаляем каналы, которых нет в JSON
            for existing_channel in existing_channels:
                if existing_channel.telegram_link not in [channel['telegram_link'] for channel in new_channels_data]:
                    await session.execute(delete(Channel).filter(Channel.id == existing_channel.id))
                    print(f"Deleted channel: {existing_channel.telegram_link}")

        # Коммит изменений в базу данных
        await session.commit()


async def get_all_orders():
    async with async_session() as session:
        stmt = select(Order)
        
        result = await session.execute(stmt)
        orders = result.scalars().all()
        
        orders_data = []
        for order in orders:
            order_data = {
                'id': order.id,
                'created_at': order.created_at,
                'channel_address': order.channel_address,
                'channel_description': order.channel_description,
                'channel_category': order.channel_category,
                'ordered_comment_posts': order.ordered_comment_posts,
                'completed_comment_posts': order.completed_comment_posts,
                'ordered_ad_days': order.ordered_ad_days,
                'completed_ad_days': order.completed_ad_days,
                'is_active': order.is_active,
                'accounts_count': order.accounts_count,
                'ordered_status': order.ordered_status
            }
            orders_data.append(order_data)

        return orders_data

async def get_order_by_id(order_id: int):
    async with async_session() as session:
        result = await session.execute(select(Order).filter(Order.id == order_id))
        order = result.scalars().first()
        order_data = {
            'id': order.id,
            'created_at': order.created_at,
            'channel_address': order.channel_address,
            'channel_description': order.channel_description,
            'channel_category': order.channel_category,
            'ordered_comment_posts': order.ordered_comment_posts,
            'completed_comment_posts': order.completed_comment_posts,
            'ordered_ad_days': order.ordered_ad_days,
            'completed_ad_days': order.completed_ad_days,
            'is_active': order.is_active,
            'accounts_count': order.accounts_count,
            'ordered_status': order.ordered_status
        }
        return order_data


async def get_all_telegram_accounts():
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(TelegramAccount))
            accounts = result.scalars().all()
            
            accounts_list = []
            for account in accounts:
                accounts_list.append({
                    "id": account.id,
                    "username": account.username,
                    "phone_number_id": account.phone_number_id,
                    "proxy_id": account.proxy_id,
                    "gender": account.gender,
                    "description": account.description,
                    "is_banned": account.is_banned,
                    "created_at": account.created_at.isoformat() if account.created_at else None,
                    "api_id": account.api_id,
                    "api_hash": account.api_hash,
                    "is_searcher": account.is_searcher,
                    "is_connected": account.is_connected,
                    "auth_code": account.auth_code,
                    "current_order_id": account.current_order_id,
                })
            
            return accounts_list


async def get_all_telegram_accounts_by_order_id(order_id):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(TelegramAccount).filter_by(current_order_id=order_id))
            accounts = result.scalars().all()
            
            accounts_list = []
            for account in accounts:
                accounts_list.append({
                    "id": account.id,
                    "username": account.username,
                    "phone_number_id": account.phone_number_id,
                    "proxy_id": account.proxy_id,
                    "gender": account.gender,
                    "description": account.description,
                    "is_banned": account.is_banned,
                    "created_at": account.created_at.isoformat() if account.created_at else None,
                    "api_id": account.api_id,
                    "api_hash": account.api_hash,
                    "is_searcher": account.is_searcher,
                    "is_connected": account.is_connected,
                    "auth_code": account.auth_code,
                    "current_order_id": account.current_order_id,
                })
            
            return accounts_list


async def get_order_by_channel_address(channel_address: str):
    async with async_session() as session:
        stmt = select(Order).filter(Order.channel_address == channel_address)
        
        result = await session.execute(stmt)
        order = result.scalars().first()

        if not order:
            return None  

        order_data = {
            'id': order.id,
            'created_at': order.created_at,
            'channel_address': order.channel_address,
            'channel_description': order.channel_description,
            'channel_category': order.channel_category,
            'ordered_comment_posts': order.ordered_comment_posts,
            'completed_comment_posts': order.completed_comment_posts,
            'ordered_ad_days': order.ordered_ad_days,
            'completed_ad_days': order.completed_ad_days,
            'is_active': order.is_active,
        }

        return order_data


async def deactivate_order_by_channel_address(channel_address: str):
    async with async_session() as session:
        stmt = select(Order).filter(Order.channel_address == channel_address)
        result = await session.execute(stmt)
        order = result.scalars().first()

        if not order:
            return None

        order.ordered_status = 'completed'
        await session.commit()


async def activate_order_by_id(id: int):
    async with async_session() as session:
        stmt = select(Order).filter(Order.id == id)
        result = await session.execute(stmt)
        order = result.scalars().first()

        if not order:
            return None

        order.ordered_status = 'active'
        await session.commit()


async def get_numberphone_by_id(id: int):
    async with async_session() as session:
        stmt = select(PhoneNumber).filter(PhoneNumber.id == id)
        result = await session.execute(stmt)
        number = result.scalars().first()
        return number.number


async def increment_completed_comment_posts(channel_address: str):
    async with async_session() as session:
        stmt = select(Order).filter(Order.channel_address == channel_address)
        result = await session.execute(stmt)
        order = result.scalars().first()

        if not order:
            return None

        order.completed_comment_posts = int(order.completed_comment_posts) + 1
        await session.commit()


async def create_comment_in_db(api_hash: str, api_id: str, channel_link: str, text: str, comment_link: str):
    async with async_session() as session:
        stmt = select(TelegramAccount).filter(
            and_(TelegramAccount.api_id == api_id, TelegramAccount.api_hash == api_hash)
        )
        result = await session.execute(stmt)
        telegram_account = result.scalars().first()
        
        if not telegram_account:
            return
        
        # Создаем новую запись в Comment
        new_comment = Comment(
            telegram_account_id=telegram_account.id,
            channel_link=channel_link,
            text=text,
            comment_link=comment_link,
            posted_at=datetime.utcnow()
        )
        session.add(new_comment)
        await session.commit()
        
        return


async def get_about_data(api_hash: str, api_id: str):
    async with async_session() as session:
        stmt = select(TelegramAccount).filter(
            and_(TelegramAccount.api_id == api_id, TelegramAccount.api_hash == api_hash)
        )
        result = await session.execute(stmt)
        telegram_account = result.scalars().first()
        
        if not telegram_account:
            return
        
        description = telegram_account.description
        
        return description
    

async def link_account_to_order(account_id: int, order_id: int):
    async with async_session() as session:
        result = await session.execute(select(TelegramAccount).filter_by(id=account_id))
        account = result.scalar_one_or_none()

        if not account:
            return

        result = await session.execute(select(Order).filter_by(id=order_id))
        order = result.scalar_one_or_none()

        if not order:
            return
        
        account.current_order_id = order.id

        await session.commit()

        return account
    

async def unlink_account_to_order(order_id: int):
    async with async_session() as session:
        result = await session.execute(select(TelegramAccount).filter_by(current_order_id=order_id))
        accounts = await result.scalars().all()

        for account in accounts:
            account.current_order_id = None

        await session.commit()
