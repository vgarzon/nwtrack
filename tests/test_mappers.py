"""
Test record to entity mappers.
"""

from nwtrack.mappers import (
    Mapper,
    AccountMapper,
    CategoryMapper,
    CurrencyMapper,
    BalanceMapper,
    ExchangeRateMapper,
    NetWorthMapper,
)

from nwtrack.models import (
    Currency,
    Category,
    Account,
    Balance,
    ExchangeRate,
    NetWorth,
    Month,
    Status,
    Side,
)


def test_currency_mapper() -> None:
    mapper: Mapper = CurrencyMapper()
    record = {"code": "USD", "description": "US Dollar"}
    entity = mapper.to_entity(record)
    assert isinstance(entity, Currency)
    assert entity.code == "USD"
    assert entity.description == "US Dollar"
    record_converted = mapper.to_record(entity)
    assert record_converted == record


def test_category_mapper() -> None:
    mapper: Mapper = CategoryMapper()
    record = {"name": "Cash", "side": "asset"}
    entity = mapper.to_entity(record)
    assert isinstance(entity, Category)
    assert entity.name == "Cash"
    assert isinstance(entity.side, Side)
    assert str(entity.side) == "asset"
    record_converted = mapper.to_record(entity)
    assert record_converted == record


def test_account_mapper() -> None:
    mapper: Mapper = AccountMapper()
    record = {
        "id": 1,
        "name": "Checking",
        "description": "Main checking account",
        "category": "Cash",
        "currency": "USD",
        "status": "active",
    }
    entity = mapper.to_entity(record)
    assert isinstance(entity, Account)
    assert entity.id == 1
    assert entity.name == "Checking"
    assert entity.description == "Main checking account"
    assert entity.category_name == "Cash"
    assert entity.currency_code == "USD"
    assert isinstance(entity.status, Status)
    assert str(entity.status) == "active"
    record_converted = mapper.to_record(entity)
    assert record_converted == record


def test_balance_mapper() -> None:
    mapper: Mapper = BalanceMapper()
    record = {
        "id": 1,
        "account_id": 1,
        "month": "2023-05",
        "amount": 10000,
    }
    entity = mapper.to_entity(record)
    assert isinstance(entity, Balance)
    assert entity.id == 1
    assert entity.account_id == 1
    assert isinstance(entity.month, Month)
    assert entity.month.year == 2023
    assert entity.month.month == 5
    assert entity.amount == 10_000
    record_converted = mapper.to_record(entity)
    assert record_converted == record


def test_exchange_rate_mapper() -> None:
    mapper: Mapper = ExchangeRateMapper()
    record = {
        "currency": "EUR",
        "month": "2023-05",
        "rate": 1.1,
    }
    entity = mapper.to_entity(record)
    assert isinstance(entity, ExchangeRate)
    assert entity.currency_code == "EUR"
    assert isinstance(entity.month, Month)
    assert entity.month.year == 2023
    assert entity.month.month == 5
    assert entity.rate == 1.1
    record_converted = mapper.to_record(entity)
    assert record_converted == record


def test_net_worth_mapper() -> None:
    mapper: Mapper = NetWorthMapper()
    record = {
        "month": "2023-05",
        "total_assets": 500,
        "total_liabilities": 200,
        "net_worth": 300,
    }
    entity = mapper.to_entity(record)
    assert isinstance(entity, NetWorth)
    assert isinstance(entity.month, Month)
    assert entity.month.year == 2023
    assert entity.month.month == 5
    assert entity.assets == 500
    assert entity.liabilities == 200
    assert entity.net_worth == 300
    record_converted = mapper.to_record(entity)
    assert record_converted == record
