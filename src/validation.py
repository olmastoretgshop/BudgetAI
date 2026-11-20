
# ============================================================
# VALIDATION
# ============================================================

ALLOWED_CURRENCIES = {
    "UZS",
    "USD",
    "EUR",
    "RUB"
}


ALLOWED_CATEGORIES = {
    "food",
    "transport",
    "shopping",
    "entertainment",
    "health",
    "education",
    "bills",
    "salary",
    "freelance",
    "business",
    "bonus",
    "investment",
    "gift",
    "refund",
    "other"
}


# ============================================================
# AMOUNT VALIDATION
# ============================================================

def validate_amount(amount):
    """
    Проверяет корректность суммы.

    Валидная сумма:
        - число
        - больше 0
    """

    if amount is None:
        return False

    if not isinstance(amount, (int, float)):
        return False

    if amount <= 0:
        return False

    return True


# ============================================================
# CURRENCY VALIDATION
# ============================================================

def validate_currency(currency):
    """
    Проверяет, поддерживается ли валюта.
    """

    if not currency:
        return False

    return currency in ALLOWED_CURRENCIES


# ============================================================
# CATEGORY VALIDATION
# ============================================================

def validate_category(category):
    """
    Проверяет, существует ли такая категория.
    """

    if not category:
        return False

    return category in ALLOWED_CATEGORIES


# ============================================================
# DESCRIPTION VALIDATION
# ============================================================

def validate_description(description):
    """
    Проверяет описание транзакции.

    Description может быть None,
    потому что пользователь может написать только сумму:

        "25000"

    Но если описание существует,
    оно должно быть строкой и не должно быть пустым.
    """

    if description is None:
        return True

    if not isinstance(description, str):
        return False

    if not description.strip():
        return False

    return True


# ============================================================
# FULL TRANSACTION VALIDATION
# ============================================================

def validate_transaction(transaction):
    """
    Проверяет всю транзакцию.

    Ожидаемый формат:

        {
            "amount": 25000,
            "currency": "UZS",
            "category": "food",
            "description": "кофе"
        }

    Возвращает:
        True  -> транзакция валидна
        False -> транзакция невалидна
    """

    if not isinstance(transaction, dict):
        return False

    amount = transaction.get("amount")
    currency = transaction.get("currency")
    category = transaction.get("category")
    description = transaction.get("description")

    if not validate_amount(amount):
        return False

    if not validate_currency(currency):
        return False

    if not validate_category(category):
        return False

    if not validate_description(description):
        return False

    return True

