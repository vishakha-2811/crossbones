"""Sparse crossword grid and entry model for Crossbones.

Grid is a sparse dict keyed by (row, col); a cell is empty iff the
key is absent. Bounding box is computed only at render time.
"""

import random
from dataclasses import dataclass

# Sparse grid: (row, col) -> single uppercase letter. Absent key = empty cell.
Grid = dict[tuple[int, int], str]

DIRECTIONS = ("across", "down")


@dataclass
class Entry:
    """A placed answer in the grid."""

    answer: str      # uppercase word, e.g. "PARSECONFIG"
    name: str        # original symbol name, e.g. "parse_config"
    kind: str        # "function" | "class" | "file"
    file: str        # repo-relative path
    line: int
    direction: str   # "across" | "down"
    row: int
    col: int

    @property
    def length(self) -> int:
        return len(self.answer)


def causes_collision(grid: Grid, word: str, row: int, col: int, direction: str) -> bool:
    """Return True if any cell the new word would occupy holds a different letter.

    A cell that is empty (absent from the grid) is never a collision.
    A cell that holds the same letter is NOT a collision (valid intersection).

    Args:
        grid:      Sparse grid dict, (row, col) -> uppercase letter.
        word:      Uppercase answer to place.
        row:       Row of the first letter.
        col:       Column of the first letter.
        direction: "across" (increment col) or "down" (increment row).
    """
    dr, dc = (0, 1) if direction == "across" else (1, 0)
    for i, letter in enumerate(word):
        existing = grid.get((row + dr * i, col + dc * i))
        if existing is not None and existing != letter:
            return True
    return False


def causes_adjacency(
    grid: Grid,
    word: str,
    row: int,
    col: int,
    direction: str,
    intersection_cell: tuple[int, int] | None,
) -> bool:
    """Return True if placing *word* would create illegal adjacency.

    Two rules are enforced:

    1. **Side rule** – for every cell of the new word *except* the
       intersection cell, the two cells perpendicular to the word's
       direction must be empty in the grid.  This prevents two parallel
       words from running side-by-side and touching.

    2. **Head/tail rule** – the cell immediately before the word's start
       and the cell immediately after its end (both along the word's own
       direction) must be empty.  This prevents the new word from
       abutting another word along the same axis and forming an
       unintended longer word.

    The intersection cell itself is exempt from rule 1; it is the
    deliberate crossing point between two perpendicular entries.

    Args:
        grid:             Sparse grid dict, (row, col) -> uppercase letter.
        word:             Uppercase answer to place.
        row:              Row of the first letter.
        col:              Column of the first letter.
        direction:        "across" (increment col) or "down" (increment row).
        intersection_cell: (row, col) of the shared crossing cell, or None
                          when placing the very first word.

    Returns:
        True if any adjacency rule is violated; False otherwise.
    """
    dr, dc = (0, 1) if direction == "across" else (1, 0)

    # Perpendicular deltas (the "side" direction).
    # For "across" words, sides are above/below (row ±1, same col).
    # For "down" words, sides are left/right (same row, col ±1).
    if direction == "across":
        pr, pc = 1, 0   # perpendicular step
    else:
        pr, pc = 0, 1

    # Rule 1: side cells for each letter position except the intersection.
    for i in range(len(word)):
        cell = (row + dr * i, col + dc * i)
        if cell == intersection_cell:
            continue  # exempt — this is exactly where the two entries cross
        # Check both perpendicular neighbours.
        if grid.get((cell[0] - pr, cell[1] - pc)) is not None:
            return True
        if grid.get((cell[0] + pr, cell[1] + pc)) is not None:
            return True

    # Rule 2: head cell (immediately before the start) and
    #          tail cell (immediately after the end).
    head = (row - dr, col - dc)
    tail = (row + dr * len(word), col + dc * len(word))
    if grid.get(head) is not None:
        return True
    if grid.get(tail) is not None:
        return True

    return False


def can_place(
    grid: Grid,
    entries: list,
    word: str,
    row: int,
    col: int,
    direction: str,
) -> bool:
    """Return True iff the word can be legally placed at (row, col, direction).

    A placement is legal when BOTH conditions hold:
    - ``causes_collision`` returns False (no cell conflict with existing letters)
    - ``causes_adjacency`` returns False (no illegal side-touching or head/tail abutment)

    The ``intersection_cell`` passed to ``causes_adjacency`` is the single grid
    cell that is already occupied *and* whose letter matches the new word's
    letter at that position.  For the very first word (empty grid) no such cell
    exists, so ``intersection_cell`` is ``None``.

    Args:
        grid:      Sparse grid dict, (row, col) -> uppercase letter.
        entries:   List of already-placed Entry objects (unused directly here,
                   kept for interface consistency with the broader placer API).
        word:      Uppercase answer to test.
        row:       Row of the first letter.
        col:       Column of the first letter.
        direction: "across" (increment col) or "down" (increment row).

    Returns:
        True if the placement is legal; False otherwise.
    """
    if causes_collision(grid, word, row, col, direction):
        return False

    # Determine the intersection cell: the one grid cell already occupied whose
    # letter agrees with the new word at that position.
    dr, dc = (0, 1) if direction == "across" else (1, 0)
    intersection_cell: tuple[int, int] | None = None
    for i, letter in enumerate(word):
        cell = (row + dr * i, col + dc * i)
        if grid.get(cell) == letter:
            intersection_cell = cell
            break  # there is at most one valid intersection for a legal placement

    if causes_adjacency(grid, word, row, col, direction, intersection_cell):
        return False

    return True


