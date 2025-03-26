import asyncio
import openai

from modules import settings


openai.api_key = settings.OPENAI_API_KEY


async def fetch_chatgpt_response(
        model: str, 
        prompt: str, 
        max_tokens: int = 200) -> str:
    try:

        request_params = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens
        }

        response = await openai.ChatCompletion.acreate(**request_params)

        return response['choices'][0]['message']['content']
    
    except Exception as e:  
        return settings.DEFAULT_COMMENT
    

async def generate_comment(post_text: str, gender: str) -> str:
    if len(post_text) > 255:
        post_text = post_text[0:255]

    comment = await fetch_chatgpt_response(
        model='gpt-4o-mini',
        prompt=settings.COMMENT_PROMT.format(
            'Мужчина' if gender == 'M' else 'Женщина',
            post_text
        ),
        max_tokens=200
    )
    
    for symbol in settings.SYMBOLS_TO_DELETE:
        comment = comment.replace(symbol, '')

    for old_symbol, new_symbol in settings.SYMBOLS_TO_REPLACE:
        comment = comment.replace(old_symbol, new_symbol)

    return comment


async def generate_about_text(gender: str, channel_address: str, channel_description: str) -> str:
    large_about_text = await fetch_chatgpt_response(
        model='gpt-4o-mini',
        prompt=settings.ABOUT_PROMT_1.format(
            'Мужчина' if gender == 'M' else 'Женщина',
            channel_address,
            channel_description
        )
    )
    small_about_text = await fetch_chatgpt_response(
        model='gpt-4o-mini',
        prompt=settings.ABOUT_PROMT_2.format(
            large_about_text
        )
    )
    if not channel_address in small_about_text:
        if len(small_about_text + channel_address) + 1 > 70:
            small_about_text = channel_address
        else:
            small_about_text = f"{small_about_text} {channel_address}"

    return small_about_text



if __name__ == '__main__':
    asyncio.run(fetch_chatgpt_response(
        model='gpt-4o-mini',
        prompt='Привет, как тебя зовут?',
        max_tokens=200
    ))