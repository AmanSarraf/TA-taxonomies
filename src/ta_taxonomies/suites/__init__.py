"""One package per taxonomy suite. Suites never import each other.

Each suite implements the contract in `ta_taxonomies.contract` and owns its
loader (fetch -> normalize -> load -> validate), schema mapping to the
canonical vocabulary, and tools. One mentee owns each suite.
"""
