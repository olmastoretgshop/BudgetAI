from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict


MONTH_NAMES_RU = {
    1: "Январь",
    2: "Февраль",
    3: "Март",
    4: "Апрель",
    5: "Май",
    6: "Июнь",
    7: "Июль",
    8: "Август",
    9: "Сентябрь",
    10: "Октябрь",
    11: "Ноябрь",
    12: "Декабрь"
}

DEFAULT_TIMEZONE = ZoneInfo("Asia/Tashkent")


def parse_db_datetime(dt_val, tz=DEFAULT_TIMEZONE):
    """
    Преобразует строку даты из базы данных (UTC) в datetime с нужным часовым поясом.
    """
    if dt_val is None:
        return None

    if isinstance(dt_val, datetime):
        if dt_val.tzinfo is None:
            return dt_val.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
        return dt_val.astimezone(tz)

    dt_str = str(dt_val).strip()

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(dt_str, fmt)
            return parsed.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(dt_str).astimezone(tz)
    except Exception:
        return None


def format_amount(amount):
    """
    Форматирует число с разделением тысяч пробелами:
    1500000 -> "1 500 000"
    25.5 -> "25.50"
    """
    if amount is None:
        return "0"

    if isinstance(amount, (int, float)) and amount == int(amount):
        return f"{int(amount):,}".replace(",", " ")

    return f"{amount:,.2f}".replace(",", " ")


def get_period_ranges(period="all", now=None, tz=DEFAULT_TIMEZONE):
    """
    Возвращает диапазоны дат для текущего и предшествующего периода:
    (current_start, current_end, current_label, prev_start, prev_end, prev_label)
    """
    if now is None:
        now = datetime.now(tz)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=tz)
    else:
        now = now.astimezone(tz)

    period = (period or "all").lower().strip()

    if period in ("week", "неделя", "w"):
        # Текущая неделя (начиная с понедельника 00:00:00)
        curr_start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        curr_end = now
        curr_label = "Текущая неделя"

        prev_start = curr_start - timedelta(days=7)
        prev_end = curr_start - timedelta(microseconds=1)
        prev_label = "Прошлая неделя"

        return curr_start, curr_end, curr_label, prev_start, prev_end, prev_label

    elif period in ("month", "месяц", "m"):
        # Текущий месяц (с 1-го числа 00:00:00)
        curr_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        curr_end = now
        curr_label = f"{MONTH_NAMES_RU.get(now.month, '')}"

        # Прошлый месяц
        if now.month == 1:
            prev_year = now.year - 1
            prev_month = 12
        else:
            prev_year = now.year
            prev_month = now.month - 1

        prev_start = datetime(prev_year, prev_month, 1, 0, 0, 0, tzinfo=tz)
        prev_end = curr_start - timedelta(microseconds=1)
        prev_label = f"{MONTH_NAMES_RU.get(prev_month, '')}"

        return curr_start, curr_end, curr_label, prev_start, prev_end, prev_label

    elif period in ("year", "год", "y"):
        # Текущий год
        curr_start = datetime(now.year, 1, 1, 0, 0, 0, tzinfo=tz)
        curr_end = now
        curr_label = f"{now.year} год"

        prev_start = datetime(now.year - 1, 1, 1, 0, 0, 0, tzinfo=tz)
        prev_end = curr_start - timedelta(microseconds=1)
        prev_label = f"{now.year - 1} год"

        return curr_start, curr_end, curr_label, prev_start, prev_end, prev_label

    else:
        # "all" - за всё время
        # Для сравнения берем текущий календарный месяц и прошлый календарный месяц
        curr_start = None
        curr_end = None
        curr_label = "Всё время"

        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 1:
            prev_year = now.year - 1
            prev_month = 12
        else:
            prev_year = now.year
            prev_month = now.month - 1

        prev_start = datetime(prev_year, prev_month, 1, 0, 0, 0, tzinfo=tz)
        prev_end = month_start - timedelta(microseconds=1)

        prev_label = f"{MONTH_NAMES_RU.get(prev_month, '')}"
        comp_curr_label = f"{MONTH_NAMES_RU.get(now.month, '')}"

        return curr_start, curr_end, curr_label, prev_start, prev_end, (prev_label, comp_curr_label)


def filter_transactions_by_period(transactions, start_dt=None, end_dt=None, tz=DEFAULT_TIMEZONE):
    """
    Фильтрует транзакции по диапазону дат [start_dt, end_dt].
    """
    if start_dt is None and end_dt is None:
        return list(transactions)

    filtered = []
    for tx in transactions:
        created_at_str = tx[6] if isinstance(tx, (tuple, list)) else tx.get("created_at")
        dt = parse_db_datetime(created_at_str, tz)

        if dt is None:
            continue

        if start_dt is not None and dt < start_dt:
            continue

        if end_dt is not None and dt > end_dt:
            continue

        filtered.append(tx)

    return filtered


