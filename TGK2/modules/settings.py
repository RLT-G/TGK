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

# CLIENT_ID = os.getenv('CLIENT_ID')

# SCOPE = os.getenv('SCOPE')

# AUTHORIZED_KEY = os.getenv('AUTHORIZED_KEY')

# GRIZZLYSMS_API_KEY = os.getenv('GRIZZLYSMS_API_KEY')

# GECKO_DRIVER_PATH = '/snap/bin/firefox.geckodriver'

# LOADING_CHANNELS_FROM_JSON = True

# GRIZZLYSMS_COUNTRY_CODES = {
#     "AU": 175,  "AT": 50,       "AZ": 35,       "AL": 155,   "DZ": 58,  "AS": 10161,    "AI": 181,  "AO": 76,  "AG": 169, "AM": 148,
#     "AW": 179,  "AF": 74,       "BS": 122,      "BD": 60,    "BB": 118, "BH": 145,      "BY": 51,   "BZ": 124, "BE": 82,  "BJ": 120,
#     "BG": 83,   "BO": 92,       "BA": 108,      "BW": 123,   "BR": 73,  "BN": 121,      "BF": 152,  "BI": 119, "BT": 158, "HU": 84,
#     "VE": 70,   "TL": 91,       "VN": 10,       "GA": 154,   "HT": 26,  "GY": 131,      "GM": 28,   "GH": 38,  "GP": 160, "GT": 94,
#     "GN": 68,   "GW": 130,      "DE": 43,       "GI": 201,   "HN": 88,  "HK": 14,       "GD": 127,  "GR": 129, "CD": 18,  "DK": 172,
#     "DJ": 168,  "DM": 126,      "DO": 109,      "EG": 21,    "ZM": 147, "ZW": 96,       "IL": 13,   "IN": 22,  "ID": 6,   "JO": 116,
#     "IQ": 47,   "IR": 10016,    "IE": 23,       "IS": 132,   "ES": 56,  "IT": 86,       "YE": 30,   "CV": 186, "KZ": 2,   "KY": 170,
#     "KH": 24,   "CM": 41,       "CA": 36,       "QA": 111,   "KE": 8,   "CY": 77,       "KG": 11,   "CN": 3,   "CO": 33,  "KM": 133,
#     "CR": 93,   "CI": 27,       "KW": 100,      "LA": 25,    "LS": 136, "LR": 135,      "LB": 153,  "LY": 102, "LT": 44,  "LI": 10348,
#     "LU": 165,  "MU": 157,      "MR": 114,      "MG": 17,    "MO": 20,  "MW": 137,      "MY": 7,    "ML": 69,  "MV": 159,  "MA": 37,
#     "MX": 54,   "MZ": 80,       "MC": 144,      "MN": 72,    "MS": 180, "MM": 5,        "NA": 138,  "NP": 81,  "NE": 139,  "NG": 19,
#     "NL": 48,   "NI": 90,       "NZ": 67,       "NC": 185,   "NO": 174, "AE": 95,       "OM": 107,  "PK": 66,  "PA": 112,  "PG": 79,
#     "PY": 87,   "PE": 65,       "PL": 15,       "PT": 117,   "PR": 97,  "CG": 150,      "RE": 146,  "RW": 140, "RO": 32,   "US": 187,
#     "SV": 101,  "WS": 10231,    "ST": 178,      "SA": 53,    "SZ": 106, "MK": 183,      "SC": 184,  "SN": 61,  "VC": 166,  "KN": 134,
#     "LC": 164,  "RS": 29,       "SG": 10351,    "SX": 10349, "SY": 110, "SK": 141,      "SI": 59,   "SO": 149, "SR": 142,  "SL": 115,
#     "TJ": 143,  "TH": 52,       "TW": 55,       "TZ": 9,     "TG": 99,  "TO": 10227,    "TT": 104,  "TN": 89,  "TM": 161,  "TR": 62,
#     "UG": 75,   "UZ": 40,       "UA": 1,        "UY": 156,   "PH": 4,   "FI": 163,      "FR": 78,   "GF": 162, "CF": 125,  "TD": 42,
#     "ME": 171,  "CZ": 63,       "CL": 151,      "CH": 173,   "SE": 46,  "LK": 64,       "EC": 105,  "GQ": 167, "ER": 176,  "EE": 34,
#     "ET": 71,   "ZA": 31,       "KR": 10350,    "SS": 177,   "JM": 103, "JP": 182,      "GB": 16,   "AR": 39,  "GE": 128,  "LV": 49,
#     "MD": 85,   "HR": 45
# }

