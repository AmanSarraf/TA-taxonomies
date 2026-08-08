"""ESCO suite package: EU occupations, skills, and related graph ops.

Use case: one place for the ESCO taxonomy in Talent Angels — load the graph
(``load`` module) and query it (``EscoSuite`` in tools). Public export is
``EscoSuite`` for TA-agents and scripts.

Domain notes: aligns to ISCO-08 (codes as strings, leading zeros); prefer
``description`` over mostly empty ``definition``; occ↔skill edges are
essential/optional (any numeric ranking is a declared TA policy, not source
data). See NOTES.md for Docker/Aura repro.
"""

from ta_taxonomies.suites.esco.tools import EscoSuite

__all__ = ["EscoSuite"]
