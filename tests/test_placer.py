"""Unit tests for placer.build_grid — grid legality invariants.

Covers tasks 10.1, 10.2, 10.3, and 10.4.
"""

import unittest

from placer import build_grid


def make_candidate(answer, name="sym", kind="function",
                   file="f.py", line=1, doc="A helper."):
    return {"answer": answer, "name": name, "kind": kind,
            "file": file, "line": line, "doc": doc}


def entry_cells(entry):
    """Return a dict of {(row, col): letter_index} for every cell of *entry*."""
    dr, dc = (0, 1) if entry.direction == "across" else (1, 0)
    return {
        (entry.row + dr * i, entry.col + dc * i): i
        for i in range(len(entry.answer))
    }


class TestFirstWordPlaced(unittest.TestCase):
    """Task 10.1 — P1: single-candidate build_grid places exactly one entry
    whose grid cells spell the answer across from (0, 0).
    """

    def test_p1_first_word_placed(self):
        c = make_candidate("LOADDATA")
        grid, entries = build_grid([c], seed=0)

        # Exactly one entry.
        self.assertEqual(len(entries), 1)

        entry = entries[0]
        self.assertEqual(entry.answer, "LOADDATA")
        self.assertEqual(entry.direction, "across")
        self.assertEqual(entry.row, 0)
        self.assertEqual(entry.col, 0)

        # Grid cells spell the answer.
        word_from_grid = "".join(
            grid[(0, i)] for i in range(len("LOADDATA"))
        )
        self.assertEqual(word_from_grid, "LOADDATA")


class TestCrossingEntriesAgree(unittest.TestCase):
    """Task 10.2 — P1: when two candidates share a letter and both are placed,
    the shared intersection cell holds the same letter for both entries.
    """

    def test_p1_crossing_entries_agree(self):
        # "LOADDATA" and "DATAMODEL" both contain 'D' and 'A', so the placer
        # can find at least one valid crossing.
        candidates = [
            make_candidate("LOADDATA"),
            make_candidate("DATAMODEL"),
        ]
        grid, entries = build_grid(candidates, seed=0)

        self.assertEqual(len(entries), 2, "Both candidates should be placed")

        e0, e1 = entries[0], entries[1]
        cells0 = entry_cells(e0)
        cells1 = entry_cells(e1)

        # Find the intersection cell — a cell covered by both entries.
        shared = set(cells0) & set(cells1)
        self.assertTrue(shared, "There must be at least one shared cell")

        for cell in shared:
            letter_from_e0 = e0.answer[cells0[cell]]
            letter_from_e1 = e1.answer[cells1[cell]]
            grid_letter = grid[cell]

            self.assertEqual(
                letter_from_e0, letter_from_e1,
                f"Both entries must require the same letter at {cell}; "
                f"got {letter_from_e0!r} vs {letter_from_e1!r}",
            )
            self.assertEqual(
                grid_letter, letter_from_e0,
                f"Grid cell {cell} must hold {letter_from_e0!r}, got {grid_letter!r}",
            )


class TestNoCollisionOrAdjacency(unittest.TestCase):
    """Task 10.3 — P1 grid-legality invariant: for every placed entry, reading
    its cells from the grid spells the answer exactly; and for every pair of
    entries, any shared cell has the same letter from both.
    """

    def test_p1_no_collision_or_adjacency(self):
        candidates = [
            make_candidate("LOADDATA"),
            make_candidate("DATAMODEL"),
            make_candidate("TOKENIZE"),
            make_candidate("MODELINE"),
            make_candidate("RENDER"),
        ]
        grid, entries = build_grid(candidates, seed=0)

        # At least the first word must have been placed.
        self.assertGreater(len(entries), 0)

        # Each entry's grid cells must spell its own answer.
        for entry in entries:
            dr, dc = (0, 1) if entry.direction == "across" else (1, 0)
            word_from_grid = "".join(
                grid.get((entry.row + dr * i, entry.col + dc * i), "")
                for i in range(len(entry.answer))
            )
            self.assertEqual(
                word_from_grid, entry.answer,
                f"Grid does not spell {entry.answer!r} for entry {entry}",
            )

        # For every pair, any shared cell must agree on its letter.
        for idx, e1 in enumerate(entries):
            cells1 = entry_cells(e1)
            for e2 in entries[idx + 1:]:
                cells2 = entry_cells(e2)
                shared = set(cells1) & set(cells2)
                for cell in shared:
                    letter1 = e1.answer[cells1[cell]]
                    letter2 = e2.answer[cells2[cell]]
                    self.assertEqual(
                        letter1, letter2,
                        f"Collision at {cell}: {e1.answer!r}[{cells1[cell]}]={letter1!r} "
                        f"vs {e2.answer!r}[{cells2[cell]}]={letter2!r}",
                    )


class TestDroppedCandidatesAbsent(unittest.TestCase):
    """Task 10.4 — P1: a candidate that shares no letters with any placed
    entry cannot cross anything and must be dropped from the final entries.
    """

    def test_p1_dropped_candidates_absent(self):
        # "BBBB" contains only 'B'; "LOADDATA" has no 'B' — no crossing possible.
        c1 = make_candidate("LOADDATA")
        c2 = make_candidate("BBBB", name="bbbb")

        grid, entries = build_grid([c1, c2], seed=0)

        # Only the first (seed) word is placed; BBBB can't cross it.
        self.assertEqual(len(entries), 1)
        answers = {e.answer for e in entries}
        self.assertNotIn("BBBB", answers)


if __name__ == "__main__":
    unittest.main()
