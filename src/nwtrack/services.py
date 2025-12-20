"""
Service layer for managing user operations using unit of work pattern.
"""

from nwtrack.unitofwork import SQLiteUnitOfWork
from nwtrack.fileio import csv_file_to_list_dict
from nwtrack.models import (
    Account,
    Balance,
    Category,
    NetWorth,
    Side,
    Currency,
    ExchangeRate,
    Month,
    Status,
)


class InitDataService:
    """Initialize reference and sample data in the database."""

    def __init__(self, uow: SQLiteUnitOfWork) -> None:
        self._uow = uow

    def initialize_reference_data(
        self, currencies_path: str, categories_path: str
    ) -> None:
        """Initialize reference data in the database.

        Args:
            currencies_path (str): Path to currencies CSV file.
            categories_path (str): Path to categories CSV file.
        """
        print("Service: Initializing reference data.")
        currencies = csv_file_to_list_dict(currencies_path)
        categories = csv_file_to_list_dict(categories_path)

        currencies = [Currency(**c) for c in currencies]
        categories = [
            Category(name=at["name"], side=Side(at["side"])) for at in categories
        ]
        with self._uow() as uow:
            uow.currency.insert_many(currencies)
            uow.category.insert_many(categories)

    def insert_accounts(self, accounts: list[Account]) -> None:
        """Insert accounts into the database.

        Args:
            accounts_data (list[dict]): list of Account objects.
        """
        print("Service: Inserting sample accounts data.")
        with self._uow() as uow:
            uow.account.insert_many(accounts)

    def parse_account_data(self, accounts_data: list[dict]) -> list[Account]:
        """Parse account data from list of dicts to list of Account objects.

        Args:
            accounts_data (list[dict]): list of account data as dicts.

        Returns:
            list[Account]: list of Account objects.
        """
        with self._uow() as uow:
            currency_map = uow.currency.get_dict()
            category_map = uow.category.get_dict()
        accounts = []
        for row in accounts_data:
            currency = currency_map.get(row["currency"], None)
            if not currency:
                raise ValueError(
                    f"Currency code '{row['currency']}' not found in database."
                )
            category = category_map.get(row["category"], None)
            if not category:
                raise ValueError(
                    f"Category name '{row['category']}' not found in database."
                )
            account = Account(
                id=0,  # id will be set by the database
                name=row["name"],
                description=row["description"],
                category_name=category.name,
                currency_code=currency.code,
                status=Status(row["status"]),
            )
            accounts.append(account)
        return accounts

    def insert_balances(self, balances: list[Balance]) -> None:
        """Insert balances into the database.

        Args:
            balances (list[Balance]): list of Balance objects.
        """
        print("Service: Inserting sample balances data.")
        with self._uow() as uow:
            uow.balance.insert_many(balances)

    def parse_balance_data(self, balances_data: list[dict]) -> list[Balance]:
        """Parse balance data from list of dicts to list of Balance objects.

        Args:
            balances_data (list[dict]): list of balance data as dicts.

        Returns:
            list[Balance]: list of Balance objects.
        """
        skip_cols = ("date", "year", "month")
        with self._uow() as uow:
            account_map = uow.account.get_dict_name()
        balances = []
        for row in balances_data:
            for key in row:
                if key.lower() in skip_cols:
                    continue
                account = account_map.get(key, None)
                if not account:
                    raise ValueError(f"Account name '{key}' not found in accounts.")
                bal = Balance(
                    id=0,  # id will be set by the database
                    account_id=account.id,
                    month=Month(year=int(row["year"]), month=int(row["month"])),
                    amount=abs(int(row[key])) if row[key] else 0,
                )
                if bal.amount != 0:
                    balances.append(bal)
        return balances

    def insert_sample_data(self, accounts_path: str, balances_path: str) -> None:
        """Insert sample accounts and balances data.

        Args:
            accounts_path (str): Path to the accounts CSV file.
            balances_path (str): Path to the balances CSV file.

        File formats:
          - accounts.csv: name, description, category, currency, status
          - balances.csv: Date, year, month, <account_name_1>, <acct_name_2>, ...

        Notes:
          - Liabilities are assumed to be in negative amounts and will be stored as
          - Account names in the header must match those in the accounts.csv file.
            positive.
        """
        print("Service: Inserting sample data.")
        accounts_data = csv_file_to_list_dict(accounts_path)
        accounts = self.parse_account_data(accounts_data)
        self.insert_accounts(accounts)

        balances_data = csv_file_to_list_dict(balances_path)
        balances = self.parse_balance_data(balances_data)
        self.insert_balances(balances)

    def insert_exchange_rates(self, exchange_rates_path: str) -> None:
        """Insert exchange rate data from a CSV file.

        Args:
            exchange_rates_path (str): Path to the exchange rates CSV file.
        """
        print(f"Service: Inserting exchange rates from {exchange_rates_path}.")
        exchange_rates_data = csv_file_to_list_dict(exchange_rates_path)
        assert exchange_rates_data, "No exchange rates data found."

        # check that currency codes in the file exist in the database
        with self._uow() as uow:
            currency_codes = uow.currency.get_codes()
        skip_cols = ("date", "year", "month")
        row = exchange_rates_data[0]
        for key in row:
            if key.lower() in skip_cols:
                continue
            if key not in currency_codes:
                raise ValueError(f"Currency code '{key}' not found in database.")

        rates = []
        for row in exchange_rates_data:
            for key in row:
                if key.lower() in skip_cols:
                    continue
                if not row[key]:
                    continue
                rate = ExchangeRate(
                    currency_code=key,
                    month=Month(year=int(row["year"]), month=int(row["month"])),
                    rate=float(row[key]),
                )
                rates.append(rate)

        with self._uow() as uow:
            uow.exchange_rate.insert_many(rates)


