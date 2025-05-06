import asyncio
import time
from celery import shared_task
from telethon import TelegramClient
from asgiref.sync import sync_to_async
import os


@sync_to_async
def get_phone_number(account):
    if account.phone_number:
        return account.phone_number.number
    else:
        raise ValueError("Phone number is not set for this account.")

@sync_to_async
def get_auth_code(account):
    return account.auth_code

@sync_to_async
def refresh_account(account):
    account.refresh_from_db()
    return account

@sync_to_async
def save_account(account):
    account.save()

@shared_task
def connect_telegram_account(account_id):
    from .models import TelegramAccount

    account = TelegramAccount.objects.get(id=account_id)

    async def init_connect(account):
        phone_number = await get_phone_number(account)

        if phone_number is None:
            raise ValueError(f"Phone number is not set for account with ID {account_id}")
        
        client = TelegramClient(
            f"../TGK3/sessions/{account.api_id}{account.api_hash}{str(phone_number)[1:]}", 
            account.api_id, 
            account.api_hash, 
            system_version='4.16.30-vxCUSTOM'
        )
        
        await client.connect()
        if not await client.is_user_authorized():

            await client.send_code_request(str(phone_number))
            
            start_time = time.time()
            while time.time() - start_time < 300: 
                account = await refresh_account(account)  
                auth_code = await get_auth_code(account)
                
                if auth_code:
                    await client.sign_in(str(phone_number), auth_code)
                    account.is_connected = True
                    await save_account(account)
                    await client.disconnect()
                    return
                
                await asyncio.sleep(5)
            
            account.delete()

        await client.disconnect()

    asyncio.run(init_connect(account))
