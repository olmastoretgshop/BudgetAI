import sqlite3


DB_NAME = "database/finance.db"


def create_database():
    connection = sqlite3.connect(DB_NAME)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            category TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


def add_transaction(
    user_id,
    transaction_type,
    amount,
    currency,
    category,
    description
):
    connection = sqlite3.connect(DB_NAME)

    connection.execute("""
        INSERT INTO transactions
        (user_id, type, amount, currency, category, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        transaction_type,
        amount,
        currency,
        category,
        description
    ))

    connection.commit()
    connection.close()


def get_balance(user_id):
    connection = sqlite3.connect(DB_NAME)

    cursor = connection.execute("""
        SELECT
            currency,
            SUM(
                CASE
                    WHEN type = 'income' THEN amount
                    WHEN type = 'expense' THEN -amount
                END
            ) AS balance
        FROM transactions
        WHERE user_id = ?
        GROUP BY currency
        ORDER BY currency
    """, (user_id,))

    balances = cursor.fetchall()

    connection.close()

    return balances


def get_history(user_id, limit=10):
    connection = sqlite3.connect(DB_NAME)

    cursor = connection.execute("""
        SELECT
            id,
            type,
            amount,
            currency,
            category,
            description,
            created_at
        FROM transactions
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, limit))

    transactions = cursor.fetchall()

    connection.close()

    return transactions


def get_all_transactions(user_id):
    connection = sqlite3.connect(DB_NAME)

    cursor = connection.execute("""
        SELECT
            id,
            type,
            amount,
            currency,
            category,
            description,
            created_at
        FROM transactions
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))

    transactions = cursor.fetchall()

    connection.close()

    return transactions


def delete_transaction(user_id, transaction_id):
    connection = sqlite3.connect(DB_NAME)

    cursor = connection.execute("""
        DELETE FROM transactions
        WHERE id = ? AND user_id = ?
    """, (
        transaction_id,
        user_id
    ))

    connection.commit()

    deleted = cursor.rowcount

    connection.close()

    return deleted > 0


def update_transaction(
    user_id,
    transaction_id,
    fields
):
    allowed_fields = {
        "amount",
        "currency",
        "category",
        "description"
    }

    if not fields:
        return False

    if any(field not in allowed_fields for field in fields):
        return False

    set_clause = ", ".join(
        f"{field} = ?" for field in fields
    )

    values = list(fields.values())
    values.extend([
        transaction_id,
        user_id
    ])

    connection = sqlite3.connect(DB_NAME)

    cursor = connection.execute(
        f"""
        UPDATE transactions
        SET {set_clause}
        WHERE id = ? AND user_id = ?
        """,
        values
    )

    connection.commit()

    updated = cursor.rowcount

    connection.close()

    return updated > 0


if __name__ == "__main__":
    create_database()
    print("Database created successfully!")

