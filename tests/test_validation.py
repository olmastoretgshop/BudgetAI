from src.validation import (
    validate_amount,
    validate_currency,
    validate_category,
    validate_description,
    validate_transaction
)

# ============================================================
# TEST: AMOUNT
# ============================================================

print("=" * 60)
print("TEST: validate_amount()")
print("=" * 60)

amount_tests = [
    25000,
    100,
    0,
    -500,
    None,
    "25000"
]

for amount in amount_tests:
    result = validate_amount(amount)
    print(f"{repr(amount):<15} -> {result}")


# ============================================================
# TEST: CURRENCY
# ============================================================

print("\n" + "=" * 60)
print("TEST: validate_currency()")
print("=" * 60)

currency_tests = [
    "UZS",
    "USD",
    "EUR",
    "RUB",
    "GBP",
    None,
    ""
]

for currency in currency_tests:
    result = validate_currency(currency)
    print(f"{repr(currency):<15} -> {result}")


# ============================================================
# TEST: CATEGORY
# ============================================================

print("\n" + "=" * 60)
print("TEST: validate_category()")
print("=" * 60)

category_tests = [
    "food",
    "transport",
    "shopping",
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
    "other",
    "random",
    None,
    ""
]

for category in category_tests:
    result = validate_category(category)
    print(f"{repr(category):<20} -> {result}")


# ============================================================
# TEST: DESCRIPTION
# ============================================================

print("\n" + "=" * 60)
print("TEST: validate_description()")
print("=" * 60)

description_tests = [
    "кофе",
    "такси",
    "что-то",
    None,
    "",
    "   ",
    123
]

for description in description_tests:
    result = validate_description(description)
    print(f"{repr(description):<20} -> {result}")


# ============================================================
# TEST: FULL TRANSACTION
# ============================================================

print("\n" + "=" * 60)
print("TEST: validate_transaction()")
print("=" * 60)

transaction_tests = [
    {
        "amount": 25000,
        "currency": "UZS",
        "category": "food",
        "description": "кофе"
    },

    {
        "amount": 50,
        "currency": "USD",
        "category": "transport",
        "description": "taxi"
    },

    {
        "amount": 0,
        "currency": "UZS",
        "category": "food",
        "description": "кофе"
    },

    {
        "amount": -5000,
        "currency": "UZS",
        "category": "food",
        "description": "кофе"
    },

    {
        "amount": 25000,
        "currency": "GBP",
        "category": "food",
        "description": "кофе"
    },

    {
        "amount": 25000,
        "currency": "UZS",
        "category": "random",
        "description": "что-то"
    },

    {
        "amount": 25000,
        "currency": "UZS",
        "category": "food",
        "description": None
    },

    {
        "amount": 25000,
        "currency": "UZS",
        "category": "food",
        "description": ""
    }
]

for transaction in transaction_tests:
    result = validate_transaction(transaction)

    print(f"\nTransaction: {transaction}")
    print(f"Valid:       {result}")


# ============================================================
# TEST: INCOME TRANSACTIONS
# ============================================================

print("\n" + "=" * 60)
print("TEST: INCOME TRANSACTIONS")
print("=" * 60)

income_tests = [
    {
        "amount": 5000000,
        "currency": "UZS",
        "category": "salary",
        "description": "зарплата"
    },

    {
        "amount": 500,
        "currency": "USD",
        "category": "freelance",
        "description": "freelance"
    },

    {
        "amount": 250000,
        "currency": "UZS",
        "category": "bonus",
        "description": "бонус"
    },

    {
        "amount": 100000,
        "currency": "UZS",
        "category": "investment",
        "description": "дивиденды"
    },

    {
        "amount": 50000,
        "currency": "UZS",
        "category": "gift",
        "description": "подарок"
    },

    {
        "amount": 30000,
        "currency": "UZS",
        "category": "refund",
        "description": "возврат"
    },

    {
        "amount": 1000000,
        "currency": "UZS",
        "category": "business",
        "description": "продажа"
    },

    {
        "amount": 5000000,
        "currency": "UZS",
        "category": "other",
        "description": None
    }
]

for transaction in income_tests:
    result = validate_transaction(transaction)

    print(f"\nTransaction: {transaction}")
    print(f"Valid:       {result}")