def calculate_summary(transactions):
    """
    Рассчитывает общие доходы, расходы, чистый баланс и количество операций.
    Группирует по валютам:
    {
        "UZS": {
            "income": 5000000,
            "expense": 1750000,
            "balance": 3250000,
            "total_count": 15,
            "income_count": 2,
            "expense_count": 13
        },
        ...
    }
    """
    data_by_currency = defaultdict(lambda: {
        "income": 0.0,
        "expense": 0.0,
        "balance": 0.0,
        "total_count": 0,
        "income_count": 0,
        "expense_count": 0
    })

    for tx in transactions:
        if isinstance(tx, (tuple, list)):
            _, tx_type, amount, currency, _, _, _ = tx
        else:
            tx_type = tx.get("type")
            amount = tx.get("amount")
            currency = tx.get("currency")

        amount = float(amount or 0)
        curr_dict = data_by_currency[currency]

        curr_dict["total_count"] += 1

        if tx_type == "income":
            curr_dict["income"] += amount
            curr_dict["income_count"] += 1
        elif tx_type == "expense":
            curr_dict["expense"] += amount
            curr_dict["expense_count"] += 1

    for curr_dict in data_by_currency.values():
        curr_dict["balance"] = curr_dict["income"] - curr_dict["expense"]

    return dict(data_by_currency)


def calculate_categories(transactions, tx_type="expense"):
    """
    Рассчитывает суммы и доли по категориям для указанного типа ('expense' или 'income').
    Группирует по валютам.
    Возвращает для каждой валюты:
    {
        "currency": {
            "total": float,
            "categories": [
                {"category": "Food", "amount": 450000, "share": 25.7},
                ...
            ],
            "top_category": {"category": "Food", "amount": 450000, "share": 25.7} или None
        }
    }
    """
    res = defaultdict(lambda: {
        "total": 0.0,
        "cat_sums": defaultdict(float)
    })

    for tx in transactions:
        if isinstance(tx, (tuple, list)):
            _, item_type, amount, currency, category, _, _ = tx
        else:
            item_type = tx.get("type")
            amount = tx.get("amount")
            currency = tx.get("currency")
            category = tx.get("category")

        if item_type != tx_type:
            continue

        amount = float(amount or 0)
        cat_name = (category or "other").capitalize()

        res[currency]["total"] += amount
        res[currency]["cat_sums"][cat_name] += amount

    output = {}
    for currency, data in res.items():
        total = data["total"]
        cat_list = []

        # Сортируем по убыванию суммы
        sorted_cats = sorted(data["cat_sums"].items(), key=lambda x: x[1], reverse=True)

        for cat_name, cat_amount in sorted_cats:
            share = (cat_amount / total * 100.0) if total > 0 else 0.0
            cat_list.append({
                "category": cat_name,
                "amount": cat_amount,
                "share": share
            })

        top_cat = cat_list[0] if cat_list else None

        output[currency] = {
            "total": total,
            "categories": cat_list,
            "top_category": top_cat
        }

    return output


def get_top_expenses(transactions, limit=3):
    """
    Возвращает самые крупные расходы, сгруппированные по валютам:
    {
        "currency": [
            {
                "id": 1,
                "category": "Shopping",
                "amount": 850000,
                "description": "куртка",
                "created_at": "..."
            },
            ...
        ]
    }
    """
    by_currency = defaultdict(list)

    for tx in transactions:
        if isinstance(tx, (tuple, list)):
            tx_id, tx_type, amount, currency, category, description, created_at = tx
        else:
            tx_id = tx.get("id")
            tx_type = tx.get("type")
            amount = tx.get("amount")
            currency = tx.get("currency")
            category = tx.get("category")
            description = tx.get("description")
            created_at = tx.get("created_at")

        if tx_type != "expense":
            continue

        by_currency[currency].append({
            "id": tx_id,
            "category": (category or "other").capitalize(),
            "amount": float(amount or 0),
            "description": description,
            "created_at": created_at
        })

    output = {}
    for currency, items in by_currency.items():
        items.sort(key=lambda x: x["amount"], reverse=True)
        output[currency] = items[:limit]

    return dict(output)


def compare_period_metrics(current_expenses, prev_expenses):
    """
    Сравнивает расходы за два периода и возвращает процент изменения:
    например, -16.7% или +25.0%.
    Формула: ((current - prev) / prev) * 100
    """
    if prev_expenses > 0:
        change_pct = ((current_expenses - prev_expenses) / prev_expenses) * 100.0
        return change_pct, f"{change_pct:+.1f}%"
    elif current_expenses > 0:
        return 100.0, "+100.0%"
    else:
        return 0.0, "0.0%"


