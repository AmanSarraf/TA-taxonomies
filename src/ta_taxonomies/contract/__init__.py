"""The suite contract: the typed tool surface every suite implements.

    search_nodes(text, kind?)                -> candidates + confidence
    get_neighbors(node_id, rel_types?)       -> nodes + edges
    enumerate_paths(from_id, to_id, limits)  -> depth-capped, cycle-free paths
    score_paths(paths, policy)               -> ranked under a named policy

This package is the ONLY surface TA-agents may import. Typed I/O (Pydantic
v2); node IDs are suite-scoped; every node carries source + source_id;
evidence is a pointer, not a payload. Skeleton.
"""
