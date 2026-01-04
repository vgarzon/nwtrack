"""
Test reporting service methods.
"""

from nwtrack.compose import build_data_services_container
from nwtrack.container import Container
from nwtrack.services import ReportService
from tests.test_services import init_db_tables_w_entities


def test_get_all_categories(
    test_container: Container, test_entities: dict[str, list]
) -> None:
    """Test retrieving all categories."""
    container = build_data_services_container(test_container)
    init_db_tables_w_entities(container, test_entities)
    prn_svc: ReportService = container.resolve(ReportService)

    categories = prn_svc.get_all_categories()
    assert len(categories) == 4
    assert categories[0].name == "checking"
    assert categories[0].side.value == "asset"
    assert categories[3].name == "revolving_credit"
    assert categories[3].side.value == "liability"
