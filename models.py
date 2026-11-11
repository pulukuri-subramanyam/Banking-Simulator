from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Iterator

from exceptions import InsufficientFundsError, ValidationError

def validate_nonnegative_money(value: Decimal, label: str) -> None:
    if not isinstance(value, Decimal) or not value.is_finite() or value < 0 or value.as_tuple().exponent < -2:
        raise ValidationError(f"{label} must be finite, non-negative, and have at most two decimal places.")


def money(value: Decimal) -> str:
    # ASCII currency text keeps the app readable in older Windows consoles.
    return f"INR {value:,.2f}"


@dataclass
class Transaction:
    transaction_id: str
    timestamp: datetime
    kind: str
    amount: Decimal
    account_number: str
    related_account: str | None
    balance_after: Decimal

    def __str__(self) -> str:
        related = f" (related: {self.related_account})" if self.related_account else ""
        return f"{self.transaction_id} | {self.timestamp:%Y-%m-%d %H:%M} | {self.kind} | {money(self.amount)}{related} | balance {money(self.balance_after)}"


@dataclass
class Customer:
    customer_id: str
    name: str
    phone: str
    email: str
    accounts: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"{self.customer_id} - {self.name} ({self.phone}, {self.email})"


class Account:
    account_type = "Account"

    def __init__(self, number: str, customer_id: str, opening_balance: Decimal) -> None:
        validate_nonnegative_money(opening_balance, "Opening balance")
        self.number = number
        self.customer_id = customer_id
        self._balance = opening_balance
        self.transactions: list[Transaction] = []

    @property
    def balance(self) -> Decimal:
        return self._balance

    def can_withdraw(self, amount: Decimal) -> bool:
        return amount <= self._balance

    def withdraw(self, amount: Decimal) -> None:
        if not isinstance(amount, Decimal) or not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
            raise ValidationError("Transaction amount must be finite and positive with at most two decimal places.")
        if not self.can_withdraw(amount):
            raise InsufficientFundsError("This withdrawal would break the account rule.")
        self._balance -= amount

    def deposit(self, amount: Decimal) -> None:
        if not isinstance(amount, Decimal) or not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
            raise ValidationError("Transaction amount must be finite and positive with at most two decimal places.")
        self._balance += amount

    def __str__(self) -> str:
        return f"{self.number} | {self.account_type} | customer {self.customer_id} | {money(self.balance)}"


class SavingsAccount(Account):
    account_type = "Savings"

    def __init__(self, number: str, customer_id: str, opening_balance: Decimal, minimum_balance: Decimal) -> None:
        validate_nonnegative_money(minimum_balance, "Savings minimum balance")
        if opening_balance < minimum_balance:
            raise ValidationError(f"Savings opening balance must be at least {money(minimum_balance)}.")
        super().__init__(number, customer_id, opening_balance)
        self.minimum_balance = minimum_balance

    def can_withdraw(self, amount: Decimal) -> bool:
        return self._balance - amount >= self.minimum_balance


class CurrentAccount(Account):
    account_type = "Current"

    def __init__(self, number: str, customer_id: str, opening_balance: Decimal, overdraft_limit: Decimal) -> None:
        validate_nonnegative_money(overdraft_limit, "Overdraft limit")
        super().__init__(number, customer_id, opening_balance)
        self.overdraft_limit = overdraft_limit

    def can_withdraw(self, amount: Decimal) -> bool:
        return self._balance - amount >= -self.overdraft_limit


def filtered_transactions(account: Account, kind: str | None = None) -> Iterator[Transaction]:
    """Yield matching transactions without creating another list."""
    yield from (item for item in account.transactions if kind is None or item.kind == kind)

