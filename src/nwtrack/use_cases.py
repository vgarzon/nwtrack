"""
Use cases for updating account balances and generating reports.
"""

from pathlib import Path

from nwtrack.admin import DBAdminService
from nwtrack.config import Config
from nwtrack.container import Container
from nwtrack.models import Month
from nwtrack.services import (
    AccountService,
    InitDataService,
    ReportService,
    UpdateService,
)


class DBInitializerCSV:
    def __init__(self, container: Container) -> None:
        self._container = container
        self._config: Config = self._container.resolve(Config)
        self._data_svc: InitDataService = self._container.resolve(InitDataService)
        self._admin_svc: DBAdminService = self._container.resolve(DBAdminService)

    def run(self, file_paths: dict[str, str]) -> None:
        print(f"Database file path: {self._config.db_file_path}")
        print(f"DDL script path: {self._config.db_ddl_path}")
        print("Specified CSVfile paths:")
        for key, path in file_paths.items():
            print(f"  {key}: {path}")
        # TODO: Use RepoRegistry to specifi required keys
        required_keys = {
            "accounts",
            "balances",
            "categories",
            "currencies",
            "exchange_rates",
        }
        self._validate_file_path_keys(file_paths, required_keys)
        self._validate_file_paths(file_paths)
        print("WARNING: This script will DELETE and RE-CREATE the database.")
        confirmation = input("Type 'YES' to continue: ")
        if confirmation != "YES":
            print("Quitting.")
            return

        print("Initializing SQLite database.")
        self._admin_svc.init_database()
        self._data_svc.insert_data_from_csv(file_paths)
        print("Database initialization complete.")

    def _validate_file_path_keys(
        self, file_paths: dict[str, str], required_keys: set[str]
    ) -> None:
        print("Validating required file path keys.")
        missing_keys = required_keys - file_paths.keys()
        if missing_keys:
            raise KeyError(f"Missing required file paths for keys: {missing_keys}")

    def _validate_file_paths(self, file_paths: dict[str, str]) -> None:
        print("Validating file paths.")
        for key, path in file_paths.items():
            _path = Path(path)
            if not _path.is_file():
                raise FileNotFoundError(f"Path for '{key}' is not a file: {path}")


class BalanceUpdater:
    def __init__(self, container: Container) -> None:
        self._container = container
        self._account_svc: AccountService = self._container.resolve(AccountService)
        self._report_svc: ReportService = self._container.resolve(ReportService)
        self._update_svc: UpdateService = self._container.resolve(UpdateService)

    def run(self) -> None:
        self.print_active_accounts()
        month = self.input_month()
        if month is None:
            return
        self.update_balances_loop(month)
        print("Final active account balances:")
        self.print_balances(month)
        print("Net Worth:")
        self.print_net_worth(month)

    def input_month(self) -> Month | None:
        while True:
            response = input("Enter year and month as 'YYYY MM' or 'q' to quit: ")
            if response.lower().strip() == "q":
                return None
            try:
                _year, _month = map(int, response.split())
            except ValueError:
                print("Invalid input format. Please use 'YYYY MM'.")
                continue

            try:
                month = Month(year=_year, month=_month)

            except ValueError:
                print("Invalid month format. Please use YYYY-MM.")
                continue
            break
        return month

    def update_balances_loop(self, month: Month) -> None:
        while True:
            self.print_balances(month)
            res = input("Select account to update. Enter 'q' to quit: ")
            if res.lower() == "q":
                break
            try:
                account_id = int(res)
            except ValueError:
                print("Invalid input. Please enter a valid account ID or 'q' to quit. ")
                continue
            self.update_account_balance(account_id, month)

    def print_net_worth(self, month: Month) -> None:
        self._report_svc.print_net_worth(month)

    def update_account_balance(self, account_id: int, month: Month) -> None:
        accounts_map_id = self._report_svc.get_map_id_to_account()
        balance = self._report_svc.get_balance_for_account_id(month, account_id)
        current_balance = balance.amount if balance else 0

        while True:
            _account = accounts_map_id.get(account_id)
            assert _account is not None, f"Account id '{account_id}' not found"
            account_name = _account.name
            print(
                f"Balance amount for account {account_name} ({account_id}) on {month}: "
                f"{current_balance}"
            )
            new_amount_str = input("Enter new balance amount: ")
            try:
                new_amount = int(new_amount_str)
            except ValueError:
                print("Invalid amount. Please enter a valid integer amount.")
                continue
            break
        self._update_svc.update_balance(account_id, month, new_amount)

    def print_active_accounts(self):
        active_accounts = self._report_svc.get_accounts(active_only=True)
        print("Active accounts:")
        for account in active_accounts:
            _id, _name = account.id, account.name
            _category = self._account_svc.get_category_by_account_id(_id)
            _side = _category.side.value
            print(f"Account {_id:2}: {_name:20} {_category.name:16} ({_side})")
        print()

    def print_balances(self, month: Month):
        balances = self._report_svc.get_month_balances(month, active_only=True)
        account_map = self._report_svc.get_map_id_to_account()
        print("Balances for", month)
        for balance in balances:
            account_id = balance.account_id
            account_name = account_map[account_id].name
            account_category = self._account_svc.get_category_by_account_id(account_id)
            assert account_category is not None, (
                f"Category not found for account ID {account_id}"
            )
            account_side = account_category.side.value
            print(
                f"{account_id:2} {account_name:20} ({account_side:9}) "
                f"{balance.amount:10,}"
            )
        print()
