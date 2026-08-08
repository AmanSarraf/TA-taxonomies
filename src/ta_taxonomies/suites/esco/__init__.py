"""ESCO suite (EU occupations, skills, qualifications).

Notes from the team's Sprint 1 slice: aligns to ISCO-08 (keep codes as
strings — leading zeros); `description` is populated, `definition` mostly
isn't; edges are structurally binary (essential/optional — any weighting is
our declared policy, not source data).
"""

from ta_taxonomies.suites.esco.tools import EscoSuite

__all__ = ["EscoSuite"]
