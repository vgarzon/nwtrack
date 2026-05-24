"""Tests for AssignInstitutions use case."""

import pytest
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.application.use_cases.admin_assign_institutions import AssignInstitutions
from nwtrack.bootstrap.container import Container
from nwtrack.domain.models import Account, Institution
from nwtrack.infra.config.settings import Settings


class MockAdminAssignInstitutionsPresenter:
    def __init__(
        self,
        account_choices: list[int | None],
        institution_choices: list[int | None],
        confirm_choices: list[bool],
    ) -> None:
        self.account_choices = list(account_choices)
        self.institution_choices = list(institution_choices)
        self.confirm_choices = list(confirm_choices)
        self.calls: list[str] = []
        self.assigned_pairs: list[tuple[str, str]] = []
        self.summary_count: int = -1

    def show_header(self) -> None:
        self.calls.append("show_header")

    def display_unassigned(self, accounts: list[Account]) -> None:
        self.calls.append("display_unassigned")

    def show_empty_state(self) -> None:
        self.calls.append("show_empty_state")

    def select_account(self, accounts: list[Account]) -> int | None:
        self.calls.append("select_account")
        if self.account_choices:
            return self.account_choices.pop(0)
        return None

    def select_institution(self, institutions: list[Institution]) -> int | None:
        self.calls.append("select_institution")
        if self.institution_choices:
            return self.institution_choices.pop(0)
        return None

    def show_no_institutions_error(self) -> None:
        self.calls.append("show_no_institutions_error")

    def confirm_assignment(self, account: Account, institution: Institution) -> bool:
        self.calls.append("confirm_assignment")
        if self.confirm_choices:
            return self.confirm_choices.pop(0)
        return False

    def show_assignment_success(
        self, account: Account, institution: Institution
    ) -> None:
        self.calls.append("show_assignment_success")
        self.assigned_pairs.append((account.name, institution.name))

    def show_session_summary(self, assigned_count: int) -> None:
        self.calls.append("show_session_summary")
        self.summary_count = assigned_count


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    from nwtrack.application.ports.schema import SchemaManager
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
    from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl

    return (
        base_container.register(
            SchemaManager,
            lambda c: SchemaManagerImpl(engine=c.resolve(SQLiteSessionManager).engine),
        )
        .register(
            DBAdminService,
            lambda c: DBAdminService(c.resolve(Settings), c.resolve(SchemaManager)),
        )
        .register(
            FetchService,
            lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
        )
    )


def _make_use_case(
    container: Container,
    account_choices: list[int | None],
    institution_choices: list[int | None],
    confirm_choices: list[bool],
) -> tuple[AssignInstitutions, MockAdminAssignInstitutionsPresenter]:
    presenter = MockAdminAssignInstitutionsPresenter(
        account_choices=account_choices,
        institution_choices=institution_choices,
        confirm_choices=confirm_choices,
    )
    uc = AssignInstitutions(
        uow=lambda: container.resolve(UnitOfWork),
        fetcher=container.resolve(FetchService),
        presenter=presenter,
    )
    return uc, presenter


def test_no_institutions_shows_error(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """When no institutions exist, show_no_institutions_error is called."""
    init_db_tables_w_entities(configured_container, sample_entities)
    uc, presenter = _make_use_case(
        configured_container,
        account_choices=[],
        institution_choices=[],
        confirm_choices=[],
    )

    result = uc.run()

    assert not result.success
    assert "show_no_institutions_error" in presenter.calls
    assert "show_header" in presenter.calls
    assert "select_account" not in presenter.calls


def test_no_unassigned_accounts_shows_empty_state(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """When all accounts already have institutions, show_empty_state is called."""
    init_db_tables_w_entities(configured_container, sample_entities)

    uow: UnitOfWork
    inst_id: int
    with configured_container.resolve(UnitOfWork) as uow:
        inst_id = uow.institutions.insert(Institution(name="Bank C", description=""))
        acct: Account
        for acct in uow.accounts.get_all():
            updated = Account(
                name=acct.name,
                description=acct.description,
                category_name=acct.category_name,
                currency_code=acct.currency_code,
                institution_id=inst_id,
                status=acct.status,
            )
            updated.id = acct.id
            uow.accounts.update(updated)

    uc, presenter = _make_use_case(
        configured_container,
        account_choices=[],
        institution_choices=[],
        confirm_choices=[],
    )

    result = uc.run()

    assert result.success
    assert "show_empty_state" in presenter.calls
    assert "select_account" not in presenter.calls
    assert presenter.summary_count == 0


def test_assign_one_institution_persists_and_reports_success(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """Assigning one institution saves institution_id to DB."""
    init_db_tables_w_entities(configured_container, sample_entities)

    uow: UnitOfWork
    inst_id: int
    first_account_id: int
    with configured_container.resolve(UnitOfWork) as uow:
        inst_id = uow.institutions.insert(Institution(name="Bank D", description=""))
        first_account_id = uow.accounts.get_all()[0].id

    uc, presenter = _make_use_case(
        configured_container,
        account_choices=[first_account_id, None],
        institution_choices=[inst_id],
        confirm_choices=[True],
    )

    result = uc.run()

    assert result.success
    assert result.data == 1
    assert "show_assignment_success" in presenter.calls
    assert presenter.summary_count == 1

    updated_account: Account | None
    uow2: UnitOfWork
    with configured_container.resolve(UnitOfWork) as uow2:
        updated_account = uow2.accounts.get_by_id(first_account_id)
    assert updated_account is not None
    assert updated_account.institution_id == inst_id


def test_user_cancels_after_one_assignment_persists_prior_work(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """Cancelling mid-session preserves assignments already made."""
    init_db_tables_w_entities(configured_container, sample_entities)

    uow: UnitOfWork
    inst_id: int
    first_id: int
    second_id: int
    with configured_container.resolve(UnitOfWork) as uow:
        inst_id = uow.institutions.insert(Institution(name="Bank E", description=""))
        all_accounts: list[Account] = uow.accounts.get_all()
        first_id = all_accounts[0].id
        second_id = all_accounts[1].id

    uc, presenter = _make_use_case(
        configured_container,
        account_choices=[first_id, None],
        institution_choices=[inst_id],
        confirm_choices=[True],
    )

    result = uc.run()

    assert result.success
    assert presenter.summary_count == 1

    uow2: UnitOfWork
    with configured_container.resolve(UnitOfWork) as uow2:
        assert uow2.accounts.get_by_id(first_id).institution_id == inst_id  # type: ignore[union-attr]
        assert uow2.accounts.get_by_id(second_id).institution_id is None  # type: ignore[union-attr]


def test_declined_confirmation_skips_assignment(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """When user declines confirmation, no assignment is saved."""
    init_db_tables_w_entities(configured_container, sample_entities)

    uow: UnitOfWork
    inst_id: int
    account_id: int
    with configured_container.resolve(UnitOfWork) as uow:
        inst_id = uow.institutions.insert(Institution(name="Bank F", description=""))
        account_id = uow.accounts.get_all()[0].id

    uc, presenter = _make_use_case(
        configured_container,
        account_choices=[account_id, None],
        institution_choices=[inst_id],
        confirm_choices=[False],
    )

    result = uc.run()

    assert result.success
    assert "show_assignment_success" not in presenter.calls
    assert presenter.summary_count == 0

    uow2: UnitOfWork
    with configured_container.resolve(UnitOfWork) as uow2:
        assert uow2.accounts.get_by_id(account_id).institution_id is None  # type: ignore[union-attr]
