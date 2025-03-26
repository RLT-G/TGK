from telethon import TelegramClient
from telethon import functions
from telethon.tl.functions.channels import (
    JoinChannelRequest, 
    GetParticipantRequest, 
    GetFullChannelRequest
)
from telethon.errors import UserNotParticipantError

from modules.chatgpt import generate_comment, generate_about_text
from modules.log_handler import logger
from modules.database.queries import (
    get_order_by_channel_address, 
    deactivate_order_by_channel_address, 
    increment_completed_comment_posts, 
    create_comment_in_db, 
    get_about_data,
    get_numberphone_by_id
)
from pprint import pprint
import traceback


async def _init_block(account, order):
    try:
        phone_number = await get_numberphone_by_id(
            account.get('phone_number_id')
        )
        channel_address = order.get('channel_address')
        current_order_data = await get_order_by_channel_address(channel_address=channel_address)

        return [
            account.get('api_id'),
            account.get('api_hash'),
            phone_number,
            account.get('gender'),
            channel_address,
            current_order_data,
            order.get('channel_description')
        ]
    
    except Exception as ex:
        logger.error(f'_init_block: {ex}')
        return


async def _check_order_block(current_order_data: dict, channel_address: str) -> bool:
    try:
        if current_order_data.get('is_active') == False:
            return
        
        if current_order_data.get('ordered_comment_posts') != None:
            if current_order_data.get('completed_comment_posts') >=\
                current_order_data.get('ordered_comment_posts'):
                await deactivate_order_by_channel_address(channel_address=channel_address)
                return

        if current_order_data.get('ordered_ad_days') != None:
            if current_order_data.get('completed_ad_days') >=\
                current_order_data.get('ordered_ad_days'):
                await deactivate_order_by_channel_address(channel_address=channel_address)
                return
        
        return True
    
    except Exception as ex:
        logger.error(f'_check_order_block: {ex}')
        return


async def _change_about_block(client, api_id, api_hash, channel_address, gender, channel_description):
    try:
        about_text = await generate_about_text(gender, channel_address, channel_description)
        await client(functions.account.UpdateProfileRequest(about=about_text))

    except Exception as ex:
        logger.warning(f'_change_about_block: {ex}')


async def _post_data_block(client, channel_to_comment):
    try:
        telegram_link = channel_to_comment.get('telegram_link')
        entity = await client.get_entity(telegram_link)
        full_channel = await client(GetFullChannelRequest(entity))
        if not full_channel.full_chat or not full_channel.full_chat.linked_chat_id:
            return None

        discussion_group_id = full_channel.full_chat.linked_chat_id
        messages = await client.get_messages(entity, limit=50)
        for message in messages:
            if message and message.text:
                result = await client(functions.messages.GetDiscussionMessageRequest(
                    peer=telegram_link,
                    msg_id=message.id
                ))

                discussion_message = result.messages[0] if result.messages else None
                    
                if discussion_message:
                    return {
                        "discussion_group_id": discussion_group_id,
                        "last_post": {
                            'id': message.id,
                            'discussion_id': discussion_message.id,
                            'date': message.date,
                            'text': message.text,
                        }
                    }
        return None
    
    except Exception as ex:
        logger.warning(f'_post_data_block: {ex}')


async def _join_channel_block(client, discussion_group_id):
    try:
        await client(GetParticipantRequest(discussion_group_id, 'me'))
        return True
    
    except UserNotParticipantError:
        try:
            await client(JoinChannelRequest(discussion_group_id))
            return True
        
        except Exception as ex:
            logger.warning(f'_join_channel_block: {ex}')
            return


async def _send_comment_block(
    order,
    client,
    api_id,
    account,
    api_hash,
    post_data, 
    comment_text, 
    channel_address,
    channel_to_comment,
):
    try:

        message = await client.send_message(
            post_data.get('discussion_group_id'),
            comment_text, 
            reply_to=post_data.get('last_post').get('discussion_id')
        )
        comment_link = None
        try:
            chat = await client.get_entity(post_data.get('discussion_group_id'))
            group_link = f"https://t.me/{chat.username}"
            comment_link = f"{group_link}/{message.id}"
        except Exception as ex:
            ...

        await increment_completed_comment_posts(channel_address=channel_address)
        await create_comment_in_db(
            api_hash=api_hash,
            api_id=api_id,
            channel_link=channel_to_comment.get('telegram_link'),
            text=comment_text,
            comment_link=comment_link
        )
        await client.disconnect()
        
        logger.debug(
            f'Comment by {account.get('username')} made on {channel_address} and saved in DB.'
        )

        return True
        
    except Exception as ex:
        logger.warning(
            f'Comment by {account.get('username')} dont made on {channel_address}. Error: {ex}'
        )
        return
        

