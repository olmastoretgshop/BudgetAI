import re


# ============================================================
# AMOUNT
# ============================================================

def extract_amount(text):
    """
    Извлекает сумму из свободного текста.

    Поддерживает:
        25000
        25 000
        25.000
        25,000
        25.5
        25,5
        25к
        25k
        25.5k
        500 тыс
        1.5 млн
        2 млрд

    Возвращает:
        float
        или None, если сумма не найдена / некорректна.
    """

    if not text or not isinstance(text, str):
        return None

    # Отрицательные суммы запрещены
    if re.search(r'(?<!\d)-\s*\d', text):
        return None

    text_lower = text.lower()

    # ========================================================
    # 1. BILLION / MILLION / THOUSAND
    # ========================================================

    multiplier_patterns = [
        # Миллиарды
        (
            r'(\d+(?:[.,]\d+)?)\s*'
            r'(?:млрд|миллиард(?:а|ов)?|billion|bn)\b',
            1_000_000_000
        ),

        # Миллионы
        (
            r'(\d+(?:[.,]\d+)?)\s*'
            r'(?:млн|миллион(?:а|ов)?|million)\b',
            1_000_000
        ),

        # Тысячи
        (
            r'(\d+(?:[.,]\d+)?)\s*'
            r'(?:тыс|тысяч(?:а|и)?|тысячи|thousand)\b',
            1_000
        ),
    ]

    for pattern, multiplier in multiplier_patterns:
        match = re.search(pattern, text_lower)

        if match:
            number = match.group(1).replace(",", ".")

            try:
                amount = float(number) * multiplier
            except ValueError:
                return None

            if amount <= 0:
                return None

            return amount

    # ========================================================
    # 2. SHORT FORMAT: 25к / 25k / 25.5k / 25,5k
    # ========================================================

    match = re.search(
        r'(?<![\d.])'
        r'(\d+(?:[.,]\d+)?)'
        r'\s*[кk]'
        r'(?![a-zа-яё])',
        text_lower
    )

    if match:
        number = match.group(1).replace(",", ".")

        try:
            amount = float(number) * 1_000
        except ValueError:
            return None

        if amount <= 0:
            return None

        return amount

    # ========================================================
    # 3. NUMBERS WITH THOUSAND SEPARATORS
    # ========================================================

    match = re.search(
        r'(?<!\d)'
        r'(\d{1,3}(?:[ .,]\d{3})+(?:[.,]\d+)?)'
        r'(?!\d)',
        text
    )

    if match:
        number = match.group(1)

        # Убираем пробелы
        number = number.replace(" ", "")

        # ----------------------------------------------------
        # Есть и точка, и запятая
        # ----------------------------------------------------

        if "." in number and "," in number:

            # Последний разделитель считаем десятичным
            if number.rfind(",") > number.rfind("."):
                number = number.replace(".", "")
                number = number.replace(",", ".")
            else:
                number = number.replace(",", "")

        # ----------------------------------------------------
        # Только запятая
        # ----------------------------------------------------

        elif "," in number:
            parts = number.split(",")

            if len(parts) > 2:
                # 1,500,000
                number = "".join(parts)

            elif len(parts) == 2 and len(parts[1]) == 3:
                # 25,000
                number = "".join(parts)

            else:
                # 25,5
                number = number.replace(",", ".")

        # ----------------------------------------------------
        # Только точка
        # ----------------------------------------------------

        elif "." in number:
            parts = number.split(".")

            if len(parts) > 2:
                # 1.250.000
                number = "".join(parts)

            elif len(parts) == 2 and len(parts[1]) == 3:
                # 25.000
                number = "".join(parts)

        try:
            amount = float(number)
        except ValueError:
            return None

        if amount <= 0:
            return None

        return amount

    # ========================================================
    # 4. NORMAL INTEGER / DECIMAL
    # ========================================================

    match = re.search(
        r'(?<![\d.])'
        r'(\d+(?:[.,]\d+)?)'
        r'(?![\d.])',
        text
    )

    if not match:
        return None

    number = match.group(1).replace(",", ".")

    try:
        amount = float(number)
    except ValueError:
        return None

    if amount <= 0:
        return None

    return amount


# ============================================================
# CURRENCY
# ============================================================

