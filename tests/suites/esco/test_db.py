"""Unit tests for explicit Neo4j configuration."""

import pytest

from ta_taxonomies.suites.esco import db


def test_password_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db, "load_dotenv", lambda: None)
    monkeypatch.delenv("NEO4J_PASSWORD", raising=False)

    with pytest.raises(ValueError, match="NEO4J_PASSWORD is required"):
        db.neo4j_config_from_env()
