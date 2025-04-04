from zoneinfo import ZoneInfo
import pytz

import os
from dotenv import load_dotenv


load_dotenv()

PROXY6NET_API_KEY = os.getenv('PROXY6NET_API_KEY')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

TZ = ZoneInfo("Europe/Moscow")

LOGGER_TZ = pytz.timezone("Europe/Moscow")

COMMENT_PROMT = """
Проанализируй текст поста, выдели ключевые темы, аргументы и эмоциональный тон.
Представь, что ты: {}, 22 года.
Сгенерируй комментарий, который:
1. Связаны с содержанием поста – отражают его основные идеи, задают вопросы, дополняют фактами или примерами.
2. Разнообразны по стилю:
- Согласие | поддержка («Спасибо за пост! Особенно важно, что...»).
- Критика | вопросы («А как насчёт...?», «Не согласен, потому что...»).
- Личный опыт («У меня был похожий случай...»).
- Ирония | сарказм (если тон поста позволяет).
- Призыв к действию («Поддерживаю! Нужно...», «Хватит молчать — ...»).
3. Учитывают аудиторию : пиши так, чтобы комментарии провоцировали дискуссию, но не переходили на оскорбления.
4. Краткость и ясность : избегай сложных конструкций, используй разговорный язык.
5. Комментарий должен быть всего один.
6. Комментарий должен быть коротким, максимум одно предложение.
7. Не упоминай о том что ты ИИ. 
Примеры для вдохновения :
- «Интересная мысль! А как это работает в [конкретный контекст]?»
- «Полностью согласен. Особенно раздражает, когда...»
- «А если взглянуть с другой стороны: ...?»
Важно : не повторяй шаблоны, фокусируйся на уникальности поста и потенциальных «болевых точках» аудитории."
Для ответа выбери только один лучший комментарий, в котором нет символов на китайском языке. И в ответе выведи только текст самого комментария.

Пост: {}
"""

DEFAULT_COMMENT = '🔥🔥🔥'

SYMBOLS_TO_DELETE = ['«', '»', '>', '<', '"', '«', '»', '《', '》', '(', ')', '[', ']', '{', '}', '„', '“', '❝', '❞']

SYMBOLS_TO_REPLACE = [
    ('—', '-'),
    ('…', '...'),
    ('−', '-'),
    ('°', 'градус'),
    ('€', 'евро'),
    ('¥', 'йен'),
    ('£', 'фунтов'),
    ('→', '->'),
    ('⇒', '->'),
    ('⟶', '->'),
]

DAYS_ACTIVE = {
    "0": [0, 1],
    "1": [1, 2],
    "2": [1, 5],
    "3": [2, 7],
    "4": [5, 10],
    "5": [10, 20],
    "6": [15, 35],
}

ABOUT_PROMT_1 = """
Проанализируйте расширенное описание автора, выделите ключевые темы, аргументы.
Представьте, что вы: {}, 24 года.
Сгенерируйте 7 очень коротких описаний автора, в соответствии с требованиями :
1. Подчеркните авторитет и квалификацию
- Упомяните конкретные достижения, опыт и академические/профессиональные звания эксперта. 
- Социальная инженерия : Принцип авторитета — люди склонны доверять тем, кто имеет подтвержденные достижения.
2. Добавьте эмоциональную связь через историю
- Расскажите о личном опыте эксперта, который делает его близким читателю. Например: "Доктор Иванов разработал метод X после 10 лет работы в критических ситуациях, где ошибки стоили жизни".
- Социальная инженерия : Сторителлинг манипулирует эмоциями, создавая эмпатию и доверие.
3. Подчеркните уникальность подхода
- Опишите, чем методы эксперта отличаются от других.
- Социальная инженерия : Принцип рекомендации — уникальность вызывает интерес и желание подражать.
4. Структурируйте описание логично
- Разделите информацию на маленькие блоки.
- В конце должен быть адрес канала : {}. 
- Социальная инженерия : Порядок "проблема-решение-результат" мотивирует доверие.
5. Добавьте динамику через примеры
- Используйте метафоры, связанные с его работой. Например: "Как хирург, он разбирает сложные задачи на элементы, которые любой может понять".
- Социальная инженерия : Метафоры упрощают восприятие и создают образ эксперта как “простого” гения.
Для ответа выбери только одно лучшее описание автора, и в ответе выведи только текст самого комментария.

Расширенное описание автора:
{}
"""

ABOUT_PROMT_2 = """
Сократите текст яркого описания до 60 символов или меньше (с учетом пробелов), сохранив ключевые метафоры и адрес канала:
{}
"""


