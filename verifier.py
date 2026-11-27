"""Entry verification for Crossbones.

Checks every placed Entry against the extracted symbol set, the grid
contents, any available clues, and crossing-letter consistency.

Valid ``check`` values for a ``Failure``:
    "symbol"            — answer not in the extracted symbol set
    "grid-word"         — grid letters do not spell the answer
    "clue-containment"  — clue text contains the answer (case-insensitive)
    "crossing"          — two entries disagree on a shared cell's letter
"""

import collections

from placer import Entry, Grid  # noqa: F401 — re-exported for downstream use

# ---------------------------------------------------------------------------
# Failure record
# ---------------------------------------------------------------------------

Failure = collections.namedtuple("Failure", "entry check detail")
"""A single verification failure.

Fields:
    entry  — the Entry object that did not pass a check
    check  — which check failed: "symbol", "grid-word",
              "clue-containment", or "crossing"
    detail — human-readable description of what went wrong
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def verify_grid(grid, entries, symbols, clues):
    """Verify every entry in *entries* against the grid and symbol set.

    Args:
        grid:    Sparse grid dict ``{(row, col): letter}`` produced by the
                 placer.
        entries: List of ``Entry`` objects to verify.
        symbols: Either a set/collection of valid answer strings, or a dict
                 keyed by answer string whose values are dicts with keys
                 ``answer``, ``name``, ``kind``, ``file``, ``line``, ``doc``
                 (the rows returned by ``extract_symbols``).  Both forms
                 support membership testing via ``in``.
        clues:   Dict mapping answer strings to clue text (from
                 ``clues_cache.json``), or ``{}``.

    Returns:
        A list of ``Failure`` namedtuples — one per failed check per entry.
        An empty list means every entry passed all applicable checks.
        An entry can contribute multiple failures (one per check that fails).

    Clue resolution (Requirement 4.3 / 4.7):
        1. Use ``clues.get(entry.answer)`` if non-empty.
        2. If no cached clue and *symbols* is a dict, fall back to the
           ``"doc"`` field of the matching symbol row (if non-empty).
        3. If still no clue, skip the clue-containment check entirely.
    """
    # Build a fast membership set regardless of whether symbols is a set or
    # a dict keyed by answer (Requirement 4.5 / 4.6).
    symbol_set = set(symbols)

    failures = []

    for entry in entries:
        # Check 1 — symbol (Requirement 4.1)
        # Fail if the answer is not in the extracted symbol set.
        if entry.answer not in symbol_set:
            failures.append(
                Failure(entry, "symbol", f"{entry.answer!r} not in symbol set")
            )

        # Check 2 — grid-word (Requirement 4.2)
        # Read the entry's cells from the grid and compare to the answer.
        dr, dc = (0, 1) if entry.direction == "across" else (1, 0)
        grid_word = "".join(
            grid.get((entry.row + dr * i, entry.col + dc * i), "")
            for i in range(len(entry.answer))
        )
        if grid_word != entry.answer:
            failures.append(
                Failure(
                    entry,
                    "grid-word",
                    f"expected {entry.answer!r}, got {grid_word!r}",
                )
            )

        # Check 3 — clue-containment (Requirement 4.3)
        # Resolve clue: prefer clues_cache dict, then fall back to doc string.
        clue = clues.get(entry.answer)
        if not clue and isinstance(symbols, dict):
            row = symbols.get(entry.answer)
            if row and row.get("doc"):
                clue = row["doc"]
        if clue:  # skip entirely when no clue is available (Requirement 4.7)
            if entry.answer.lower() in clue.lower():
                failures.append(
                    Failure(
                        entry,
                        "clue-containment",
                        f"clue contains answer {entry.answer!r}",
                    )
                )

        # Check 4 — crossing (Requirement 4.4)
        # For every cell of this entry, look for another entry that also
        # covers that cell and ensure both entries agree on the letter.
        dr, dc = (0, 1) if entry.direction == "across" else (1, 0)
        for i in range(len(entry.answer)):
            r = entry.row + dr * i
            c = entry.col + dc * i
            for other in entries:
                if other is entry:
                    continue
                # Determine whether *other* covers cell (r, c).
                if other.direction == "across":
                    if other.row != r:
                        continue
                    if not (other.col <= c < other.col + len(other.answer)):
                        continue
                    offset = c - other.col
                else:  # "down"
                    if other.col != c:
                        continue
                    if not (other.row <= r < other.row + len(other.answer)):
                        continue
                    offset = r - other.row
                required = other.answer[offset]
                if entry.answer[i] != required:
                    failures.append(
                        Failure(
                            entry,
                            "crossing",
                            f"crossing conflict at ({r},{c}): "
                            f"{entry.answer[i]!r} vs {required!r}",
                        )
                    )

    return failures
