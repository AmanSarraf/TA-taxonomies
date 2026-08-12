"""Fixture normalize path without Neo4j."""

from ta_taxonomies.suites.esco.load import load_fixture_document, normalize_document


def test_fixture_normalize_shapes() -> None:
    doc = load_fixture_document()
    payload = normalize_document(doc)

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


def test_numeric_occupation_isco_code_resolves_to_uri_code_with_leading_zero() -> None:
    payload = normalize_document(
        {
            "isco_groups": [
                {
                    "conceptUri": "http://data.europa.eu/esco/isco/C0110",
                    "preferredLabel": "Commissioned armed forces officers",
                }
            ],
            "occupations": [
                {
                    "conceptUri": "http://data.europa.eu/esco/occupation/officer",
                    "preferredLabel": "armed forces officer",
                    "iscoGroup": 110.0,
                }
            ],
        }
    )

    assert payload["classified"] == [
        {
            "from_id": "esco:occupation:officer",
            "to_id": "esco:isco:0110",
        }
    ]
    assert payload["unmatched_classifications"] == []


def test_unmatched_occupation_isco_code_is_reported() -> None:
    payload = normalize_document(
        {
            "isco_groups": [],
            "occupations": [
                {
                    "conceptUri": "http://data.europa.eu/esco/occupation/unknown",
                    "preferredLabel": "unknown occupation",
                    "iscoGroup": 9999.0,
                }
            ],
        }
    )

    assert payload["classified"] == []
    assert payload["unmatched_classifications"] == [
        {
            "occupation_id": "esco:occupation:unknown",
            "isco_group": "9999",
        }
    ]