def format_analytics_report(all_user_transactions, period="all", now=None, tz=DEFAULT_TIMEZONE):
    """
    Формирует полный текст аналитического отчета по запросу пользователя.
    Включает:
    1. Общие показатели (доходы, расходы, баланс, операции)
    2. Аналитику за выбранный период (week, month, year, all)
    3. Расходы по категориям (доли %, самая дорогая категория)
    4. Доходы по категориям
    5. Самые крупные расходы (Топ-3)
    6. Сравнение периодов (например, Сентябрь vs Октябрь)
    """
    if not all_user_transactions:
        return "У тебя пока нет транзакций для аналитики."

    if now is None:
        now = datetime.now(tz)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=tz)

    (
        curr_start,
        curr_end,
        curr_label,
        prev_start,
        prev_end,
        prev_label_info
    ) = get_period_ranges(period, now=now, tz=tz)

    # Текущие транзакции за период
    current_txs = filter_transactions_by_period(all_user_transactions, curr_start, curr_end, tz=tz)

    if not current_txs:
        period_title = {
            "week": "за текущую неделю",
            "month": f"за {curr_label}",
            "year": f"за {curr_label}",
            "all": "за всё время"
        }.get(period, "за выбранный период")
        return f"За {period_title} пока нет транзакций."

    # Предыдущие транзакции для сравнения
    prev_txs = filter_transactions_by_period(all_user_transactions, prev_start, prev_end, tz=tz)

    # Для "all" текущий месяц для блока сравнения:
    if period == "all":
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        comp_curr_txs = filter_transactions_by_period(all_user_transactions, month_start, now, tz=tz)
        prev_label, comp_curr_label = prev_label_info
    else:
        comp_curr_txs = current_txs
        prev_label = prev_label_info
        comp_curr_label = curr_label

    summary_by_curr = calculate_summary(current_txs)
    prev_summary_by_curr = calculate_summary(prev_txs)
    comp_curr_summary_by_curr = calculate_summary(comp_curr_txs)

    expense_cats_by_curr = calculate_categories(current_txs, tx_type="expense")
    income_cats_by_curr = calculate_categories(current_txs, tx_type="income")
    top_expenses_by_curr = get_top_expenses(current_txs, limit=3)

    # Формируем заголовок периода
    if period == "week":
        header = f"📊 Аналитика за неделю ({curr_label})"
    elif period == "month":
        header = f"📊 Аналитика за месяц ({curr_label} {now.year})"
    elif period == "year":
        header = f"📊 Аналитика за год ({curr_label})"
    else:
        header = "📊 Аналитика за всё время"

    lines = [header, ""]

    currencies = sorted(summary_by_curr.keys())

    for idx, currency in enumerate(currencies):
        summary = summary_by_curr[currency]

        if len(currencies) > 1:
            lines.append(f"══════ {currency} ══════")

        # 1 & 2. Общие показатели
        income_str = format_amount(summary["income"])
        expense_str = format_amount(summary["expense"])
        bal_num = summary["balance"]
        bal_sign = "+" if bal_num > 0 else ""
        bal_str = f"{bal_sign}{format_amount(bal_num)}"

        lines.append(f"💰 Общие показатели ({currency}):")
        lines.append(f"• Доходы: {income_str}")
        lines.append(f"• Расходы: {expense_str}")
        lines.append(f"• Чистый баланс: {bal_str}")
        lines.append(f"• Количество операций: {summary['total_count']}")
        lines.append("")

        # 3. Расходы по категориям
        exp_data = expense_cats_by_curr.get(currency)
        if exp_data and exp_data["categories"]:
            lines.append("📉 Расходы по категориям:")
            for cat in exp_data["categories"]:
                cat_amount_str = format_amount(cat["amount"])
                lines.append(f"• {cat['category']:<15} {cat_amount_str} ({cat['share']:.1f}%)")

            if exp_data["top_category"]:
                top = exp_data["top_category"]
                top_amt_str = format_amount(top["amount"])
                lines.append("")
                lines.append(
                    f"🏆 Самая дорогая категория: {top['category']} "
                    f"({top_amt_str} {currency} — {top['share']:.1f}%)"
                )
            lines.append("")
        elif summary["expense_count"] == 0:
            lines.append("📉 Расходы по категориям: расходов нет\n")

        # 4. Доходы по категориям
        inc_data = income_cats_by_curr.get(currency)
        if inc_data and inc_data["categories"]:
            lines.append("📈 Доходы по категориям:")
            for cat in inc_data["categories"]:
                cat_amount_str = format_amount(cat["amount"])
                lines.append(f"• {cat['category']:<15} {cat_amount_str} ({cat['share']:.1f}%)")
            lines.append("")
        elif summary["income_count"] == 0:
            lines.append("📈 Доходы по категориям: доходов нет\n")

        # 5. Самые крупные расходы
        top_exp_list = top_expenses_by_curr.get(currency, [])
        if top_exp_list:
            lines.append("🔥 Самые крупные расходы:")
            for rank, item in enumerate(top_exp_list, 1):
                amt_str = format_amount(item["amount"])
                desc_suffix = f" ({item['description']})" if item.get("description") else ""
                lines.append(f"{rank}. {item['category']}{desc_suffix} — {amt_str} {currency}")
            lines.append("")

        # 6. Сравнение периодов
        prev_curr_sum = prev_summary_by_curr.get(currency, {"expense": 0.0, "income": 0.0})
        comp_curr_sum = comp_curr_summary_by_curr.get(currency, {"expense": 0.0, "income": 0.0})

        curr_exp = comp_curr_sum["expense"]
        prev_exp = prev_curr_sum["expense"]

        if prev_exp > 0 or curr_exp > 0:
            _, change_text = compare_period_metrics(curr_exp, prev_exp)
            lines.append("⚖️ Сравнение периодов:")
            lines.append(f"{prev_label}:")
            lines.append(f"Расходы: {format_amount(prev_exp)} {currency}")
            lines.append("")
            lines.append(f"{comp_curr_label}:")
            lines.append(f"Расходы: {format_amount(curr_exp)} {currency}")
            lines.append("")
            lines.append(f"Изменение: {change_text}")
            lines.append("")
        else:
            lines.append("⚖️ Сравнение периодов: нет данных для сравнения\n")

    return "\n".join(lines).strip()


