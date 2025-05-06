from pprint import pprint
from modules.database import queries
from modules import chatgpt
from telethon.tl.custom.message import Message
from telethon import types
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

from datetime import datetime, timezone
import settings

class Account:
    def __init__(
        self, 
        channels: list[dict], 
        account_data: dict, 
        current_order: dict
    ):
        self.channels = channels
        self.current_order = current_order
        self.account_data = account_data
        self.api_id = account_data['api_id']
        self.api_hash = account_data['api_hash']
        self.gender = account_data['gender']
        self.client = None
        self.numberphone = None 

    async def _connect(self):
        if not self.client:
            self.numberphone = await queries.get_numberphone_by_id(
                self.account_data['phone_number_id']
            )
            self.client = TelegramClient(
                f"./sessions/{self.api_id}{self.api_hash}{self.numberphone[1::]}", 
                self.api_id,
                self.api_hash,
                system_version='4.16.30-vxCUSTOM',
            )
            await self.client.connect()
            if not await self.client.is_user_authorized():
                await self.client.disconnect()

    async def _disconnect(self):
        if self.client:
            self.client.disconnect()

    async def _change_account(self):
        if self.client and self.account_data['need_update']:
            try:
                about_text = await chatgpt.generate_about_text(
                    self.gender,
                    self.current_order["channel_address"],
                    self.current_order["channel_description"]
                )
                await self.client(functions.account.UpdateProfileRequest(about=about_text))
            except Exception as ex:
                ...
            try:
                avatar_url = self.account_data['avatar_url']
                photos = await self.client.get_profile_photos('me')
                if photos:
                    photo_ids = [types.InputPhoto(id=photo.id, access_hash=photo.access_hash, file_reference=photo.file_reference) for photo in photos]
                    await self.client(functions.photos.DeletePhotosRequest(id=photo_ids))

                full_avatar_url = f'../django_project/media/{avatar_url}'
                file = await self.client.upload_file(full_avatar_url)
                await self.client(functions.photos.UploadProfilePhotoRequest(file=file))
            except Exception:
                ...

            try:
                account_firstname = self.account_data['firstname']
                if account_firstname:
                    await self.client(functions.account.UpdateProfileRequest(
                        first_name=account_firstname
                    ))
            except Exception:
                ...

            try:
                account_lastname = self.account_data['lastname']
                if account_lastname:
                    await self.client(functions.account.UpdateProfileRequest(
                        last_name=account_lastname
                    ))
            except Exception:
                ...

            try:
                await self.client(SetPrivacyRequest(
                    key=types.InputPrivacyKeyPhoneNumber(),
                    rules=[types.InputPrivacyValueDisallowAll()]
                ))
            except Exception:
                ...
        
        await queries.set_need_update(self.account_data['id'], False)

    async def _join_to_channel(self, post_data):
        discussion_group_id = post_data['discussion_group_id']
        if self.client:
            try:
                await self.client(GetParticipantRequest(discussion_group_id, 'me'))
                return True
            
            except Exception:
                try:
                    await self.client(JoinChannelRequest(discussion_group_id))
                    return True
                
                except Exception as ex:
                    logger.warning(f'_join_channel_block: {ex}')
                    return

    async def _parse_channel(self, channel_to_comment: dict) -> dict:
        if self.client:
            telegram_link = channel_to_comment['telegram_link']
            entity = await self.client.get_entity(telegram_link)
            full_channel = await self.client(GetFullChannelRequest(entity))
            if not full_channel.full_chat or not full_channel.full_chat.linked_chat_id:
                return 

            participants_count = None
            try:
                participants_count = full_channel.full_chat.participants_count
            except Exception:
                ...

            discussion_group_id = full_channel.full_chat.linked_chat_id
            try:
                me = await self.client.get_me()
                discussion_group = await self.client.get_entity(types.PeerChannel(discussion_group_id))
                all_comments = await self.client.get_messages(discussion_group, limit=100)
                for msg in all_comments:
                    if isinstance(msg, Message) and msg.from_id and msg.from_id.user_id == me.id:
                        return
            except Exception:
                ...

            messages: TotalList = await self.client.get_messages(entity, limit=50)
            for message in messages:
                if message and message.text:
                    result = await self.client(functions.messages.GetDiscussionMessageRequest(
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
                                'participants_count': participants_count if participants_count else None
                            }
                        }

    async def _send_comment(self, post_data: dict, comment_text: str, channel_to_comment: dict) -> bool:
        if self.client:
            try:
                message = await self.client.send_message(
                    post_data['discussion_group_id'],
                    comment_text, 
                    reply_to=post_data['last_post']['discussion_id']
                )

                comment_link = None
                try:
                    chat = await self.client.get_entity(post_data['discussion_group_id'])
                    group_link = f"https://t.me/{chat.username}"
                    comment_link = f"{group_link}/{message.id}"
                except Exception as ex:
                    ...

                await queries.increment_completed_comment_posts(self.current_order['id'])
                await queries.create_comment_in_db(
                    api_hash=self.api_hash,
                    api_id=self.api_id,
                    channel_link=channel_to_comment['telegram_link'],
                    text=comment_text,
                    comment_link=comment_link
                )
                return True
            except Exception as ex:
                return False

    async def _send_reply(self):
        ...

    async def do_job(self):
        await self._connect()
        await self._change_account()

        for channel in self.channels:
            post_data = await self._parse_channel(channel)

            if post_data == None:
                continue   
            
            if post_data['last_post']['minutes_passed'] > 360:
                continue

            if post_data['last_post']['replies'] > post_data['last_post']['participants_count'] * 0.1:
                continue

            if post_data['last_post']['text_len'] < settings.POST_MIN_LEN:
                continue

            pprint(post_data)

            is_joined = await self._join_to_channel(post_data)
            if is_joined == False:
                continue

            
            comment_text = await chatgpt.generate_comment(
                post_text=post_data['last_post']['text'],
                gender=('Мужчина' if self.gender == 'M' else 'Женщина'),
                post_max_len=4096,
                max_out_tokens=4096,
                use_two_steps=True
            )
            comment_is_made = await self._send_comment(post_data, comment_text, channel)
            if comment_is_made:
                break
            
        await self._disconnect()


async def init_account(
    random_channels_to_comment: list,
    order: dict,
    account: dict
):
    current_account = Account(
        channels=random_channels_to_comment,
        account_data=account,
        current_order=order
    )

    await current_account.do_job()

