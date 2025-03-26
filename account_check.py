from telethon import TelegramClient


async def main():
    try:
        API_ID = input('Введите API_ID >>> ')
        API_HASH = input('Введите API_HASH >>> ')
        PHONE_NUMBER = input('Введите номер телефона (+7XXXXXXXXXX) >>> ')

        client = TelegramClient("session_name", API_ID, API_HASH)
        client = TelegramClient(
            f"REMOVE_THIS", 
            API_ID, 
            API_HASH, 
            system_version='4.16.30-vxCUSTOM'
        )

        await client.connect()
        
        if not await client.is_user_authorized():
            await client.send_code_request(PHONE_NUMBER)
            code = input("Введите код из Telegram: ")
            await client.sign_in(PHONE_NUMBER, code)
        
        try:
            me = await client.get_me()
            print(f"ID: {me.id}")
            print(f"Имя: {me.first_name}")
            print(f"Фамилия: {me.last_name}")
            print(f"Юзернейм: {me.username}")
            print(f"Телефон: {me.phone}")
        except Exception as ex:
            print(f"API доступен, однако произошла иная ошибка: {ex}")

        await client.disconnect()

    except Exception as ex:
        print(f'Произошла следующая ошибка: {ex}')


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    input('Нажмите enter для завершения >>> ')