def place_first(grid: Grid, entries: list, candidate: dict) -> None:
    """Place the first candidate at (0, 0) across, unconditionally.

    The grid is assumed empty (this is the seed placement of an attempt,
    Requirement 3.1). Each letter of ``candidate["answer"]`` is written
    into the grid along row 0, and an ``Entry`` is appended to ``entries``.

    Args:
        grid:      Sparse grid dict, (row, col) -> uppercase letter (empty).
        entries:   List of already-placed Entry objects (empty for a new attempt).
        candidate: Dict with keys ``answer``, ``name``, ``kind``, ``file``,
                   ``line``, ``doc``.
    """
    answer = candidate["answer"]
    for i, letter in enumerate(answer):
        grid[(0, i)] = letter
    entries.append(
        Entry(
            answer=answer,
            name=candidate["name"],
            kind=candidate["kind"],
            file=candidate["file"],
            line=candidate["line"],
            direction="across",
            row=0,
            col=0,
        )
    )

def try_place(grid: Grid, entries: list, candidate: dict) -> bool:
    """Try to place *candidate* crossing an existing entry; return True on success.

    For each existing entry, for each index ``i`` in the new word, and for each
    position ``j`` in the existing entry's answer where the letters match, the
    new word's start is computed so that letter ``i`` lands on the existing
    entry's letter-``j`` cell.  The new entry runs perpendicular to the existing
    one (across crosses down, down crosses across), which guarantees a genuine
    intersection.  The first placement that satisfies ``can_place`` is committed
    (letters written into the grid, an ``Entry`` appended) and ``True`` is
    returned.  If no combination yields a legal placement, the candidate is
    dropped (nothing is mutated) and ``False`` is returned (Requirement 3.3).

    Coordinate derivation:
    - Existing "across": letter ``j`` sits at ``(e.row, e.col + j)``.  The new
      word runs "down" (rows increase), so its start is
      ``(e.row - i, e.col + j)``.
    - Existing "down": letter ``j`` sits at ``(e.row + j, e.col)``.  The new
      word runs "across" (cols increase), so its start is
      ``(e.row + j, e.col - i)``.

    Args:
        grid:      Sparse grid dict, (row, col) -> uppercase letter.
        entries:   List of already-placed Entry objects (non-empty).
        candidate: Dict with keys ``answer``, ``name``, ``kind``, ``file``,
                   ``line``, ``doc``.

    Returns:
        True if the candidate was placed; False if it was dropped.
    """
    word = candidate["answer"]

    for existing in entries:
        for i, new_letter in enumerate(word):
            for j, old_letter in enumerate(existing.answer):
                if new_letter != old_letter:
                    continue

                if existing.direction == "across":
                    # Cross it with a "down" placement.
                    row, col = existing.row - i, existing.col + j
                    direction = "down"
                    dr, dc = 1, 0
                else:
                    # Cross it with an "across" placement.
                    row, col = existing.row + j, existing.col - i
                    direction = "across"
                    dr, dc = 0, 1

                if not can_place(grid, entries, word, row, col, direction):
                    continue

                for k, letter in enumerate(word):
                    grid[(row + dr * k, col + dc * k)] = letter
                entries.append(
                    Entry(
                        answer=word,
                        name=candidate["name"],
                        kind=candidate["kind"],
                        file=candidate["file"],
                        line=candidate["line"],
                        direction=direction,
                        row=row,
                        col=col,
                    )
                )
                return True

    return False


def build_grid(
    candidates: list[dict],
    attempts: int = 50,
    seed=None,
) -> tuple[Grid, list["Entry"]]:
    """Run multiple shuffled placement attempts and return the densest grid.

    Algorithm:
    1. Empty candidates → return ({}, []) immediately.
    2. Seed the RNG once if *seed* is not None.
    3. For each attempt: shuffle a copy of candidates, place the first word
       unconditionally at (0, 0) across, then try to cross-place every
       remaining candidate.
    4. Keep the attempt whose (len(entries), len(grid)) pair is greatest
       lexicographically (primary: most entries placed; tiebreak: most filled
       cells).  Ties are resolved in favour of the first-seen attempt.
    5. Return (best_grid, best_entries).

    Args:
        candidates: List of candidate dicts (keys: answer, name, kind, file,
                    line, doc).  Must not be empty to get a non-trivial result.
        attempts:   Number of shuffled placement attempts to run (Req 3.7).
        seed:       Optional RNG seed for deterministic tests (Req 3.2).

    Returns:
        A (grid, entries) tuple for the best attempt found.
    """
    if not candidates:
        return {}, []

    if seed is not None:
        random.seed(seed)

    best_grid: Grid = {}
    best_entries: list[Entry] = []
    best_density = (-1, -1)

    for _ in range(attempts):
        shuffled = candidates[:]
        random.shuffle(shuffled)

        grid: Grid = {}
        entries: list[Entry] = []

        place_first(grid, entries, shuffled[0])

        for candidate in shuffled[1:]:
            try_place(grid, entries, candidate)

        density = (len(entries), len(grid))
        if density > best_density:
            best_density = density
            best_grid = grid
            best_entries = entries

    return best_grid, best_entries
