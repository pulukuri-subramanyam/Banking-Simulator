import unittest
from decimal import Decimal

from bank import Bank, parse_money
from exceptions import InsufficientFundsError, NotFoundError, ValidationError
from models import filtered_transactions


class BankingTests(unittest.TestCase):
    def setUp(self):
        self.bank = Bank()
        self.customer = self.bank.create_customer("Asha", "9876543210", "asha@example.com")

    def account(self, kind="current", opening="0.00"):
        return self.bank.create_account(self.customer.customer_id, kind, Decimal(opening))

    def test_unique_ids_and_multiple_accounts(self):
        other = self.bank.create_customer("Ben", "9999999999", "ben@example.com")
        self.assertNotEqual(self.customer.customer_id, other.customer_id)
        self.assertNotEqual(self.account().number, self.account().number)
        self.assertEqual(len(self.customer.accounts), 2)

    def test_deposit_and_invalid_amounts(self):
        account = self.account()
        self.bank.deposit(account.number, Decimal("25.50"))
        self.assertEqual(account.balance, Decimal("25.50"))
        for value in ["NaN", "Infinity", "1.234", "0"]:
            with self.assertRaises(ValidationError): parse_money(value)

    def test_savings_minimum_and_current_boundary(self):
        savings = self.account("savings", "100.00")
        with self.assertRaises(InsufficientFundsError): self.bank.withdraw(savings.number, Decimal("0.01"))
        current = self.account("current", "0.00")
        self.bank.withdraw(current.number, Decimal("500.00"))
        self.assertEqual(current.balance, Decimal("-500.00"))
        with self.assertRaises(InsufficientFundsError): self.bank.withdraw(current.number, Decimal("0.01"))

    def test_transfer_history_and_atomic_rejection(self):
        source, target = self.account("current", "100.00"), self.account("current", "0.00")
        self.bank.transfer(source.number, target.number, Decimal("40.00"))
        self.assertEqual(source.balance, Decimal("60.00"))
        self.assertEqual(target.balance, Decimal("40.00"))
        self.assertEqual(len(source.transactions), 1)
        self.assertEqual(len(target.transactions), 1)
        before = (source.balance, target.balance, len(source.transactions), len(target.transactions))
        with self.assertRaises(InsufficientFundsError): self.bank.transfer(source.number, target.number, Decimal("1000.00"))
        self.assertEqual(before, (source.balance, target.balance, len(source.transactions), len(target.transactions)))

    def test_summary_and_filter(self):
        account = self.account()
        self.bank.deposit(account.number, Decimal("10.00"))
        self.bank.withdraw(account.number, Decimal("2.00"))
        report = self.bank.summary()
        self.assertEqual(report["total_balance"], Decimal("8.00"))
        self.assertEqual(len(list(filtered_transactions(account, "Deposit"))), 1)

    def test_search_and_edge_cases(self):
        account = self.account("current", "0.00")
        self.assertEqual(len(self.bank.search_customers("asha")), 1)
        self.assertEqual(self.bank.search_accounts(account.number)[0], account)
        with self.assertRaises(ValidationError): self.bank.transfer(account.number, account.number, Decimal("1.00"))
        with self.assertRaises(ValidationError): self.bank.create_customer("", "123", "x@y.com")
        with self.assertRaises(NotFoundError): self.bank.get_account("missing")

    def test_business_logic_rejects_invalid_transaction_amounts(self):
        account = self.account()
        for amount in [Decimal("0"), Decimal("-1.00"), Decimal("1.001"), Decimal("NaN")]:
            with self.assertRaises(ValidationError): self.bank.deposit(account.number, amount)
        with self.assertRaises(ValidationError): Bank(overdraft_limit=Decimal("-1.00"))

    def test_failed_operations_do_not_change_state(self):
        account = self.account("current", "10.00")
        before = (account.balance, len(account.transactions))
        with self.assertRaises(InsufficientFundsError): self.bank.withdraw(account.number, Decimal("600.00"))
        self.assertEqual((account.balance, len(account.transactions)), before)

    def test_phone_validation_and_zero_opening_balance(self):
        self.assertEqual(self.bank.create_customer("Cara", "+91 98765-43210", "cara@example.com").name, "Cara")
        with self.assertRaises(ValidationError): self.bank.create_customer("Dan", "123", "dan@example.com")
        account = self.account("current", "0.00")
        self.assertEqual(account.balance, Decimal("0.00"))

    def test_opening_balance_and_limits_are_strictly_validated(self):
        for value in [Decimal("NaN"), Decimal("Infinity"), Decimal("1.001")]:
            with self.assertRaises(ValidationError):
                self.bank.create_account(self.customer.customer_id, "current", value)
            with self.assertRaises(ValidationError):
                Bank(minimum_savings_balance=value)

    def test_model_constructors_and_account_type_are_defensive(self):
        with self.assertRaises(ValidationError):
            self.bank.create_account(self.customer.customer_id, None, Decimal("0.00"))
        with self.assertRaises(ValidationError):
            self.bank.create_account(self.customer.customer_id, "current", Decimal("NaN"))

    def test_empty_reports_and_searches(self):
        empty_account = self.account()
        self.assertEqual(self.bank.search_customers("nobody"), [])
        self.assertEqual(self.bank.search_accounts("999999"), [])
        self.assertEqual(list(filtered_transactions(empty_account, "Deposit")), [])


if __name__ == "__main__": unittest.main()

