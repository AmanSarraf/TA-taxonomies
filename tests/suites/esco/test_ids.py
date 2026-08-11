"""Unit tests for ESCO identity helpers (no Neo4j)."""

from ta_taxonomies.suites.esco.ids import (
    code_to_str,
    isco_code_from_uri,
    split_alt_labels,
    suite_id_from_uri,
)


def test_isco_leading_zeros() -> None:
    assert isco_code_from_uri("http://data.europa.eu/esco/isco/C0110") == "0110"
    assert isco_code_from_uri("http://data.europa.eu/esco/isco/C01") == "01"
    assert isco_code_from_uri("http://data.europa.eu/esco/isco/C1") == "1"


def test_suite_id_from_uri() -> None:
    assert (
        suite_id_from_uri(
            "http://data.europa.eu/esco/occupation/f2b15a0e-e65a-438a-affb-29b9d50b77d1"
        )
        == "esco:occupation:f2b15a0e-e65a-438a-affb-29b9d50b77d1"
    )
    assert suite_id_from_uri("http://data.europa.eu/esco/isco/C2512") == "esco:isco:2512"
    assert suite_id_from_uri("http://data.europa.eu/esco/isced-f/0613") == "esco:isced-f:0613"


def test_code_to_str_float() -> None:
    assert code_to_str(2512.0) == "2512"
    assert code_to_str(8121.4) == "8121.4"
    assert code_to_str("2654.1.7") == "2654.1.7"


def test_split_alt_labels() -> None:
    assert split_alt_labels("a\nb\nc") == ["a", "b", "c"]
    assert split_alt_labels("a | b | c") == ["a", "b", "c"]
    assert split_alt_labels(None) == []
