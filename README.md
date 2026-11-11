# Banking Simulator

A simple terminal banking simulator for creating customers, managing accounts, and performing everyday banking operations.

## What you can do

- Create customers with contact details.
- Create savings and current accounts.
- Give one customer multiple accounts.
- Deposit, withdraw, and transfer money.
- Search customers and accounts.
- View account transaction history.
- Filter history by transaction type.
- Sort accounts by balance or customer name.
- View account and customer summary reports.

## Requirements

- Python 3.10 or newer.
- No external packages are required.

## Run the simulator

```bash
python main.py
```

Run the tests with:

```bash
python -m unittest -v tests.py
```

## Basic workflow

1. Choose `1` to create a customer.
2. Note the generated customer ID, such as `C1001`.
3. Choose `3` to create a savings or current account for that customer.
4. Use the account number for deposits, withdrawals, transfers, and history.
5. Choose `10` for help or `11` to exit.

## Account rules

- Savings accounts must open with at least INR 100.00.
- Savings accounts must keep at least INR 100.00 after withdrawals.
- Current accounts can use up to INR 500.00 overdraft.
- Money amounts must be finite, positive, and have at most two decimal places.
- Opening balances may be zero for current accounts.
- Transfers to the same account are not allowed.

## Example session

```text
Choose an option: 1
Name: Asha Rao
Phone: 9876543210
Email: asha@example.com
C1001 - Asha Rao (9876543210, asha@example.com)

Choose an option: 3
Opening balance (0 allowed): 250.00
Customer ID: C1001
Type (savings/current): savings
Created 100001 | Savings | customer C1001 | INR 250.00. Owner: Asha Rao.
```

## Important limitation

This is an educational simulation. All data is stored in memory and is reset when the program exits. It does not provide real banking services, authentication, encryption, databases, file storage, networking, or online payments.
