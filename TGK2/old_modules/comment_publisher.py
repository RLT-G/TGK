# import asyncio
# from telethon import TelegramClient
# from telethon.errors import ChatWriteForbiddenError, UserNotParticipantError
# from telethon.tl.functions.channels import JoinChannelRequest, GetParticipantRequest
# from telethon.tl.functions.messages import GetHistoryRequest

# from modules import settings


# async def comment_on_post(account: dict, channel: str, discussion_group_id: int, discussion_id: int, comment_text: str, delay: int) -> bool | None:
#     print('Зашел в comment_on_post')

#     await asyncio.sleep(delay)

#     api_id = account['api_id']
#     api_hash = account['api_hash']
#     phone_number = account['phone_number']['number']
    
#     client = TelegramClient(f"./sessions/{api_id}{api_hash}{phone_number[1:]}", api_id, api_hash, system_version='4.16.30-vxCUSTOM')
    
#     try:
#         await client.connect()
#         if not await client.is_user_authorized():
#             await client.send_code_request(phone_number)
#             code = input('Введите код: ')
#             await client.sign_in(phone_number, code)

#         # Получаем объект группы обсуждения
#         try:
#             discussion_group = await client.get_entity(discussion_group_id)
#             discussion_group_input = await client.get_input_entity(discussion_group)
#         except Exception as e:
#             print(f"Ошибка: не удалось найти группу обсуждения {discussion_group_id}: {e}")
#             return

#         # Проверяем, состоит ли бот в группе обсуждения
#         try:
#             await client(GetParticipantRequest(discussion_group_input, 'me'))
#         except UserNotParticipantError:
#             try:
#                 await client(JoinChannelRequest(discussion_group_input))
#                 print(f"Успешно присоединились к группе обсуждения {discussion_group_id}")
#             except Exception as e:
#                 print(f"Не удалось присоединиться к группе обсуждения {discussion_group_id}: {e}")
#                 return

#         # Отправляем комментарий
#         try:
#             await client.send_message(discussion_group_input, comment_text, reply_to=discussion_id)
#             print(f"Комментарий отправлен к посту {discussion_id} в канале {discussion_group_id}")
#             return True
#         except ChatWriteForbiddenError:
#             print(f"Бот не может писать в группу обсуждения {discussion_group_id}. Проверьте права доступа.")
#         except Exception as e:
#             print(f"Ошибка при комментировании поста {discussion_id} в канале {discussion_group_id}: {e}")

#     finally:
#         await client.disconnect()

import asyncio

from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.errors import ChatWriteForbiddenError
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.errors import UserNotParticipantError
from telethon.tl.functions.channels import JoinChannelRequest, GetParticipantRequest
from pprint import pprint
from telethon import functions, types

from modules import settings


async def comment_on_post(
        account: dict, 
        channel: str, 
        discussion_group_id: int, 
        discussion_id: int, 
        comment_text: str, 
        delay: int
    ) -> bool | None:
    

    await asyncio.sleep(delay)

    api_id = account['api_id']
    api_hash = account['api_hash']
    phone_number = account['phone_number']['number']
    
    client = TelegramClient(f"./sessions/{api_id}{api_hash}{phone_number[1:]}", api_id, api_hash, system_version='4.16.30-vxCUSTOM')
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            await client.send_code_request(phone_number)
            code = input('Введите код: ')
            await client.sign_in(phone_number, code)

        entity = await client.get_entity(channel)
        full_channel = await client(GetFullChannelRequest(entity))

        if not full_channel.full_chat or not full_channel.full_chat.linked_chat_id:
            print(f"У канала {channel} нет привязанной группы обсуждения.")
        
        discussion_group_id = full_channel.full_chat.linked_chat_id
        
        try:
            await client(GetParticipantRequest(discussion_group_id, 'me'))
        except UserNotParticipantError:
            try:
                await client(JoinChannelRequest(discussion_group_id))
                print(f"Успешно присоединились к группе обсуждения {discussion_group_id}")
            except Exception as e:
                print(f"Не удалось присоединиться к группе обсуждения {discussion_group_id}: {e}")
                return
        
        try:
            await client.send_message(discussion_group_id, comment_text, reply_to=discussion_id)
            print(f"Комментарий отправлен к посту {discussion_id} в канале {discussion_group_id}")
            return True
        except ChatWriteForbiddenError:
            print(f"Бот не может писать в группу обсуждения {discussion_group_id}. Проверьте права доступа.")
        except Exception as e:
            print(f"Ошибка при комментировании поста {discussion_id} в канале {discussion_group_id}: {e}")

    finally:
        await client.disconnect()