def extract_currency(text):
    """
    Определяет валюту из текста.

    Поддерживает:
        UZS / сум / сўм / som
        USD / $ / dollar
        EUR / € / euro
        RUB / ₽ / рубль

    Если валюта не указана:
        возвращает UZS.
    """

    if not text or not isinstance(text, str):
        return "UZS"

    text = text.lower().strip()

    # ========================================================
    # UZS
    # ========================================================

    uzs_patterns = [
        r'\buzs\b',
        r'\bсум\b',
        r'\bсумов\b',
        r'\bсўм\b',
        r'\bсўмлар\b',
        r"\bso['’]?m\b",
        r'\bsom\b'
    ]

    for pattern in uzs_patterns:
        if re.search(pattern, text):
            return "UZS"

    # ========================================================
    # USD
    # ========================================================

    usd_patterns = [
        r'\busd\b',
        r'\bdollar\b',
        r'\bdollars\b',
        r'\bдоллар\b',
        r'\bдоллара\b',
        r'\bдолларов\b',
        r'\$'
    ]

    for pattern in usd_patterns:
        if re.search(pattern, text):
            return "USD"

    # ========================================================
    # EUR
    # ========================================================

    eur_patterns = [
        r'\beur\b',
        r'\beuro\b',
        r'\beuros\b',
        r'\bевро\b',
        r'€'
    ]

    for pattern in eur_patterns:
        if re.search(pattern, text):
            return "EUR"

    # ========================================================
    # RUB
    # ========================================================

    rub_patterns = [
        r'\brub\b',
        r'\bruble\b',
        r'\brubles\b',
        r'\bруб\b',
        r'\bрубль\b',
        r'\bрублей\b',
        r'₽'
    ]

    for pattern in rub_patterns:
        if re.search(pattern, text):
            return "RUB"

    return "UZS"


# ============================================================
# CATEGORY
# ============================================================

CATEGORY_KEYWORDS = {

    # ========================================================
    # EXPENSE CATEGORIES
    # ========================================================

    "food": [
        "еда",
        "продукты",
        "продукт",
        "обед",
        "завтрак",
        "ужин",
        "хлеб",
        "кофе",
        "чай",
        "пицца",
        "бургер",
        "ресторан",
        "кафе",
        "фастфуд",
        "food",
        "coffee",
        "restaurant",
        "pizza",
        "burger"
    ],

    "transport": [
        "такси",
        "метро",
        "автобус",
        "бензин",
        "топливо",
        "машина",
        "парковка",
        "transport",
        "taxi",
        "bus",
        "fuel",
        "gas"
    ],

    "shopping": [
        "одежда",
        "одежду",
        "обувь",
        "магазин",
        "покупка",
        "шопинг",
        "shopping",
        "clothes",
        "shoes",
        "store"
    ],

    "entertainment": [
        "кино",
        "фильм",
        "игра",
        "концерт",
        "развлечения",
        "театр",
        "cinema",
        "movie",
        "game",
        "concert",
        "entertainment"
    ],

    "health": [
        "аптека",
        "лекарство",
        "врач",
        "больница",
        "стоматолог",
        "анализы",
        "medicine",
        "doctor",
        "hospital",
        "pharmacy",
        "dentist"
    ],

    "education": [
        "курс",
        "курсы",
        "университет",
        "учеба",
        "обучение",
        "книга",
        "книги",
        "course",
        "university",
        "education",
        "book",
        "books"
    ],

    "bills": [
        "интернет",
        "свет",
        "газ",
        "вода",
        "электричество",
        "коммуналка",
        "телефон",
        "internet",
        "electricity",
        "water",
        "gas",
        "phone",
        "bills"
    ],

    # ========================================================
    # INCOME CATEGORIES
    # ========================================================

    "salary": [
        "зарплата",
        "зарплату",
        "зарплатой",
        "аванс",
        "оклад",
        "salary",
        "paycheck"
    ],

    "freelance": [
        "фриланс",
        "freelance"
    ],

    "business": [
        "бизнес",
        "business",
        "продажа",
        "продажи",
        "продал",
        "продала"
    ],

    "bonus": [
        "бонус",
        "премия",
        "bonus"
    ],

    "investment": [
        "инвестиция",
        "инвестиции",
        "дивиденд",
        "дивиденды",
        "investment",
        "dividend"
    ],

    "gift": [
        "подарок",
        "подарили",
        "подарил",
        "gift"
    ],

    "refund": [
        "возврат",
        "вернули",
        "вернул",
        "refund"
    ]
}


def extract_category(text):
    """
    Определяет категорию по ключевым словам.

    Если категория не найдена:
        возвращает "other".
    """

    if not text or not isinstance(text, str):
        return "other"

    text = text.lower().strip()

    for category, keywords in CATEGORY_KEYWORDS.items():

        for keyword in keywords:

            pattern = rf'(?<!\w){re.escape(keyword)}(?!\w)'

            if re.search(pattern, text):
                return category

    return "other"


# ============================================================
# DESCRIPTION
# ============================================================

