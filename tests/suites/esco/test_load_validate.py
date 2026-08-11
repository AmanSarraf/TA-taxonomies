"""Load + validate ESCO fixture in Neo4j (skipped if DB down)."""

from __future__ import annotations

import pytest
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from ta_taxonomies.suites.esco.db import neo4j_driver, verify_connectivity
from ta_taxonomies.suites.esco.load import run_load


def _neo4j_available() -> bool:
    try:
        with neo4j_driver() as (driver, _db):
            verify_connectivity(driver)
        return True
    except (ServiceUnavailable, Neo4jError, OSError):
        return False


pytestmark = pytest.mark.skipif(
    not _neo4j_available(),
    reason="Neo4j not available (start with: docker compose up -d)",
)


def test_fixture_load_validates() -> None:
    counts = run_load(mode="fixture", wipe=True)
    assert counts["occupations"] >= 4
    assert counts["skills"] >= 10
    assert counts["has_skill"] >= 10
    assert counts["isco_groups"] >= 1
