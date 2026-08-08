"""Fixture normalize path without Neo4j."""

from ta_taxonomies.suites.esco.load import load_fixture_document, normalize_fixture


def test_fixture_normalize_shapes() -> None:
    doc = load_fixture_document()
    payload = normalize_fixture(doc)

    assert len(payload["occupations"]) >= 4
    assert len(payload["skills"]) >= 10
    assert len(payload["has_skill"]) >= 10
    assert len(payload["isco_groups"]) >= 1

    occ = next(o for o in payload["occupations"] if o["pref_label"] == "software developer")
    assert occ["id"].startswith("esco:occupation:")
    assert occ["source"] == "esco"
    assert occ["source_id"].startswith("http://data.europa.eu/esco/occupation/")
    assert isinstance(occ["alt_labels"], list)

    for g in payload["isco_groups"]:
        assert g["id"].startswith("esco:isco:")
        # codes are strings (leading zeros preserved when present in URI)
        assert g["code"] is None or isinstance(g["code"], str)

    for edge in payload["has_skill"]:
        assert edge["relation_type"] in {"essential", "optional"}
        assert edge["from_id"].startswith("esco:occupation:")
        assert edge["to_id"].startswith("esco:skill:")
