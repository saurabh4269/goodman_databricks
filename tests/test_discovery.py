from pathlib import Path

from dpdp_kavach.discovery import DiscoveryEngine


def test_parse_sql_schema_extracts_columns() -> None:
    engine = DiscoveryEngine()
    elements = engine.parse_schema_file(Path("data/demo_schema.sql"))

    names = {(item.table_name, item.column_name) for item in elements}
    assert ("customers", "mobile_number") in names
    assert ("transactions", "upi_handle") in names
    assert len(elements) >= 10