async def post_comment_for_order(channels_to_comment, order, account):


    init_data = await _init_block(account, order) # Получаем начальные данные
    if not init_data:
        return
    api_id, api_hash, phone_number, gender, channel_address, current_order_data, channel_description = init_data


    # order_is_normal = await _check_order_block(current_order_data, channel_address) # Проверяем статус заказа
    # if not order_is_normal:
    #     return
    
    try:
        client = TelegramClient(
            f"./sessions/{api_id}{api_hash}{phone_number[1::]}", 
            api_id, 
            api_hash, 
            system_version='4.16.30-vxCUSTOM'
        ) # Подключаемся
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            raise Exception('Auth failed')

        await _change_about_block(client, api_id, api_hash, channel_address, gender, channel_description) # Меняем About 

        for channel_to_comment in channels_to_comment:
            post_data = await _post_data_block(client, channel_to_comment) # Получаем инфу по ласт посту в канале
            if not post_data:
                continue
            discussion_group_id = post_data.get('discussion_group_id')

            is_joined = await _join_channel_block(client, discussion_group_id) # Пытаемся подключиться в группу
            if not is_joined:
                continue
            
            comment_text = await generate_comment(
                post_text=post_data.get('last_post').get('text'),
                gender=('Мужчина' if gender == 'M' else 'Женщина')
            ) # Генерим коммент

            comment_is_made = await _send_comment_block(
                order=order,
                client=client,
                api_id=api_id,
                account=account,
                api_hash=api_hash,
                post_data=post_data,
                comment_text=comment_text,
                channel_address=channel_address,
                channel_to_comment=channel_to_comment
            ) # Отправляем коммент

            if comment_is_made:
                break

        await client.disconnect()

    except Exception as ex:
        logger.error(f'post_comment_for_order (Comment part): {ex}')
        traceback.print_exc()

    
    

    


# async def post_comment_for_order(channels_to_comment, order):
#     try:
#         api_id = order.get('telegram_account').get('api_id')
#         api_hash = order.get('telegram_account').get('api_hash')
#         phone_number = order.get('telegram_account').get('phone_number').get('number')
#         gender = order.get('telegram_account').get('gender')
#         channel_address = order.get('channel_address')
#         current_order_data = await get_order_by_channel_address(channel_address=channel_address)
#     except Exception as ex:
#         logger.error(f'post_comment_for_order (init block): {ex}')

#     try:
#         if current_order_data.get('is_active') == False:
#             return
        
#         if current_order_data.get('ordered_comment_posts') != None:
#             if current_order_data.get('completed_comment_posts') >=\
#                 current_order_data.get('ordered_comment_posts'):
#                 await deactivate_order_by_channel_address(channel_address=channel_address)
#                 return

#         if current_order_data.get('ordered_ad_days') != None:
#             if current_order_data.get('completed_ad_days') >=\
#                 current_order_data.get('ordered_ad_days'):
#                 await deactivate_order_by_channel_address(channel_address=channel_address)
#                 return
            
#     except Exception as ex:
#         logger.error(f'post_comment_for_order (check order block): {ex}')

#     try:
#         client = TelegramClient(
#             f"./sessions/{api_id}{api_hash}{phone_number[1::]}", 
#             api_id, 
#             api_hash, 
#             system_version='4.16.30-vxCUSTOM'
#         )
#         await client.connect()
#         if not await client.is_user_authorized():
#             raise Exception('Auth failed')

#         try:
#             about = await get_about_data(api_hash=api_hash, api_id=api_id)
#             about_with_order_link = str(about).replace('{}', str(channel_address))
#             await client(functions.account.UpdateProfileRequest(about=about_with_order_link))

#         except Exception as ex:
#             logger.warning(f'post_comment_for_order (Chnage about info): {ex}')

#         for channel_to_comment in channels_to_comment:
#             try:
#                 telegram_link = channel_to_comment.get('telegram_link')
#                 entity = await client.get_entity(telegram_link)
#                 full_channel = await client(GetFullChannelRequest(entity))
#                 if not full_channel.full_chat or not full_channel.full_chat.linked_chat_id:
#                     continue

#                 discussion_group_id = full_channel.full_chat.linked_chat_id
#                 posts_data = {
#                     "discussion_group_id": discussion_group_id,
#                     "last_post": None
#                 }
#                 messages = await client.get_messages(entity, limit=50)
#                 for message in messages:
#                     if message and message.text:
#                         result = await client(functions.messages.GetDiscussionMessageRequest(
#                             peer=telegram_link,
#                             msg_id=message.id
#                         ))

#                         discussion_message = result.messages[0] if result.messages else None
                            
#                         if discussion_message:
#                             posts_data['last_post'] = {
#                                 'id': message.id,
#                                 'discussion_id': discussion_message.id,
#                                 'date': message.date,
#                                 'text': message.text,
#                             }
#                             break
                
#                 if posts_data.get('last_post') == None:
#                     continue
                
#                 try:
#                     await client(GetParticipantRequest(discussion_group_id, 'me'))
#                 except UserNotParticipantError:
#                     try:
#                         await client(JoinChannelRequest(discussion_group_id))
#                     except Exception as e:
#                         continue
                
#                 comment_text = await generate_comment(
#                     post_text=posts_data.get('last_post').get('text'),
#                     gender=('Мужчина' if gender == 'M' else 'Женщина')
#                 )

#                 try:
#                     await client.send_message(
#                         posts_data.get('discussion_group_id'),
#                         comment_text, 
#                         reply_to=posts_data.get('last_post').get('discussion_id')
#                     )
#                     await increment_completed_comment_posts(channel_address=channel_address)
#                     await create_comment_in_db(
#                         api_hash=api_hash,
#                         api_id=api_id,
#                         channel_link=telegram_link,
#                         text=comment_text
#                     )
#                     await client.disconnect()
                    
#                     logger.debug(
#                         f'Comment by {order.get('telegram_account').get('username')} made on {channel_address} and saved in DB.'
#                     )

#                     return
                
#                 except Exception as ex:
#                     logger.warning(
#                         f'Comment by {order.get('telegram_account').get('username')} dont made on {channel_address}. Error: {ex}'
#                     )

#             except Exception as ex:
#                 logger.warning(f'post_comment_for_order (For channel part): {ex}')

#         await client.disconnect()

#     except Exception as ex:
#         logger.error(f'post_comment_for_order (Comment part): {ex}')

    
    

    


