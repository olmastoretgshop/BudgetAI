from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from src.database import (
    create_database,
    add_transaction,
    get_balance,
    get_history,
    get_all_transactions,
    delete_transaction,
    update_transaction
)

from src.parser import (
    parse_transaction,
    extract_category
)

from src.validation import validate_transaction

from src.analytics import (
    format_analytics_report,
    format_comparison_report
)

from datetime import datetime
from zoneinfo import ZoneInfo


# ============================================================
# BOT TOKEN
# ============================================================

TOKEN = "8872317208:AAHJIr8JOp7-hZkkaYY8sdiXxF1Nlt8R8QE"


# ============================================================
# /start
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я BudgetAI.\n\n"
        "Команды:\n"
        "/add — добавить расход (/add кофе 25000)\n"
        "/income — добавить доход (/income зарплата 5 млн)\n"
        "/balance — текущий баланс\n"
        "/history — история операций (/history 10)\n"
        "/analytics — финансовая аналитика (/analytics week/month/year)\n"
        "/delete — удалить операцию (/delete ID)\n"
        "/edit — изменить операцию (/edit ID поле значение)"
    )


# ============================================================
# /add
# ============================================================

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)

    transaction = parse_transaction(text)

    if transaction is None:
        await update.message.reply_text(
            "Не удалось распознать транзакцию.\n\n"
            "Примеры:\n"
            "/add кофе 25000\n"
            "/add кофе 25к\n"
            "/add taxi $25"
        )
        return

    if not validate_transaction(transaction):
        await update.message.reply_text(
            "Транзакция содержит некорректные данные."
        )
        return

    add_transaction(
        user_id=update.effective_user.id,
        transaction_type="expense",
        amount=transaction["amount"],
        currency=transaction["currency"],
        category=transaction["category"],
        description=transaction["description"]
    )

    amount = transaction["amount"]
    currency = transaction["currency"]
    category = transaction["category"]
    description = transaction["description"]

    formatted_amount = f"{amount:,.0f}".replace(",", " ")

    message = (
        "Расход добавлен:\n\n"
        f"Сумма: {formatted_amount} {currency}\n"
        f"Категория: {category}\n"
        f"Описание: {description or '—'}"
    )

    await update.message.reply_text(message)


# ============================================================
# /income
# ============================================================

async def income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)

    if not text:
        await update.message.reply_text(
            "Напиши сумму и описание дохода.\n\n"
            "Примеры:\n"
            "/income зарплата 5 млн\n"
            "/income получил зарплату 5 000 000 сум\n"
            "/income freelance $500\n"
            "/income бонус 250к"
        )
        return

    transaction = parse_transaction(text)

    if transaction is None:
        await update.message.reply_text(
            "Не удалось распознать сумму дохода.\n\n"
            "Примеры:\n"
            "/income зарплата 5 млн\n"
            "/income freelance $500"
        )
        return

    # ВАЖНО:
    # Не превращаем автоматически "other" в "salary".
    # Если категория не определена parser.py,
    # она останется "other".

    if not validate_transaction(transaction):
        await update.message.reply_text(
            "Данные дохода некорректны."
        )
        return

    add_transaction(
        user_id=update.effective_user.id,
        transaction_type="income",
        amount=transaction["amount"],
        currency=transaction["currency"],
        category=transaction["category"],
        description=transaction["description"]
    )

    formatted_amount = f"{transaction['amount']:,.0f}".replace(",", " ")

    await update.message.reply_text(
        "Доход добавлен.\n\n"
        f"+ {formatted_amount} {transaction['currency']}\n"
        f"Категория: {transaction['category']}\n"
        f"Описание: {transaction['description'] or '—'}"
    )


