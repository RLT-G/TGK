from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, UsernameInvalidError, UsernameNotOccupiedError
from telethon.tl.functions.channels import GetFullChannelRequest
import asyncio
from telethon import functions
from pprint import pprint
from modules.gigachat import generate_comment
from modules.database.queries import get_searcher_data, get_all_channels
from modules import settings


async def get_last_posts():
    searcher_data = await get_searcher_data()

    api_id = searcher_data['api_id']
    api_hash = searcher_data['api_hash']
    phone_number = searcher_data['phone_number']['number']
    gender = searcher_data['gender']

    client = TelegramClient(f"./sessions/{api_id}{api_hash}{phone_number[1::]}", api_id, api_hash, system_version='4.16.30-vxCUSTOM')
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            await client.send_code_request(phone_number)
            code = input('Введите код: ')
            await client.sign_in(phone_number, code)

        posts_data = {}

        channels = await get_all_channels()

        for channel in channels:
            channel_telegram_link = channel['telegram_link']
            try:
                entity = await client.get_entity(channel_telegram_link)
                full_channel = await client(GetFullChannelRequest(entity))

                if not full_channel.full_chat or not full_channel.full_chat.linked_chat_id:
                    print(f"У канала {channel_telegram_link} нет привязанной группы обсуждения.")
                    continue

                discussion_group_id = full_channel.full_chat.linked_chat_id
                posts_data[channel_telegram_link] = {
                    "discussion_group_id": discussion_group_id,
                    "posts": []
                }

                messages = await client.get_messages(entity, limit=50)

                for message in messages:
                    if message and message.text:

                        try:
                            result = await client(functions.messages.GetDiscussionMessageRequest(
                                peer=channel_telegram_link,
                                msg_id=message.id
                            ))

                            discussion_message = result.messages[0] if result.messages else None
                            
                            if discussion_message:
                                (posts_data[channel_telegram_link]['posts']).append({
                                    'id': message.id,
                                    'discussion_id': discussion_message.id,
                                    'date': message.date,
                                    'text': message.text,
                                })

                        except Exception as e:
                            print(f"Ошибка при обработке поста {message.id}: {e}")

                    if len(posts_data[channel_telegram_link]['posts']) == channel['comment_post_limit']:
                        break
                    
                    await asyncio.sleep(1)
                
            except (UsernameInvalidError, UsernameNotOccupiedError):
                print(f"Канал {channel_telegram_link} не найден или недоступен.")
            except Exception as e:
                print(f"Ошибка при обработке канала {channel_telegram_link}: {e}")

        return posts_data

    except SessionPasswordNeededError:
        print("Session password needed error")
    except Exception as e:
        print(f"Error: {e}")

    finally:
        await client.disconnect()


async def add_comment_to_posts(posts_data: dict, gender: str) -> dict:
    for channel, channel_data in posts_data.items(): 
        for post in channel_data['posts']:
            comment_text = settings.DEFAULT_COMMENT
            try:
                new_comment = await generate_comment(
                    post_text=post['text'],
                    gender=('Мужчина' if gender == 'M' else 'Женщина')
                )
                comment_text = new_comment
                await asyncio.sleep(1)

            except Exception as e:
                print('Произошла ошибка при генерировании комментария', e)
    
            post['comment_text'] = comment_text
    return posts_data


if __name__ == '__main__':
    channels = ['https://t.me/spbtoday', ]
    asyncio.run(get_last_posts(channels))
