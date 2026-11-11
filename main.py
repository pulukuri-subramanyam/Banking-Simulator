from bank import Bank, parse_money
from exceptions import BankingError
from models import filtered_transactions, money

def ask(prompt: str) -> str:
    return input(prompt).strip()

def show_accounts(accounts, bank: Bank) -> None:
    if not accounts:
        print("No matching accounts found.")
        return
    for account in accounts:
        print(f"{account} | owner: {bank.customers[account.customer_id].name}")

def print_help() -> None:
    """Explain the menu flow and the account rules to a new user."""
    print("""
Help
----
1. Create a customer first and note the generated customer ID.
2. Create one or more savings/current accounts using that ID.
3. Savings accounts must keep INR 100.00 after withdrawals.
4. Current accounts may use up to INR 500.00 overdraft.
5. Use positive amounts with at most two decimal places.
6. All records are temporary and reset when the program exits.
""")

def main() -> None:
    bank = Bank()
    print("\n=== Banking Simulator ===\nAll records are in memory and reset on exit.")
    while True:
        print("\n--- Customers and accounts ---\n1. Create customer       2. Find customer\n3. Create account        4. List/search accounts\n--- Banking operations ---\n5. Deposit               6. Withdraw\n7. Transfer\n--- Reports ---\n8. Account history       9. Summary\n--- Other ---\n10. Help                 11. Exit")
        try:
            choice = ask("Choose an option: ")
            if choice == "1":
                customer = bank.create_customer(ask("Name: "), ask("Phone: "), ask("Email: "))
                print(customer)
            elif choice == "2":
                matches = bank.search_customers(ask("Search by customer ID or name: "))
                if not matches:
                    print("No matching customers found.")
                for customer in matches:
                    print(customer, "| accounts:", ", ".join(customer.accounts) or "none")
            elif choice == "3":
                opening = parse_money(ask("Opening balance (0 allowed): "), allow_zero=True)
                account = bank.create_account(ask("Customer ID: "), ask("Type (savings/current): "), opening)
                owner = bank.customers[account.customer_id].name
                print(f"Created {account}. Owner: {owner}.")
                print(f"Rule: savings keep {money(bank.minimum_savings_balance)} minimum; current accounts allow {money(bank.overdraft_limit)} overdraft.")
            elif choice == "4":
                query = ask("Search by account number or customer name (blank for all): ")
                accounts = bank.search_accounts(query) if query else list(bank.accounts.values())
                sort_by = ask("Sort by (balance/customer/none): ").lower()
                if sort_by == "balance":
                    accounts.sort(key=lambda a: a.balance, reverse=True)
                elif sort_by == "customer":
                    accounts.sort(key=lambda a: bank.customers[a.customer_id].name.lower())
                show_accounts(accounts, bank)
            elif choice in {"5", "6"}:
                amount = parse_money(ask("Amount: "))
                number = ask("Account number: ")
                if ask("Confirm operation? (y/n): ").lower() != "y":
                    print("Operation cancelled.")
                else:
                    operation = bank.deposit if choice == "5" else bank.withdraw
                    operation(number, amount)
                    print("Operation successful.")
            elif choice == "7":
                source, target, amount = ask("From account: "), ask("To account: "), parse_money(ask("Amount: "))
                if ask("Confirm transfer? (y/n): ").lower() != "y":
                    print("Transfer cancelled.")
                else:
                    bank.transfer(source, target, amount)
                    print("Transfer successful.")
                    print(f"From balance: {money(bank.get_account(source).balance)} | To balance: {money(bank.get_account(target).balance)}")
            elif choice == "8":
                account = bank.get_account(ask("Account number: "))
                kind = ask("Filter (all/deposit/withdrawal/transfer): ").lower()
                if kind not in {"all", "deposit", "withdrawal", "transfer"}:
                    print("Invalid filter. Choose all, deposit, withdrawal, or transfer.")
                    continue
                selected = {"all": None, "deposit": "Deposit", "withdrawal": "Withdrawal"}.get(kind)
                transactions = list(filtered_transactions(account, selected))
                if kind == "transfer":
                    transactions = [t for t in transactions if t.kind.startswith("Transfer")]
                if not transactions:
                    print("No transactions found.")
                for transaction in transactions:
                    is_transfer = transaction.kind.startswith("Transfer")
                    if kind != "transfer" or is_transfer:
                        print(transaction)
            elif choice == "9":
                report = bank.summary()
                print(f"Customers: {report['customers']} | Accounts: {report['accounts']} | Savings: {report['savings']} | Current: {report['current']} | Total: {money(report['total_balance'])}")
                print("\nBy balance:")
                show_accounts(report["by_balance"], bank)
                print("\nBy customer:")
                show_accounts(report["by_customer"], bank)
            elif choice == "10":
                print_help()
            elif choice == "11":
                print("Goodbye!")
                return
            else:
                print("Choose a number from 1 to 11.")
        except (BankingError, ValueError) as error:
            print(f"Error: {error}")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return

if __name__ == "__main__": main()