# ============================================================
# /balance
# ============================================================

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    transactions = get_history(
        update.effective_user.id,
        limit=100000
    )

    if not transactions:
        await update.message.reply_text(
            "У тебя пока нет транзакций."
        )
        return

    balances = {}

    for transaction in transactions:
        (
            transaction_id,
            transaction_type,
            amount,
            currency,
            category,
            description,
            created_at
        ) = transaction

        if currency not in balances:
            balances[currency] = {
                "income": 0,
                "expense": 0
            }

        if transaction_type == "income":
            balances[currency]["income"] += amount
        else:
            balances[currency]["expense"] += amount

    message = "Баланс\n\n"

    for currency, data in balances.items():
        income = data["income"]
        expense = data["expense"]
        balance_amount = income - expense

        formatted_income = f"{income:,.0f}".replace(",", " ")
        formatted_expense = f"{expense:,.0f}".replace(",", " ")
        formatted_balance = f"{balance_amount:,.0f}".replace(",", " ")

        message += (
            f"{currency}\n"
            f"Доходы:  {formatted_income}\n"
            f"Расходы: {formatted_expense}\n"
            f"Баланс:  {formatted_balance}\n\n"
        )

    await update.message.reply_text(message)


# ============================================================
# /history
# ============================================================

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Использование:

        /history
        /history 10
        /history 20

    По умолчанию показываются последние 10 операций.
    """

    # --------------------------------------------------------
    # Определяем количество операций
    # --------------------------------------------------------

    limit = 10

    if context.args:

        try:
            limit = int(context.args[0])

        except ValueError:
            await update.message.reply_text(
                "Некорректное количество операций.\n\n"
                "Используй:\n"
                "/history\n"
                "/history 10\n"
                "/history 20"
            )
            return

        if limit <= 0:
            await update.message.reply_text(
                "Количество операций должно быть больше 0."
            )
            return

        if limit > 100:
            await update.message.reply_text(
                "Максимум можно показать 100 операций."
            )
            return

    # --------------------------------------------------------
    # Получаем историю
    # --------------------------------------------------------

    transactions = get_history(
        update.effective_user.id,
        limit=limit
    )

    if not transactions:
        await update.message.reply_text(
            "У тебя пока нет транзакций."
        )
        return

    message = "История операций:\n\n"

    for transaction in transactions:

        (
            transaction_id,
            transaction_type,
            amount,
            currency,
            category,
            description,
            created_at
        ) = transaction

        # ----------------------------------------------------
        # Знак
        # ----------------------------------------------------

        sign = "+" if transaction_type == "income" else "-"

        # ----------------------------------------------------
        # Перевод UTC -> Asia/Tashkent
        # ----------------------------------------------------

        utc_time = datetime.strptime(
            created_at,
            "%Y-%m-%d %H:%M:%S"
        ).replace(
            tzinfo=ZoneInfo("UTC")
        )

        local_time = utc_time.astimezone(
            ZoneInfo("Asia/Tashkent")
        )

        formatted_time = local_time.strftime(
            "%d.%m.%Y %H:%M"
        )

        # ----------------------------------------------------
        # Формируем операцию
        # ----------------------------------------------------

        formatted_amount = f"{amount:,.0f}".replace(",", " ")

        message += (
            f"#{transaction_id} "
            f"{sign} {formatted_amount} {currency}\n"
            f"Категория: {category}\n"
            f"Описание: {description or '—'}\n"
            f"Дата: {formatted_time}\n\n"
        )

    await update.message.reply_text(message)


# ============================================================
# /delete
# ============================================================

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Использование:

        /delete ID

    После команды появляется подтверждение.
    """

    try:
        transaction_id = int(context.args[0])

    except (IndexError, ValueError):
        await update.message.reply_text(
            "Используй:\n"
            "/delete ID\n\n"
            "Например:\n"
            "/delete 5"
        )
        return

    # --------------------------------------------------------
    # Получаем историю пользователя
    # --------------------------------------------------------

    transactions = get_history(
        update.effective_user.id,
        limit=100000
    )

    transaction = None

    for item in transactions:

        if item[0] == transaction_id:
            transaction = item
            break

    # --------------------------------------------------------
    # Проверяем существование транзакции
    # --------------------------------------------------------

    if transaction is None:
        await update.message.reply_text(
            f"Транзакция #{transaction_id} не найдена."
        )
        return

    (
        transaction_id,
        transaction_type,
        amount,
        currency,
        category,
        description,
        created_at
    ) = transaction

    sign = "+" if transaction_type == "income" else "-"

    # --------------------------------------------------------
    # Кнопки подтверждения
    # --------------------------------------------------------

    keyboard = [
        [
            InlineKeyboardButton(
                "Удалить",
                callback_data=f"delete_confirm:{transaction_id}"
            ),
            InlineKeyboardButton(
                "Отмена",
                callback_data=f"delete_cancel:{transaction_id}"
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    formatted_amount = f"{amount:,.0f}".replace(",", " ")

    await update.message.reply_text(
        "Ты хочешь удалить эту транзакцию?\n\n"
        f"#{transaction_id} "
        f"{sign} {formatted_amount} {currency}\n"
        f"Категория: {category}\n"
        f"Описание: {description or '—'}",
        reply_markup=reply_markup
    )


# ============================================================
# DELETE CALLBACK
# ============================================================

async def delete_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Обрабатывает кнопки:
        Удалить
        Отмена
    """

    query = update.callback_query

    await query.answer()

    data = query.data

    # ========================================================
    # CANCEL
    # ========================================================

    if data.startswith("delete_cancel:"):

        await query.edit_message_text(
            "Удаление отменено."
        )

        return

    # ========================================================
    # CONFIRM
    # ========================================================

    if data.startswith("delete_confirm:"):

        try:
            transaction_id = int(
                data.split(":")[1]
            )

        except (IndexError, ValueError):

            await query.edit_message_text(
                "Ошибка удаления."
            )

            return

        deleted = delete_transaction(
            user_id=query.from_user.id,
            transaction_id=transaction_id
        )

        if deleted:

            await query.edit_message_text(
                f"Транзакция #{transaction_id} удалена."
            )

        else:

            await query.edit_message_text(
                "Транзакция не найдена."
            )


# ============================================================
# /edit
# ============================================================

async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        transaction_id = int(context.args[0])
        field = context.args[1].lower()
        value = " ".join(context.args[2:])

    except (IndexError, ValueError):

        await update.message.reply_text(
            "Используй:\n\n"
            "/edit ID поле значение\n\n"
            "Примеры:\n"
            "/edit 1 amount 30000\n"
            "/edit 1 description кофе\n"
            "/edit 1 category food\n"
            "/edit 1 currency USD"
        )

        return

    # ========================================================
    # ALLOWED FIELDS
    # ========================================================

    allowed_fields = {
        "amount",
        "currency",
        "category",
        "description"
    }

    if field not in allowed_fields:

        await update.message.reply_text(
            "Можно изменять только:\n\n"
            "amount\n"
            "currency\n"
            "category\n"
            "description"
        )

        return

    if not value:

        await update.message.reply_text(
            "Укажи новое значение."
        )

        return

    # ========================================================
    # AMOUNT
    # ========================================================

    if field == "amount":

        try:
            amount = float(value)

            if amount <= 0:
                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "Некорректная сумма.\n\n"
                "Пример:\n"
                "/edit 1 amount 30000"
            )

            return

        updated = update_transaction(
            user_id=update.effective_user.id,
            transaction_id=transaction_id,
            fields={
                "amount": amount
            }
        )

    # ========================================================
    # CURRENCY
    # ========================================================

    elif field == "currency":

        currency = value.upper()

        if currency not in {
            "UZS",
            "USD",
            "EUR",
            "RUB"
        }:

            await update.message.reply_text(
                "Некорректная валюта.\n\n"
                "Доступные валюты:\n"
                "UZS, USD, EUR, RUB"
            )

            return

        updated = update_transaction(
            user_id=update.effective_user.id,
            transaction_id=transaction_id,
            fields={
                "currency": currency
            }
        )

    # ========================================================
    # CATEGORY
    # ========================================================

    elif field == "category":

        category = value.lower()

        if category not in {
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
        }:

            await update.message.reply_text(
                "Некорректная категория.\n\n"
                "Доступные категории:\n"
                "food\n"
                "transport\n"
                "shopping\n"
                "entertainment\n"
                "health\n"
                "education\n"
                "bills\n"
                "salary\n"
                "freelance\n"
                "business\n"
                "bonus\n"
                "investment\n"
                "gift\n"
                "refund\n"
                "other"
            )

            return

        updated = update_transaction(
            user_id=update.effective_user.id,
            transaction_id=transaction_id,
            fields={
                "category": category
            }
        )

    # ========================================================
    # DESCRIPTION
    # ========================================================

    elif field == "description":

        description = value

        category = extract_category(
            description
        )

        updated = update_transaction(
            user_id=update.effective_user.id,
            transaction_id=transaction_id,
            fields={
                "description": description,
                "category": category
            }
        )

    # ========================================================
    # RESULT
    # ========================================================

    if not updated:

        await update.message.reply_text(
            f"Транзакция #{transaction_id} не найдена."
        )

        return

    await update.message.reply_text(
        f"Транзакция #{transaction_id} успешно обновлена."
    )


# ============================================================
# /analytics
# ============================================================

def get_analytics_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📅 Неделя", callback_data="analytics:week"),
            InlineKeyboardButton("🗓 Месяц", callback_data="analytics:month"),
            InlineKeyboardButton("📆 Год", callback_data="analytics:year"),
        ],
        [
            InlineKeyboardButton("📊 Всё время", callback_data="analytics:all"),
            InlineKeyboardButton("⚖️ Сравнение", callback_data="analytics:compare"),
        ]
    ])


async def analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    period = "all"
    if context.args:
        arg = context.args[0].lower().strip()
        if arg in ("week", "неделя", "w"):
            period = "week"
        elif arg in ("month", "месяц", "m"):
            period = "month"
        elif arg in ("year", "год", "y"):
            period = "year"
        elif arg in ("all", "все", "всё"):
            period = "all"
        elif arg in ("compare", "сравнение", "сравнить"):
            period = "compare"
        else:
            await update.message.reply_text(
                "Используй:\n\n"
                "/analytics — за всё время\n"
                "/analytics week — за неделю\n"
                "/analytics month — за месяц\n"
                "/analytics year — за год\n"
                "/analytics compare — сравнение периодов"
            )
            return

    transactions = get_all_transactions(update.effective_user.id)

    if not transactions:
        await update.message.reply_text(
            "У тебя пока нет транзакций для аналитики."
        )
        return

    if period == "compare":
        text = format_comparison_report(transactions)
    else:
        text = format_analytics_report(transactions, period=period)

    keyboard = get_analytics_keyboard()
    await update.message.reply_text(text, reply_markup=keyboard)


async def analytics_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    period = query.data.split(":")[1]

    transactions = get_all_transactions(query.from_user.id)

    if not transactions:
        await query.edit_message_text(
            "У тебя пока нет транзакций для аналитики."
        )
        return

    if period == "compare":
        text = format_comparison_report(transactions)
    else:
        text = format_analytics_report(transactions, period=period)

    keyboard = get_analytics_keyboard()

    try:
        await query.edit_message_text(text, reply_markup=keyboard)
    except Exception:
        pass


# ============================================================
# DATABASE
# ============================================================

create_database()


# ============================================================
# APPLICATION
# ============================================================

app = Application.builder().token(TOKEN).build()


# ============================================================
# COMMAND HANDLERS
# ============================================================

app.add_handler(
    CommandHandler("start", start)
)

app.add_handler(
    CommandHandler("add", add)
)

app.add_handler(
    CommandHandler("income", income)
)

app.add_handler(
    CommandHandler("balance", balance)
)

app.add_handler(
    CommandHandler("history", history)
)

app.add_handler(
    CommandHandler("analytics", analytics)
)

app.add_handler(
    CommandHandler("delete", delete)
)

app.add_handler(
    CommandHandler("edit", edit)
)


# ============================================================
# CALLBACK HANDLERS
# ============================================================

app.add_handler(
    CallbackQueryHandler(
        delete_callback,
        pattern=r"^delete_(confirm|cancel):\d+$"
    )
)

app.add_handler(
    CallbackQueryHandler(
        analytics_callback,
        pattern=r"^analytics:(week|month|year|all|compare)$"
    )
)


# ============================================================
# RUN BOT
# ============================================================

app.run_polling()

