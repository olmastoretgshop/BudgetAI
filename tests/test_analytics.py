from datetime import datetime
from zoneinfo import ZoneInfo
from src.analytics import (
    calculate_summary,
    calculate_categories,
    get_top_expenses,
    compare_period_metrics,
    format_analytics_report,
    format_comparison_report,
    format_amount,
    get_period_ranges,
    filter_transactions_by_period
)


def test_analytics():
    tz = ZoneInfo("Asia/Tashkent")
    # Текущая дата фиксированная для воспроизводимости: 7 октября 2026
    fake_now = datetime(2026, 10, 7, 14, 0, 0, tzinfo=tz)

    # Тестовые данные транзакций:
    # Октябрь (текущий месяц)
    # Сентябрь (прошлый месяц)
    transactions = [
        # Сентябрь 2026
        (1, "expense", 2100000, "UZS", "shopping", "куртка", "2026-09-15 10:00:00"),
        (2, "income", 5000000, "UZS", "salary", "зарплата", "2026-09-05 10:00:00"),

        # Октябрь 2026
        (3, "expense", 850000, "UZS", "shopping", "куртка", "2026-10-02 12:00:00"),
        (4, "expense", 450000, "UZS", "food", "ресторан", "2026-10-03 13:00:00"),
        (5, "expense", 180000, "UZS", "transport", "бензин", "2026-10-04 14:00:00"),
        (6, "expense", 100000, "UZS", "entertainment", "кино", "2026-10-05 15:00:00"),
        (7, "expense", 170000, "UZS", "other", "мелочи", "2026-10-06 16:00:00"),
        # Итого расходы за октябрь: 850к + 450к + 180к + 100к + 170к = 1 750 000

        # Доходы за октябрь
        (8, "income", 5000000, "UZS", "salary", "зарплата", "2026-10-01 09:00:00"),
        (9, "income", 1200000, "UZS", "freelance", "сайт", "2026-10-03 11:00:00"),
        (10, "income", 300000, "UZS", "bonus", "премия", "2026-10-05 17:00:00"),
        # Итого доходы за октябрь: 6 500 000
    ]

    print("=" * 60)
    print("TEST 1: format_amount()")
    print("=" * 60)
    assert format_amount(1500000) == "1 500 000"
    assert format_amount(1750000) == "1 750 000"
    assert format_amount(2100000) == "2 100 000"
    assert format_amount(25.5) == "25.50"
    print("✓ format_amount passed")

    print("\n" + "=" * 60)
    print("TEST 2: compare_period_metrics() [Сентябрь 2.1M vs Октябрь 1.75M]")
    print("=" * 60)
    # Пример пользователя: Сентябрь 2 100 000, Октябрь 1 750 000 -> -16.7%
    pct, text = compare_period_metrics(1750000, 2100000)
    print(f"Calculated: {text}")
    assert text == "-16.7%"
    print("✓ compare_period_metrics passed")

    print("\n" + "=" * 60)
    print("TEST 3: calculate_summary() за Октябрь")
    print("=" * 60)
    curr_start, curr_end, _, _, _, _ = get_period_ranges("month", now=fake_now, tz=tz)
    oct_txs = filter_transactions_by_period(transactions, curr_start, curr_end, tz=tz)
    summary = calculate_summary(oct_txs)["UZS"]
    assert summary["income"] == 6500000
    assert summary["expense"] == 1750000
    assert summary["balance"] == 4750000
    assert summary["total_count"] == 8
    print(f"Доходы: {summary['income']}")
    print(f"Расходы: {summary['expense']}")
    print(f"Чистый баланс: {summary['balance']}")
    print(f"Операций: {summary['total_count']}")
    print("✓ calculate_summary passed")

    print("\n" + "=" * 60)
    print("TEST 4: calculate_categories() расходы")
    print("=" * 60)
    cats_exp = calculate_categories(oct_txs, tx_type="expense")["UZS"]
    top_cat = cats_exp["top_category"]
    print(f"Самая дорогая категория: {top_cat['category']} ({top_cat['amount']} — {top_cat['share']:.1f}%)")
    assert top_cat["category"] == "Shopping"
    assert top_cat["amount"] == 850000
    for cat in cats_exp["categories"]:
        print(f"• {cat['category']:<15} {format_amount(cat['amount']):<10} ({cat['share']:.1f}%)")
    print("✓ calculate_categories expenses passed")

    print("\n" + "=" * 60)
    print("TEST 5: calculate_categories() доходы")
    print("=" * 60)
    cats_inc = calculate_categories(oct_txs, tx_type="income")["UZS"]
    for cat in cats_inc["categories"]:
        print(f"• {cat['category']:<15} {format_amount(cat['amount']):<10} ({cat['share']:.1f}%)")
    assert cats_inc["categories"][0]["category"] == "Salary"
    assert cats_inc["categories"][0]["amount"] == 5000000
    print("✓ calculate_categories income passed")

    print("\n" + "=" * 60)
    print("TEST 6: get_top_expenses()")
    print("=" * 60)
    top_3 = get_top_expenses(oct_txs, limit=3)["UZS"]
    for i, t in enumerate(top_3, 1):
        print(f"{i}. {t['category']} ({t['description']}) — {format_amount(t['amount'])} UZS")
    assert top_3[0]["category"] == "Shopping"
    assert top_3[0]["amount"] == 850000
    assert top_3[1]["category"] == "Food"
    assert top_3[1]["amount"] == 450000
    assert top_3[2]["category"] == "Transport"
    assert top_3[2]["amount"] == 180000
    print("✓ get_top_expenses passed")

    print("\n" + "=" * 60)
    print("TEST 7: format_analytics_report('month')")
    print("=" * 60)
    report_month = format_analytics_report(transactions, period="month", now=fake_now, tz=tz)
    print(report_month)
    assert "850 000" in report_month
    assert "-16.7%" in report_month
    print("✓ format_analytics_report('month') passed")

    print("\n" + "=" * 60)
    print("TEST 8: format_analytics_report('all')")
    print("=" * 60)
    report_all = format_analytics_report(transactions, period="all", now=fake_now, tz=tz)
    print(report_all)
    print("✓ format_analytics_report('all') passed")

    print("\n" + "=" * 60)
    print("TEST 9: format_comparison_report()")
    print("=" * 60)
    compare_rep = format_comparison_report(transactions, now=fake_now, tz=tz)
    print(compare_rep)
    assert "-16.7%" in compare_rep
    print("✓ format_comparison_report passed")


if __name__ == "__main__":
    test_analytics()
