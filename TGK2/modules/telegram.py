from telethon import TelegramClient
from telethon import functions
from telethon.tl.functions.channels import (
    JoinChannelRequest, 
    GetParticipantRequest, 
    GetFullChannelRequest
)
from telethon.tl.functions.messages import GetDiscussionMessageRequest
from telethon.tl.functions.account import SetPrivacyRequest
from telethon.errors import UserNotParticipantError
from telethon.hints import TotalList

from modules.chatgpt import generate_comment, generate_about_text, generate_reply_text
from modules.log_handler import logger
from modules.database.queries import (
    get_order_by_channel_address, 
    deactivate_order_by_channel_address, 
    increment_completed_comment_posts, 
    create_comment_in_db, 
    get_about_data,
    get_numberphone_by_id,
    get_proxy_data_by_id
)
from pprint import pprint
import traceback
from telethon import types
from datetime import datetime, timezone
from modules import settings
from telethon.tl.custom.message import Message


async def _init_block(account, order):
    try:
        phone_number = await get_numberphone_by_id(
            account.get('phone_number_id')
        )
        channel_address = order.get('channel_address')
        proxy = await get_proxy_data_by_id(account.get('id'))
        return [
            account.get('api_id'),
            account.get('api_hash'),
            phone_number,
            account.get('gender'),
            channel_address,
            order.get('channel_description'),
            proxy
        ]
    
    except Exception as ex:
        logger.error(f'_init_block: {ex}')
        return


# Unneeded function, since this check is in run_order() in the main file
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


async def _change_account_block(client, api_id, api_hash, channel_address, gender, channel_description, account):
    try:
        # Change about text
        try:
            about_text = await generate_about_text(gender, channel_address, channel_description)
            await client(functions.account.UpdateProfileRequest(about=about_text))
        except Exception as ex:
            logger.debug(f'_change_account_block - bio: {ex}')

        # Change avatar
        try:
            avatar_url = account.get('avatar_url')
            if avatar_url:
                photos = await client.get_profile_photos('me')
                if photos:
                    photo_ids = [types.InputPhoto(id=photo.id, access_hash=photo.access_hash, file_reference=photo.file_reference) for photo in photos]
                    await client(functions.photos.DeletePhotosRequest(id=photo_ids))
                full_avatar_url = f'../django_project/media/{avatar_url}'
                file = await client.upload_file(full_avatar_url)
                await client(functions.photos.UploadProfilePhotoRequest(file=file))
        except Exception as ex:
            logger.debug(f'_change_account_block - avatar: {ex}')

        # Change Firstname
        try:
            account_firstname = account.get('firstname')
            if account_firstname:
                await client(functions.account.UpdateProfileRequest(
                    first_name=account_firstname
                ))
        except Exception as ex:
            logger.debug(f'_change_account_block - name: {ex}')

        # Change Lastname
        try:
            account_lastname = account.get('lastname')
            if account_lastname:
                await client(functions.account.UpdateProfileRequest(
                    last_name=account_lastname
                ))
        except Exception as ex:
            logger.debug(f'_change_account_block - lastname: {ex}')

        try:
            await client(SetPrivacyRequest(
                key=types.InputPrivacyKeyPhoneNumber(),
                rules=[types.InputPrivacyValueDisallowAll()]
            ))
        except Exception as ex:
            logger.debug(f'_change_account_block - privat')
    
    except Exception as ex:
        logger.warning(f'_change_account_block: {ex}')


