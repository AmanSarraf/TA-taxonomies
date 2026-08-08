"""ESCO identity helpers: concept URIs → suite-scoped ids and clean codes.

Use case: during load (and anywhere we touch source rows), turn messy ESCO
values into stable graph keys — e.g. occupation URI → ``esco:occupation:<uuid>``,
ISCO codes as strings with leading zeros preserved from the URI.

Why it exists: Excel often types codes as floats; architecture requires
suite-scoped string ids and string codes. Also splits multi-value altLabels
for search. Pure functions — no Neo4j access.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import unquote

from ta_taxonomies.suites.esco.config import SOURCE

_ISCO_URI = re.compile(r"/isco/C(\d+)\s*$", re.I)
_ESCO_TAIL = re.compile(r"https?://data\.europa\.eu/esco/([^?#]+)$", re.I)


def code_to_str(value: Any) -> str | None:
    """Normalize openpyxl/float/str codes to a stable string (no leading-zero loss).

    Prefer deriving ISCO codes from the concept URI when available.
    For numeric floats like 2512.0 → "2512"; keep hierarchical "2512.4" as-is.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        # preserve hierarchical-looking floats carefully (8121.4 → "8121.4")
        text = f"{value:.10f}".rstrip("0").rstrip(".")
        return text
    text = str(value).strip()
    return text or None


def isco_code_from_uri(uri: str) -> str | None:
    """Extract ISCO code string from concept URI (preserves leading zeros)."""
    m = _ISCO_URI.search(uri or "")
    return m.group(1) if m else None


def suite_id_from_uri(uri: str) -> str:
    """Map an ESCO concept URI to a suite-scoped id.

    Examples:
      http://data.europa.eu/esco/occupation/<uuid> → esco:occupation:<uuid>
      http://data.europa.eu/esco/skill/<uuid>      → esco:skill:<uuid>
      http://data.europa.eu/esco/isco/C0110        → esco:isco:0110
      http://data.europa.eu/esco/isced-f/00        → esco:isced-f:00
    """
    if not uri:
        raise ValueError("empty URI")
    uri = str(uri).strip()
    isco = isco_code_from_uri(uri)
    if isco is not None:
        return f"{SOURCE}:isco:{isco}"
    m = _ESCO_TAIL.search(uri)
    if m:
        path = unquote(m.group(1)).strip("/")
        return f"{SOURCE}:{path.replace('/', ':')}"
    # fallback: last path segment
    tail = uri.rstrip("/").rsplit("/", 1)[-1]
    return f"{SOURCE}:{tail}"


def split_alt_labels(raw: Any) -> list[str]:
    """Split ESCO altLabels (newline or pipe separated) into a clean list."""
    if raw is None:
        return []
    text = str(raw).strip()
    if not text:
        return []
    parts = re.split(r"[\n|]+", text)
    return [p.strip() for p in parts if p.strip()]
