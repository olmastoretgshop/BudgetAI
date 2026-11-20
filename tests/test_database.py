from src.database import add_transaction, get_all_transactions

add_transaction(
    user_id=123456,
    transaction_type="expense",
    amount=25000,
    currency="UZS",
    category="food",
    description="coffee"
)

txs = get_all_transactions(123456)
print(f"Transaction added successfully! Total for user: {len(txs)}")