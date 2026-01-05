"""
Demo interactive account creation use case.
"""

from typing import Callable
from nwtrack.models import Category, Currency, Status, Month
from nwtrack.services import AccountService
from nwtrack.compose import build_base_sqlite_uow_container
from nwtrack.unitofwork import UnitOfWork


class AccountCreator:
    """Create account interactively."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        account_svc: AccountService,
    ) -> None:
        self._uow = uow
        self._account_svc = account_svc

    def run(self) -> None:
        self.print_active_accounts()
        data = self.collect_data()

        with self._uow() as uow:
            account = uow.accounts.hydrate(
                {
                    "name": data["account_name"],
                    "description": data["description"],
                    "category": data["category_name"],
                    "currency": data["currency_code"],
                    "status": data["status"],
                }
            )
            try:
                account_id = uow.accounts.insert(account)
            except ValueError as e:
                print("Error inserting account:", e)
                uow.rollback()
                return
            balance = uow.balances.hydrate(
                {
                    "account_id": account_id,
                    "month": data["initial_month"],
                    "amount": data["initial_amount"],
                }
            )
            try:
                balance_id = uow.balances.insert(balance)
            except ValueError as e:
                print("Error inserting balance:", e)
                uow.rollback()
                return

        check = self.validate_new_account(data, account_id, balance_id)
        if not check:
            raise ValueError("New account validation failed.")
            return

        print(
            f"Created account '{data['account_name']}' with id {account_id}, "
            f"initial balance of {data['initial_amount']}, and initial month "
            f"{data['initial_month']}."
        )
        self.print_all_accounts()

    def collect_data(self) -> dict[str, str | int | Month | Status]:
        """Collect account info from user input."""

        account_name = self._collect_account_name()
        description = self._collect_description()
        category_name = self._collect_category_name()
        currency_code = self._collect_currency_code()
        status = self._collect_status()
        initial_month = self._collect_initial_month()
        initial_balance = self._collect_initial_balance()

        return {
            "account_name": account_name,
            "description": description,
            "category_name": category_name,
            "currency_code": currency_code,
            "status": status,
            "initial_month": initial_month,
            "initial_amount": initial_balance,
        }

    def _collect_account_name(self) -> str:
        while True:
            name = input("Enter account name or 'q' to quit: ").strip()
            if name.lower() == "q":
                raise KeyboardInterrupt("Account creation cancelled by user.")
            if name:
                return name
            print("Account name cannot be empty.")

    def _collect_description(self) -> str:
        description = input("Enter optional description or 'q' to quit: ").strip()
        if description.lower() == "q":
            raise KeyboardInterrupt("Account creation cancelled by user.")
        return description

    def _collect_category_name(self) -> str:
        all_categories = self._get_all_categories()
        print("Available categories:")
        for k, category in enumerate(all_categories):
            print(f"{k}: {category.name} ({category.side.value})")

        while True:
            choice = input("Enter choice or 'q' to quit: ").strip()
            if choice.lower() == "q":
                raise KeyboardInterrupt("Account creation cancelled.")
            try:
                index = int(choice)
            except ValueError:
                print("Invalid input. Please enter a valid number.")

            if 0 <= index < len(all_categories):
                break
            else:
                print("Invalid index. Please try again.")

        return all_categories[index].name

    def _collect_currency_code(self) -> str:
        all_currencies = self._get_all_currencies()
        print("Available currencies:")
        for k, currency in enumerate(all_currencies):
            print(f"{k}: {currency.code} - {currency.description}")

        while True:
            choice = input("Enter choice or 'q' to quit: ").strip()
            if choice.lower() == "q":
                raise KeyboardInterrupt("Account creation cancelled.")
            try:
                index = int(choice)
            except ValueError:
                print("Invalid input. Please enter a valid number.")

            if 0 <= index < len(all_currencies):
                break
            else:
                print("Invalid index. Please try again.")

        return all_currencies[index].code

    def _collect_status(self) -> Status:
        status_options = [Status.ACTIVE, Status.INACTIVE]
        print("Available status:")
        for k, status in enumerate(status_options):
            print(f"{k}: {status.value}")

        while True:
            choice = input("Enter choice or 'q' to quit: ").strip()
            if choice.lower() == "q":
                raise KeyboardInterrupt("Account creation cancelled.")
            try:
                index = int(choice)
            except ValueError:
                print("Invalid input. Please enter a valid number.")

            if 0 <= index < len(status_options):
                break
            else:
                print("Invalid index. Please try again.")

        return status_options[index]

    def _collect_initial_balance(self) -> int:
        while True:
            amount_str = input("Enter initial balance amount or 'q' to quit: ").strip()
            if amount_str.lower() == "q":
                raise KeyboardInterrupt("Account creation cancelled.")
            try:
                amount = int(amount_str)
                break
            except ValueError:
                print("Invalid amount. Please enter a valid integer amount.")

        return amount

    def _collect_initial_month(self) -> str:
        while True:
            response = input(
                "Enter year and month as 'YYYY MM' or 'q' to quit: "
            ).strip()
            if response.lower().strip() == "q":
                raise KeyboardInterrupt("Account creation cancelled.")
            try:
                _year, _month = map(int, response.split())
            except ValueError:
                print("Invalid input format. Please use 'YYYY MM'.")
                continue
            try:
                month = Month(year=_year, month=_month)
            except ValueError:
                print("Invalid month format. Please use YYYY MM.")
                continue
            break
        return str(month)

    def _get_all_categories(self) -> list[Category]:
        """Get a list of all categories.

        Returns:
            list[Category]: List of Category objects.
        """
        with self._uow() as uow:
            categories = uow.categories.get_all()
        return categories

    def _get_all_currencies(self) -> list[Currency]:
        """Get a list of all currencies.

        Returns:
            list[Currency]: List of currency codes.
        """
        with self._uow() as uow:
            currencies = uow.currencies.get_all()
        return currencies

    def print_active_accounts(self):
        active_accounts = self._account_svc.get_all(active_only=True)
        print("Active accounts:")
        for account in active_accounts:
            _id, _name = account.id, account.name
            _category = self._account_svc.get_category_by_account_id(_id)
            _side = _category.side.value
            print(f"Account {_id:2}: {_name:20} {_category.name:16} ({_side})")
        print()

    def print_all_accounts(self):
        all_accounts = self._account_svc.get_all(active_only=False)
        print("All accounts:")
        for account in all_accounts:
            _id, _name = account.id, account.name
            _category = self._account_svc.get_category_by_account_id(_id)
            _side = _category.side.value
            print(f"Account {_id:2}: {_name:20} {_category.name:16} ({_side})")
        print()

    def validate_new_account(
        self, data: dict, account_id: int, balance_id: int
    ) -> bool:
        """Validate that the new account and balance were created correctly.

        Args:
            data (dict): The data used to create the account.
            account_id (int): The ID of the created account.
            balance_id (int): The ID of the created balance.

        Returns:
            bool: True if validation passes, False otherwise.
        """
        with self._uow() as uow:
            account = uow.accounts.get_by_id(account_id)
            if account is None:
                print("Validation failed: Account not found.")
                return False
            if account.name != data["account_name"]:
                print("Validation failed: Account name mismatch.")
                return False
            if account.description != data["description"]:
                print("Validation failed: Account description mismatch.")
                return False
            if account.category_name != data["category_name"]:
                print("Validation failed: Account category mismatch.")
                return False
            if account.currency_code != data["currency_code"]:
                print("Validation failed: Account currency mismatch.")
                return False
            if account.status != data["status"]:
                print("Validation failed: Account status mismatch.")
                return False

            balance = uow.balances.get_by_id(balance_id)
            if balance is None:
                print("Validation failed: Balance not found.")
                return False
            if balance.account_id != account_id:
                print("Validation failed: Balance account ID mismatch.")
                return False
            if str(balance.month) != str(data["initial_month"]):
                print("Validation failed: Balance month mismatch.")
                return False
            if balance.amount != data["initial_amount"]:
                print("Validation failed: Balance amount mismatch.")
                return False

        return True


def main() -> None:
    """Main function to run the account creator."""
    container = build_base_sqlite_uow_container()
    container.register(
        AccountService,
        lambda c: AccountService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        AccountCreator,
        lambda c: AccountCreator(
            uow=lambda: c.resolve(UnitOfWork),
            account_svc=c.resolve(AccountService),
        ),
    )
    account_creator: AccountCreator = container.resolve(AccountCreator)
    account_creator.run()


if __name__ == "__main__":
    main()
