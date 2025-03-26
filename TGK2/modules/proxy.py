import aiohttp
from modules import settings


async def get_balance() -> float:
    url = f"https://px6.link/api/{settings.PROXY6NET_API_KEY}"

    async with aiohttp.ClientSession() as session:
        async with session.post(url) as response:
            if response.status == 200:
                result = await response.json()
                return result.get('balance') 
            

async def get_country() -> list[str]:
    url = f"https://px6.link/api/{settings.PROXY6NET_API_KEY}/getcountry"

    async with aiohttp.ClientSession() as session:
        async with session.post(url) as response:
            if response.status == 200:
                result = await response.json()
                return result.get('list') 


async def get_price_proxy(period: int = 30) -> float:
    url = f"https://px6.link/api/{settings.PROXY6NET_API_KEY}/getprice"

    params = {
        'count': 1,
        'period': period,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=params) as response:
            if response.status == 200:
                result = await response.json()
                return result.get('price') 
            

async def buy_proxy(country: str, period: int = 30) -> list[list]:
    url = f"https://px6.link/api/{settings.PROXY6NET_API_KEY}/buy"

    params = {
        'count': 1,
        'period': period,
        'country': country, 
        'type': 'socks',
        'auto_prolong': ''
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=params) as response:
            if response.status == 200:
                result = await response.json()
                return result.get('list') 
            