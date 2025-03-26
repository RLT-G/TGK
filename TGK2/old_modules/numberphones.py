import aiohttp
import json

from modules import settings


async def get_balance() -> float:
    url = f"https://api.7grizzlysms.com/stubs/handler_api.php?"

    params = {
        'api_key': settings.GRIZZLYSMS_API_KEY,
        'action': 'getBalance',
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                result = await response.text()
                return result.split(':')[-1]


async def get_numberphone(country) -> float:
    url = f"https://api.7grizzlysms.com/stubs/handler_api.php"

    params = {
        'api_key': settings.GRIZZLYSMS_API_KEY,
        'action': 'getNumber',
        'service': 'tg',
    }

    country_code = settings.GRIZZLYSMS_COUNTRY_CODES.get(country.upper(), None)
    
    if country_code:
        params['country'] = country_code

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                result = await response.text()
                # numberphone_id, numberphone = result.split(':')[1::]
                return result


async def set_status(id: int, status: int):
    """
    $status — статус активации
    -1 — отменить активацию;
    1 — сообщить о готовности номера (смс на номер отправлено);
    3 — сообщить об ожидании нового кода на тот же номер;
    6 — завершить активацию;
    8 — отменить активацию.
    """

    url = f"https://api.7grizzlysms.com/stubs/handler_api.php"

    params = {
        'api_key': settings.GRIZZLYSMS_API_KEY,
        'action': 'setStatus',
        'status': status,
        'id': id,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                return True
                # result = await response.text()
                # json_result = json.loads(result)
            return False

async def get_code(id: int):
    url = f"https://api.7grizzlysms.com/stubs/handler_api.php"

    params = {
        'api_key': settings.GRIZZLYSMS_API_KEY,
        'action': 'getStatus',
        'id': id,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                result = await response.text()
                # json_result = json.loads(result)
                return result
            

async def get_price_numberphone(country: str = '') -> float:
    url = f"https://api.7grizzlysms.com/stubs/handler_api.php"

    params = {
        'api_key': settings.GRIZZLYSMS_API_KEY,
        'action': 'getPrices',
        'service': 'tg',
        # 'rent_time': 4
    }

    country_code = settings.GRIZZLYSMS_COUNTRY_CODES.get(country.upper(), None)
    
    if country_code:
        params['country'] = country_code

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                result = await response.text()
                json_result = json.loads(result)
                return json_result
            

async def get_rent(country: str = None): 
    url = f"https://api.7grizzlysms.com/stubs/handler_api.php"

    params = {
        'api_key': settings.GRIZZLYSMS_API_KEY,
        'action': 'getRentNumber',
        'service': 'tg',
        'rent_time': 4
    }

    country_code = settings.GRIZZLYSMS_COUNTRY_CODES.get(country.upper(), None) if country else None
    
    if country_code:
        params['country'] = country_code

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            result = await response.text()
            json_result = json.loads(result)
            return json_result
                
            
    
# async def buy_proxy(country: str, period: int = 30) -> list[list]:
#     url = f"https://px6.link/api/{settings.PROXY6NET_API_KEY}/buy"

#     params = {
#         'count': 1,
#         'period': period,
#         'country': country, 
#         'type': 'socks',
#         'auto_prolong': ''
#     }

#     async with aiohttp.ClientSession() as session:
#         async with session.post(url, params=params) as response:
#             if response.status == 200:
#                 result = await response.json()
#                 return result.get('list') 