async def _post_data_block(client: TelegramClient, channel_to_comment):
    # Parse info to sending comment
    try:
        telegram_link = channel_to_comment.get('telegram_link')
        entity = await client.get_entity(telegram_link)
        full_channel = await client(GetFullChannelRequest(entity))
        if not full_channel.full_chat or not full_channel.full_chat.linked_chat_id:
            return None

        discussion_group_id = full_channel.full_chat.linked_chat_id
        # Discussion group part
        try:
            me = await client.get_me()
            discussion_group = await client.get_entity(types.PeerChannel(discussion_group_id))
            all_comments = await client.get_messages(discussion_group, limit=100)
            my_comments = [
                msg for msg in all_comments 
                if isinstance(msg, Message) and msg.from_id and msg.from_id.user_id == me.id
            ]

            for msg in all_comments:
                if msg.reply_to and msg.reply_to.reply_to_msg_id:
                    for my_comment in my_comments:
                        if my_comment.id == msg.reply_to.reply_to_msg_id:
                            messages = await client.get_messages(entity, limit=50)
                            for message in messages:
                                result = await client(functions.messages.GetDiscussionMessageRequest(
                                    peer=telegram_link,
                                    msg_id=message.id
                                ))
                                discussion_message = result.messages[0] if result.messages else None
                                if discussion_message and discussion_message.id == my_comment.reply_to_msg_id:
                                    return {
                                        "discussion_group_id": discussion_group_id,
                                        "reply_chain": {
                                            "post_text": message.text,
                                            "my_comment": my_comment,
                                            "reply_comment": msg,
                                        }
                                    }
        except Exception as ex:
            print(f"_post_data_block - discussion: {ex}")

        messages: TotalList = await client.get_messages(entity, limit=50)
        for message in messages:
            if message and message.text:
                result = await client(functions.messages.GetDiscussionMessageRequest(
                    peer=telegram_link,
                    msg_id=message.id
                ))

                discussion_message = result.messages[0] if result.messages else None

                if discussion_message:
                    post_date = message.date
                    now = datetime.now(timezone.utc)
                    delta = now - post_date
                    minutes_passed = int(delta.total_seconds() // 60)

                    return {
                        "discussion_group_id": discussion_group_id,
                        "last_post": {
                            'id': message.id,
                            'discussion_id': discussion_message.id,
                            'date': message.date,
                            'text': message.text,
                            'text_len': len(message.text),
                            'minutes_passed': minutes_passed if minutes_passed else None,
                            'replies': message.replies.replies if message.replies else None,
                        }
                    }
        return None
    
    except Exception as ex:
        logger.warning(f'_post_data_block: {ex}')


async def _join_channel_block(client, discussion_group_id):
    try:
        await client(GetParticipantRequest(discussion_group_id, 'me'))
        return True
    
    except Exception:
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
        # Send comment
        message = await client.send_message(
            post_data.get('discussion_group_id'),
            comment_text, 
            reply_to=post_data.get('last_post').get('discussion_id')
        )

        # Receive comment link
        comment_link = None
        try:
            chat = await client.get_entity(post_data.get('discussion_group_id'))
            group_link = f"https://t.me/{chat.username}"
            comment_link = f"{group_link}/{message.id}"
        except Exception as ex:
            ...

        # Save result to db 
        await increment_completed_comment_posts(channel_address=channel_address)
        await create_comment_in_db(
            api_hash=api_hash,
            api_id=api_id,
            channel_link=channel_to_comment.get('telegram_link'),
            text=comment_text,
            comment_link=comment_link
        )

        # Disconnect account
        await client.disconnect()
        
        logger.debug(
            f'Comment by {account.get("username")} made on {channel_address} and saved in DB.'
        )
        
        # Return true so post_comment_for_order() knew what all ok
        return True
        
    except Exception as ex:
        logger.warning(
            f'Comment by {account.get("username")} dont made on {channel_address}. Error: {ex}'
        )
        return
    

async def _reply_block(client, discussion_group_id, text, reply_to):
    message = await client.send_message(
        discussion_group_id,
        text, 
        reply_to=reply_to
    )
    return True


async def post_comment_for_order(channels_to_comment, order, account):
    # Receive initial date
    init_data = await _init_block(account, order) 
    if not init_data:
        return
    api_id, api_hash, phone_number, gender, channel_address, channel_description, proxy = init_data


    try:
        # Connect via Telethon
        client = TelegramClient(
            f"./sessions/{api_id}{api_hash}{phone_number[1::]}", 
            api_id, 
            api_hash, 
            system_version='4.16.30-vxCUSTOM',
            proxy=proxy
        ) 
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            raise Exception('Auth failed')

        # Change account via Telethon (Firstname, Lastname, Avatars and so on)
        await _change_account_block(client, api_id, api_hash, channel_address, gender, channel_description, account) 

        for channel_to_comment in channels_to_comment:
            # Receive last post info in channels
            post_data = await _post_data_block(client, channel_to_comment)
            if not post_data:
                continue
            
            input(" >>> ")
            if "last_post" in post_data:
                input("last post >>> ")
                if not post_data.get('last_post').get('minutes_passed'):
                    continue

                if not post_data.get('last_post').get('replies'):
                    continue
                
                if post_data.get('last_post').get('text_len') < settings.POST_MIN_LEN:
                    continue
                
                discussion_group_id = post_data.get('discussion_group_id')

                # Try to connect in group
                is_joined = await _join_channel_block(client, discussion_group_id) 
                if not is_joined:
                    continue
                
                # Generate comment
                comment_text = await generate_comment(
                    post_text=post_data.get('last_post').get('text'),
                    gender=('Мужчина' if gender == 'M' else 'Женщина'),
                    post_max_len=512,
                    max_out_tokens=512,
                    use_two_steps=True
                )

                # Send comment
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
                ) 

                # If comment is made break, else repeat
                if comment_is_made:
                    break

            elif "reply_chain" in post_data:
                text = await generate_reply_text(
                    post_text=post_data.get("post_text"),
                    my_comment_text=post_data.get("my_comment").text,
                    reply_text=post_data.get("reply_comment").text,
                )

                await _reply_block(
                    discussion_group_id=post_data.get('discussion_group_id'),
                    text=...,
                    reply_to=post_data.get("reply_comment")
                )
                
        await client.disconnect()

    except Exception as ex:
        logger.error(f'post_comment_for_order (Comment part): {ex}')
        traceback.print_exc()

    
    

    

