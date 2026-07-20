"""Shared ingestion helpers: fetch -> normalize -> load -> validate.

Licensed payloads are fetched at load time, never committed. Loads are batched
MERGEs on suite-scoped IDs; validation asserts counts survive translation and
no dangling edges remain. Skeleton.
"""
