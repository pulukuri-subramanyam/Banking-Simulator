from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

from exceptions import InsufficientFundsError, NotFoundError, ValidationError
from models import Account, CurrentAccount, Customer, SavingsAccount, Transaction

MIN_SAVINGS_BALANCE = Decimal("100.00")
DEFAULT_OVERDRAFT_LIMIT = Decimal("500.00")


def parse_money(text: str, *, allow_zero: bool = False) -> Decimal:
    try:
        value = Decimal(text.strip())
    except (InvalidOperation, AttributeError):
        raise ValidationError("Enter a valid decimal amount, such as 250.00.")
    if not value.is_finite():
        raise ValidationError("Amount must be finite.")
    if value.as_tuple().exponent < -2 or value < 0 or (not allow_zero and value == 0):
        raise ValidationError("Amount must be positive with at most two decimal places.")
    return value.quantize(Decimal("0.01"))


class Bank:
    def __init__(self, minimum_savings_balance: Decimal = MIN_SAVINGS_BALANCE, overdraft_limit: Decimal = DEFAULT_OVERDRAFT_LIMIT) -> None:
        self._validate_nonnegative_amount(minimum_savings_balance, "Savings minimum balance")
        self._validate_nonnegative_amount(overdraft_limit, "Overdraft limit")
        self.minimum_savings_balance = minimum_savings_balance
        self.overdraft_limit = overdraft_limit
        self.customers: dict[str, Customer] = {}
        self.accounts: dict[str, Account] = {}
        self._customer_sequence = 1000
        self._account_sequence = 100000
        self._transaction_sequence = 1

    def create_customer(self, name: str, phone: str, email: str) -> Customer:
        """Create and return a customer after basic contact validation."""
        phone_digits = phone.strip().replace("+", "").replace("-", "").replace(" ", "")
        if not name.strip() or not phone.strip() or not email.strip() or "@" not in email:
            raise ValidationError("Name, phone, and a simple email containing @ are required.")
        if not phone_digits.isdigit() or not 7 <= len(phone_digits) <= 15:
            raise ValidationError("Phone must contain 7 to 15 digits.")
        self._customer_sequence += 1
        customer = Customer(f"C{self._customer_sequence}", name.strip(), phone.strip(), email.strip())
        self.customers[customer.customer_id] = customer
        return customer

    def get_customer(self, customer_id: str) -> Customer:
        try:
            return self.customers[customer_id.upper()]
        except KeyError:
            raise NotFoundError("Customer not found.")

    def create_account(self, customer_id: str, kind: str, opening_balance: Decimal) -> Account:
        """Create an account owned by an existing customer."""
        customer = self.get_customer(customer_id)
        self._validate_nonnegative_amount(opening_balance, "Opening balance")
        self._account_sequence += 1
        number = str(self._account_sequence)
        if not isinstance(kind, str):
            raise ValidationError("Account type must be savings or current.")
        if kind.lower() == "savings":
            account = SavingsAccount(number, customer.customer_id, opening_balance, self.minimum_savings_balance)
        elif kind.lower() == "current":
            account = CurrentAccount(number, customer.customer_id, opening_balance, self.overdraft_limit)
        else:
            raise ValidationError("Account type must be savings or current.")
        self.accounts[number] = account
        customer.accounts.append(number)
        return account

    def get_account(self, number: str) -> Account:
        try:
            return self.accounts[number.strip()]
        except KeyError:
            raise NotFoundError("Account not found.")

    def _record(self, account: Account, kind: str, amount: Decimal, related: str | None) -> None:
        tx = Transaction(f"T{self._transaction_sequence:05d}", datetime.now(), kind, amount, account.number, related, account.balance)
        self._transaction_sequence += 1
        account.transactions.append(tx)

    def deposit(self, number: str, amount: Decimal) -> None:
        """Deposit a validated amount and record the resulting balance."""
        self._validate_transaction_amount(amount)
        account = self.get_account(number)
        account.deposit(amount)
        self._record(account, "Deposit", amount, None)

    def withdraw(self, number: str, amount: Decimal) -> None:
        """Withdraw an amount if the account rule allows it."""
        self._validate_transaction_amount(amount)
        account = self.get_account(number)
        account.withdraw(amount)
        self._record(account, "Withdrawal", amount, None)

    def transfer(self, source_number: str, target_number: str, amount: Decimal) -> None:
        """Transfer money atomically between two different accounts."""
        self._validate_transaction_amount(amount)
        source = self.get_account(source_number)
        target = self.get_account(target_number)
        if source.number == target.number:
            raise ValidationError("A transfer must use two different accounts.")
        if not source.can_withdraw(amount):
            raise InsufficientFundsError("Transfer would break the source account rule.")
        source.withdraw(amount)
        target.deposit(amount)
        self._record(source, "Transfer out", amount, target.number)
        self._record(target, "Transfer in", amount, source.number)

    @staticmethod
    def _validate_transaction_amount(amount: Decimal) -> None:
        if not isinstance(amount, Decimal) or not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
            raise ValidationError("Transaction amount must be finite and positive with at most two decimal places.")

    @staticmethod
    def _validate_nonnegative_amount(amount: Decimal, label: str) -> None:
        if not isinstance(amount, Decimal) or not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
            raise ValidationError(f"{label} must be finite, non-negative, and have at most two decimal places.")

    def search_accounts(self, text: str) -> list[Account]:
        """Find accounts by account number or customer name."""
        query = text.lower()
        return [a for a in self.accounts.values() if query in a.number.lower() or query in self.customers[a.customer_id].name.lower()]

    def search_customers(self, text: str) -> list[Customer]:
        """Find customers by customer ID or name."""
        query = text.lower()
        return [c for c in self.customers.values() if query in c.customer_id.lower() or query in c.name.lower()]

    def summary(self) -> dict[str, object]:
        """Return counts, total balance, and sorted account report data."""
        accounts = list(self.accounts.values())
        return {
            "customers": len(self.customers),
            "accounts": len(accounts),
            "savings": sum(a.account_type == "Savings" for a in accounts),
            "current": sum(a.account_type == "Current" for a in accounts),
            "total_balance": sum((a.balance for a in accounts), Decimal("0.00")),
            "by_balance": sorted(accounts, key=lambda a: a.balance, reverse=True),
            "by_customer": sorted(accounts, key=lambda a: self.customers[a.customer_id].name.lower()),
        }