class UpdateService:
    """Service layer to update balance and other data using unit of work pattern."""

    def __init__(self, uow: SQLiteUnitOfWork) -> None:
        self._uow = uow

    def update_balance(self, account_name: str, month: Month, new_amount: int) -> None:
        """Update the balance for a specific account on a given month.

        Args:
            account_name (str): Name of the account.
            month (Month): Month of the balance to update.
            new_ammount (int): New balance amount.
        """
        with self._uow() as uow:
            account_id = uow.account.get_id(account_name)
        if not account_id:
            raise ValueError(f"Account name '{account_name}' not found.")

        with self._uow() as uow:
            uow.balance.update(
                account_id=account_id, month=month, new_amount=new_amount
            )

    def roll_balances_forward(self, month: Month) -> None:
        """Copy all active account balances from one month to the next.

        Args:
            month (Month): Month of the source month.
        """
        # check that month is valid
        with self._uow() as uow:
            if not uow.balance.check_month(month):
                raise ValueError("No balances found for month.")
        next_month = month.increment()
        print(f"Service: Copying balances from {month} to {next_month}.")
        with self._uow() as uow:
            uow.balance.roll_forward(month)


class ReportService:
    """Printing and reporting service using unit of work pattern."""

    def __init__(self, uow: SQLiteUnitOfWork) -> None:
        self._uow = uow

    def get_accounts(self, active_only: bool = True) -> list[Account]:
        """Get a list of all active accounts.

        Args:
            active_only (bool): Whether to include only active accounts.

        Returns:
            list[Account]: List of active Account objects.
        """
        if active_only:
            with self._uow() as uow:
                accounts = uow.account.get_active()
        else:
            with self._uow() as uow:
                accounts = uow.account.get_all()
        return accounts

    def print_accounts(self, active: bool = True) -> None:
        """Print a table of all active accounts.

        Args:
            active (bool): Whether to include only active accounts.
        """
        accounts = self.get_accounts(active=active)
        print("Accounts:")
        print("id, name, category, status")
        for account in accounts:
            print(account.id, account.name, account.category_name, account.status)

    def get_balance(self, month: Month, account_name: str) -> Balance:
        """Get balance for an account on a specific month.

        Args:
            month (Month): Month object
            account_name (str): Name of the account

        Return:
            Balance: Balance object for the specified account and month.
        """
        with self._uow() as uow:
            balance = uow.balance.get(month, account_name)
        return balance

    def get_month_balances(
        self, month: Month, active_only: bool = True
    ) -> list[Balance]:
        """Get balance all accounts on a specific month.

        Args:
            month (Month): Month object
            active_only (bool): Whether to include only active accounts

        Return:
            list[Balance]: List of Balance object for the specified account and month.
        """
        with self._uow() as uow:
            balances = uow.balance.get_month(month, active_only)
        return balances

    def print_balance(self, month: Month, account_name: str) -> None:
        """Print account balance for a specific month.

        Args:
            month (Month): Month object
            account_name (str): Name of the account
        """
        bal = self.get_balance(month, account_name)
        print("Balance for", account_name, "on", str(bal.month), "=", bal.amount)

    def print_month_balances(self, month: Month, active_only: bool = True) -> None:
        """Print account balances on a specific month.

        Args:
            month (Month): Month object
            active_only (bool): Whether to include only active accounts
        """
        balances = self.get_month_balances(month, active_only)
        accounts = self.get_accounts(active_only)
        account_map = {acc.id: acc for acc in accounts}
        print("id, account_id, month, amount")
        for bal in balances:
            account_name = account_map[bal.account_id].name
            print(bal.id, account_name, str(bal.month), bal.amount)

    def get_net_worth(self, month: Month) -> NetWorth:
        """Get net worth for a specific month.

        Args:
            month (Month): Month object

        Returns:
            NetWorth: NetWorth object for the specified month.
        """
        with self._uow() as uow:
            nw = uow.net_worth.get(month)
        return nw

    def get_net_worth_history(self) -> list[NetWorth]:
        """Get net worth history.

        Returns:
            list[NetWorth]: List of net worth records.
        """
        with self._uow() as uow:
            nw_hist = uow.net_worth.history()
        return nw_hist

    def print_net_worth(self, month: Month, currency_code: str = "USD") -> None:
        """Print net worth on a specific month.

        Args:
            month (Month): Month object
            currency (str): Currency code (default: "USD")

        Returns:
            None
        """
        with self._uow() as uow:
            nw = uow.net_worth.get(month, currency_code)
        if not nw:
            raise ValueError(f"No net worth data found for {month} in {currency_code}")
        print(
            f"Month: {month}, Currency: {currency_code}, Assets: {nw.assets}, "
            f"Liabilities: {nw.liabilities}, Net Worth: {nw.net_worth}"
        )

    def print_net_worth_history(self) -> None:
        """Print net worth history."""
        nw_hist = self.get_net_worth_history()
        print("month, assets, liabilities, net_worth")
        for nw in nw_hist:
            print(nw.month, nw.assets, nw.liabilities, nw.net_worth)

    def get_exchange_rate(
        self, month: Month, currency_code: str
    ) -> ExchangeRate | None:
        """Get exchange rate for given currency and month.

        Args:
            month (Month): Month objectk
            currency_code (str): Currency code

        Returns:
            ExchangeRate | None
        """
        with self._uow() as uow:
            all_currency_codes = uow.currency.get_codes()
        if currency_code not in all_currency_codes:
            raise ValueError(f"Currency '{currency_code}' not found in database.")
        with self._uow() as uow:
            rate = uow.exchange_rate.get(month, currency_code)
        return rate

    def get_exchange_rate_history(self, currency_code: str) -> list[ExchangeRate]:
        """Get exchange rate history for given currency.

        Args:
            currency_code (str): Currency code

        Returns:
            list[ExchangeRate]: List of ExchangeRate objects
        """
        with self._uow() as uow:
            all_currency_codes = uow.currency.get_codes()
        if currency_code not in all_currency_codes:
            raise ValueError(f"Currency '{currency_code}' not found in database.")
        with self._uow() as uow:
            rates = uow.exchange_rate.get_currency(currency_code)
        return rates

    def get_month_exchange_rates(self, month: Month) -> list[ExchangeRate]:
        """Get exchange rates for all currencies on a specific month.

        Args:
            month (Month): Month object

        Returns:
            list[ExchangeRate]: List of ExchangeRate objects
        """
        with self._uow() as uow:
            rates = uow.exchange_rate.get_month(month)
        return rates

    def print_exchange_rate(self, month: Month, currency_code: str) -> None:
        """Print exchange rates for a specific currency and month

        Args:
            month (Month): Month object
            currency_code (str): Currency code
        """
        rate = self.get_exchange_rate(month, currency_code)
        if rate:
            print(f"Exchange rate {currency_code} to USD on {month}: {rate.rate}")
        else:
            print(f"No exchange rate found for {currency_code} on {str(month)}.")

    def print_exchange_rate_history(self, currency_code: str) -> None:
        """Print exchange rate history.

        Args:
            currency (str): Currency code
        """
        rates = self.get_exchange_rate_history(currency_code)
        print("currency, month, rate")
        for r in rates:
            print(r.currency_code, str(r.month), r.rate)