def extract_description(text):
    """
    Извлекает описание транзакции.

    Удаляет:
        - сумму
        - валюту
        - служебные слова

    Сохраняет дефисы внутри слов.

    Примеры:

        "потратил 25к на кофе"
        -> "кофе"

        "что-то 25000"
        -> "что-то"

        "получил зарплату 5 млн"
        -> "получил зарплату"
    """

    if not text or not isinstance(text, str):
        return None

    description = text.lower().strip()

    # ========================================================
    # 1. Удаляем суммы с миллиардами / миллионами / тысячами
    # ========================================================

    description = re.sub(
        r'(?<!\w)'
        r'\d+(?:[.,]\d+)?\s*'
        r'(?:млрд|миллиард(?:а|ов)?|billion|bn|'
        r'млн|миллион(?:а|ов)?|million|'
        r'тыс|тысяч(?:а|и)?|тысячи|thousand)'
        r'(?!\w)',
        ' ',
        description
    )

    # ========================================================
    # 2. Удаляем суммы 25к / 25k
    # ========================================================

    description = re.sub(
        r'(?<!\d)'
        r'\d+(?:[.,]\d+)?\s*[кk]'
        r'(?![a-zа-яё])',
        ' ',
        description
    )

    # ========================================================
    # 3. Удаляем числа с разделителями тысяч
    # ========================================================

    description = re.sub(
        r'(?<!\d)'
        r'\d{1,3}(?:[ .]\d{3})+'
        r'(?!\d)',
        ' ',
        description
    )

    description = re.sub(
        r'(?<!\d)'
        r'\d{1,3}(?:,\d{3})+'
        r'(?!\d)',
        ' ',
        description
    )

    # ========================================================
    # 4. Удаляем обычные числа
    # ========================================================

    description = re.sub(
        r'(?<![\d.,])'
        r'\d+(?:[.,]\d+)?'
        r'(?![\d.,])',
        ' ',
        description
    )

    # ========================================================
    # 5. Удаляем валюты
    # ========================================================

    currency_patterns = [
        r'\buzs\b',
        r'\busd\b',
        r'\beur\b',
        r'\brub\b',

        r'\bсум\b',
        r'\bсумов\b',
        r'\bсўм\b',
        r"\bso['’]?m\b",
        r'\bsom\b',

        r'\bdollar\b',
        r'\bdollars\b',
        r'\bдоллар\b',
        r'\bдоллара\b',
        r'\bдолларов\b',

        r'\beuro\b',
        r'\beuros\b',
        r'\bевро\b',

        r'\bruble\b',
        r'\brubles\b',
        r'\bруб\b',
        r'\bрубль\b',
        r'\bрублей\b',

        r'\$',
        r'€',
        r'₽'
    ]

    for pattern in currency_patterns:
        description = re.sub(pattern, ' ', description)

    # ========================================================
    # 6. Удаляем служебные слова
    # ========================================================

    filler_words = [
        # Русский
        "потратил",
        "потратила",
        "купил",
        "купила",
        "заплатил",
        "заплатила",
        "расход",
        "расходы",
        "трата",
        "потратил на",
        "потратила на",

        # Доходы
        "получил",
        "получила",
        "получено",
        "получены",
        "заработал",
        "заработала",

        # Предлоги
        "на",
        "за",

        # English
        "spent",
        "spend",
        "bought",
        "buy",
        "paid",
        "for",
        "received",
        "receive",
        "earned",
        "earn"
    ]

    for word in sorted(filler_words, key=len, reverse=True):

        description = re.sub(
            rf'(?<!\w){re.escape(word)}(?!\w)',
            ' ',
            description
        )

    # ========================================================
    # 7. Убираем лишние символы
    # ========================================================

    # Дефис сохраняем:
    # "что-то" -> "что-то"

    description = re.sub(
        r'[^\w\sа-яё-]',
        ' ',
        description
    )

    # ========================================================
    # 8. Убираем лишние пробелы
    # ========================================================

    description = re.sub(
        r'\s+',
        ' ',
        description
    ).strip()

    if not description:
        return None

    return description


# ============================================================
# FULL TRANSACTION PARSER
# ============================================================

def parse_transaction(text):
    """
    Полностью разбирает свободный текст пользователя.

    Возвращает:

        {
            "amount": ...,
            "currency": ...,
            "category": ...,
            "description": ...
        }

    Если сумма отсутствует, отрицательная
    или равна 0:
        возвращает None.
    """

    if not text or not isinstance(text, str):
        return None

    amount = extract_amount(text)

    if amount is None:
        return None

    currency = extract_currency(text)
    category = extract_category(text)
    description = extract_description(text)

    return {
        "amount": amount,
        "currency": currency,
        "category": category,
        "description": description
    }