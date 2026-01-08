"""
Print network summary by category
"""

from typing import Callable

from nwtrack.domain.models import Account, Balance, Category
from nwtrack.domain.value_objects import Month
from nwtrack.application.ports.uow import UnitOfWork


class SummaryService:
    """Print net worth summary by category."""

    def __init__(self, uow: Callable[[], UnitOfWork]) -> None:
        self._uow = uow

    def run(self) -> None:
        self.print_active_accounts()
        self.print_recent_months()
        month = self.input_month()
        if month is None:
            return
        if month not in [m for m, _ in self._get_balance_count_per_month()]:
            print(f"No balance data found for {month}. Exiting.")
            return

        print("Net Worth:")
        self.print_net_worth(month)

    def print_recent_months(self) -> None:
        balance_counts = self._get_balance_count_per_month()
        balance_counts.sort(key=lambda x: x[0], reverse=True)
        print("Recent month balance counts:")
        for month, count in balance_counts[:3]:
            print(f" {month}: {count} balances")
        print()

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
            with self._uow() as uow:
                if not uow.balances.check_month(month):
                    print(f"No balance data found for {month}. Please try again.")
                    continue
            break
        return month

    def print_active_accounts(self):
        active_accounts = self._get_active_accounts()
        print("Active accounts:")
        for account in active_accounts:
            _id, _name = account.id, account.name
            _category = self._get_category_by_account_id(_id)
            _side = _category.side.value
            print(f"Account {_id:2}: {_name:20} {_category.name:16} ({_side})")
        print()

    def print_balances(self, month: Month):
        balances = self._get_month_balances(month, active_only=True)
        account_map = self._get_map_id_to_account()
        print("Balances for", month)
        for balance in balances:
            account_id = balance.account_id
            account_name = account_map[account_id].name
            account_category = self._get_category_by_account_id(account_id)
            assert account_category is not None, (
                f"Category not found for account ID {account_id}"
            )
            account_side = account_category.side.value
            print(
                f"{account_id:2} {account_name:20} ({account_side:9}) "
                f"{balance.amount:10,}"
            )
        print()

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
            f"Month: {month} Currency: {currency_code} Assets: {nw.assets:,} "
            f"Liabilities: {nw.liabilities:,} Net Worth: {nw.net_worth:,}"
        )

    def _get_category_by_account_id(self, account_id: int) -> Category | None:
        """Get category side for a given account ID.

        Args:
            account_id (int): Account ID

        Returns:
            Category | None: Category instance if found, else None.
        """
        with self._uow() as uow:
            account = uow.accounts.get_by_id(account_id)
        if not account:
            return None
        with self._uow() as uow:
            category = uow.categories.get(account.category_name)
        return category

    def _get_map_id_to_account(self) -> dict[int, Account]:
        """Get a map of account id to Account objects.

        Returns:
            dict[int, Account]: Map of account id to Account objects.
        """
        with self._uow() as uow:
            accounts = uow.accounts.get_all()
        return {acc.id: acc for acc in accounts}

    def _get_balance_count_per_month(self) -> list[tuple[Month, int]]:
        """Get count of balance entries per month.

        Returns:
            list[tuple[Month, int]]: list of tuples Month count of balance entries.
        """
        with self._uow() as uow:
            counts = uow.balances.count_per_month()
        return counts

    def _get_active_accounts(self) -> list[Account]:
        """Get list of active accounts.

        Returns:
            list[Account]: List of active Account objects.
        """
        with self._uow() as uow:
            accounts = uow.accounts.get_active()
        return accounts

    def _get_balance_for_account_id(self, month: Month, account_id: int) -> Balance:
        """Get balance for an account on a specific month.

        Args:
            month (Month): Month object
            account_id (int): Account id

        Return:
            Balance: Balance object for the specified account and month.
        """
        with self._uow() as uow:
            balance = uow.balances.get_by_account_id(month, account_id)
        return balance

    def _get_month_balances(
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
            balances = uow.balances.get_month(month, active_only)
        return balances

    def update_balance(self, account_id: int, month: Month, new_amount: int) -> None:
        """Update the balance for a specific account on a given month.

        Args:
            account_id (int): ID of the account.
            month (Month): Month of the balance to update.
            new_ammount (int): New balance amount.
        """
        with self._uow() as uow:
            uow.balances.update(
                account_id=account_id, month=month, new_amount=new_amount
            )


def main() -> None:
    from nwtrack.bootstrap.composition import build_base_sqlite_uow_container

    container = build_base_sqlite_uow_container()
    container.register(
        SummaryService,
        lambda c: SummaryService(uow=lambda: c.resolve(UnitOfWork)),
    )
    service: SummaryService = container.resolve(SummaryService)
    service.run()


if __name__ == "__main__":
    main()
