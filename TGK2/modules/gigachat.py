import aiohttp
import uuid

from modules import settings


async def generate_comment(post_text: str, gender: str):
    async def get_access_token(auth_key: str, scope: str) -> str:
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
            "Authorization": f"Basic {auth_key}"
        }
        data = { "scope": scope }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data, ssl=False) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("access_token")
                else:
                    error = await response.text()
                    raise Exception(f"Failed to get access token: {response.status} - {error}")
                
    async def get_models(access_token: str) -> list:
        url = "https://gigachat.devices.sberbank.ru/api/v1/models"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, ssl=False) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("data", [])
                else:
                    error = await response.text()
                    raise Exception(f"Failed to get models: {response.status} - {error}")
                
    async def send_chat_message(access_token: str, message: str, model: str = "GigaChat") -> str:
        url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": message}
            ],
            "stream": False,
            "repetition_penalty": 1
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, ssl=False) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("choices", [])[0].get("message", {}).get("content", "")
                else:
                    error = await response.text()
                    raise Exception(f"Failed to send chat message: {response.status} - {error}")
    
    try:
        auth_key = settings.AUTHORIZED_KEY
        client_id = settings.CLIENT_ID
        scope = settings.SCOPE

        access_token = await get_access_token(auth_key, scope)

        models = await get_models(access_token)

        if len(post_text) > 255:
            post_text = post_text[0:255]

        message = settings.COMMENT_PROMT.format(gender, post_text)

        comment = await send_chat_message(access_token, message)

        comment = comment.replace('"', "")

        return comment
    
    except Exception as ex:
        return settings.DEFAULT_COMMENT