def format_comparison_report(all_user_transactions, now=None, tz=DEFAULT_TIMEZONE):
    """
    Формирует детальный отчет по сравнению двух последних месяцев.
    """
    if not all_user_transactions:
        return "У тебя пока нет транзакций для сравнения."

    if now is None:
        now = datetime.now(tz)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=tz)

    # Текущий месяц
    curr_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    curr_end = now
    curr_label = f"{MONTH_NAMES_RU.get(now.month, '')}"

    # Прошлый месяц
    if now.month == 1:
        prev_year = now.year - 1
        prev_month = 12
    else:
        prev_year = now.year
        prev_month = now.month - 1

    prev_start = datetime(prev_year, prev_month, 1, 0, 0, 0, tzinfo=tz)
    prev_end = curr_start - timedelta(microseconds=1)
    prev_label = f"{MONTH_NAMES_RU.get(prev_month, '')}"

    curr_txs = filter_transactions_by_period(all_user_transactions, curr_start, curr_end, tz=tz)
    prev_txs = filter_transactions_by_period(all_user_transactions, prev_start, prev_end, tz=tz)

    curr_summary = calculate_summary(curr_txs)
    prev_summary = calculate_summary(prev_txs)

    all_currencies = sorted(set(curr_summary.keys()) | set(prev_summary.keys()))

    if not all_currencies:
        return "Нет данных за последние месяцы для сравнения."

    lines = [f"⚖️ Сравнение периодов: {prev_label} vs {curr_label}", ""]

    for currency in all_currencies:
        c_data = curr_summary.get(currency, {"income": 0.0, "expense": 0.0, "total_count": 0})
        p_data = prev_summary.get(currency, {"income": 0.0, "expense": 0.0, "total_count": 0})

        if len(all_currencies) > 1:
            lines.append(f"══════ {currency} ══════")

        lines.append(f"{prev_label}:")
        lines.append(f"• Доходы: {format_amount(p_data['income'])} {currency}")
        lines.append(f"• Расходы: {format_amount(p_data['expense'])} {currency}")
        lines.append(f"• Операций: {p_data['total_count']}")
        lines.append("")

        lines.append(f"{curr_label}:")
        lines.append(f"• Доходы: {format_amount(c_data['income'])} {currency}")
        lines.append(f"• Расходы: {format_amount(c_data['expense'])} {currency}")
        lines.append(f"• Операций: {c_data['total_count']}")
        lines.append("")

        _, exp_change_str = compare_period_metrics(c_data["expense"], p_data["expense"])
        _, inc_change_str = compare_period_metrics(c_data["income"], p_data["income"])

        lines.append("📊 Изменения:")
        lines.append(f"• Расходы: {format_amount(p_data['expense'])} → {format_amount(c_data['expense'])} ({exp_change_str})")
        lines.append(f"• Доходы: {format_amount(p_data['income'])} → {format_amount(c_data['income'])} ({inc_change_str})")
        lines.append("")

    return "\n".join(lines).strip()
