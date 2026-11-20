from src.parser import (
    extract_amount,
    extract_currency,
    extract_category,
    extract_description,
    parse_transaction
)


# ============================================================
# TEST DATA
# ============================================================

tests = [
    "кофе 25000",
    "25 000 кофе",
    "потратил 25к на кофе",
    "coffee 25.000",
    "такси 25k",
    "обед 15000",
    "ничего не потратил",
    "купил одежду за 350000 сум",
    "заплатил 50$ за такси",
    "ресторан 120000 UZS",
    "movie 15k",
    "зарплата 5000000 сум",
    "метро 3000",
    "книга 45000",
    "интернет 100000"
]


# ============================================================
# TEST EXTRACT_AMOUNT
# ============================================================

print("=" * 60)
print("TEST: extract_amount()")
print("=" * 60)

for text in tests:
    result = extract_amount(text)
    print(f"{text:<35} -> {result}")


# ============================================================
# TEST EXTRACT_CURRENCY
# ============================================================

print("\n" + "=" * 60)
print("TEST: extract_currency()")
print("=" * 60)

currency_tests = [
    "кофе 25000",
    "кофе 25000 сум",
    "кофе 25000 UZS",
    "coffee 25$",
    "coffee 25 USD",
    "hotel 100 euro",
    "такси 500 рублей",
    "еда 25000 so'm"
]

for text in currency_tests:
    result = extract_currency(text)
    print(f"{text:<35} -> {result}")


# ============================================================
# TEST EXTRACT_CATEGORY
# ============================================================

print("\n" + "=" * 60)
print("TEST: extract_category()")
print("=" * 60)

category_tests = [
    "кофе 25000",
    "такси 25000",
    "купил одежду 350000",
    "кино 50000",
    "аптека 100000",
    "курс 500000",
    "интернет 100000",
    "зарплата 5000000",
    "что-то 25000"
]

for text in category_tests:
    result = extract_category(text)
    print(f"{text:<35} -> {result}")


# ============================================================
# TEST EXTRACT_DESCRIPTION
# ============================================================

print("\n" + "=" * 60)
print("TEST: extract_description()")
print("=" * 60)

description_tests = [
    "кофе 25000",
    "25 000 кофе",
    "потратил 25к на кофе",
    "coffee 25.000",
    "купил одежду за 350000 сум",
    "заплатил 50$ за такси",
    "ресторан 120000 UZS"
]

for text in description_tests:
    result = extract_description(text)
    print(f"{text:<35} -> {result}")


# ============================================================
# TEST FULL PARSER
# ============================================================

print("\n" + "=" * 60)
print("TEST: parse_transaction()")
print("=" * 60)
# ============================================================
# EDGE CASE TESTS
# ============================================================

print("\n" + "=" * 60)
print("TEST: EDGE CASES")
print("=" * 60)

edge_case_tests = [
    "кофе 25к",
    "25к кофе",
    "Кофе 25 000 сум",
    "потратил 1 250 000 на продукты",
    "taxi $25",
    "кофе",
    "25к",
    "25000",
    "-25000",
    "25.5k кофе",
    "1,500,000 сум продукты",
    "купил хлеб за 5 000",
    "coffee 10 usd",
    "100 евро кино",
    "500 рублей такси",
    "что-то 99999",
    "потратил 0 сум",
    "",
    "   ",
]

for text in edge_case_tests:
    result = parse_transaction(text)

    print(f"\nInput:  {repr(text)}")
    print(f"Result: {result}")


# ============================================================
# INCOME TESTS
# ============================================================

print("\n" + "=" * 60)
print("TEST: INCOME PARSING")
print("=" * 60)

income_tests = [
    "зарплата 5 млн",
    "зарплата 5000000",
    "freelance $500",
    "бонус 250к",
    "дивиденды 100000",
    "премия 1.5 млн",
    "бизнес 2 млрд",
    "подарок 50000",
    "возврат 30000",
    "получил зарплату 5 000 000 сум",
    "продажа 500 тыс",
    "5 млн",
    "250к",
]

for text in income_tests:
    result = parse_transaction(text)

    print(f"\nInput:  {repr(text)}")
    print(f"Result: {result}")