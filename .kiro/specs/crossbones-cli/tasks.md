# Implementation Plan: crossbones-cli

## Overview

Implement the four new modules (`placer.py`, `verifier.py`, `renderer.py`, `crossbones.py`), a test fixture repo, and all tests. Each task builds on the previous ones. `extractor.py` is never modified.

## Tasks

- [x] 1. Create the `Entry` dataclass and grid type in `placer.py`
  - Define the `Entry` dataclass with fields: `answer`, `name`, `kind`, `file`, `line`, `direction`, `row`, `col`
  - Define the `Grid` type alias as `dict[tuple[int, int], str]` (sparse dict, cell absent = empty)
  - Create `placer.py` at the repository root with only these definitions (no placement logic yet)
  - _Requirements: 3.8, 6.1, 6.3_

- [x] 2. Implement collision and adjacency checks in `placer.py`
  - [x] 2.1 Implement `causes_collision(grid, word, row, col, direction) -> bool`
    - Return `True` if any cell the new word would occupy already holds a different letter
    - _Requirements: 3.4_
  - [x] 2.2 Implement `causes_adjacency(grid, word, row, col, direction, intersection_cell) -> bool`
    - Return `True` if any non-intersection cell of the new word has a neighbour perpendicular to the word's direction, OR if the cell immediately before the word's start or after its end (along the direction) is occupied
    - `intersection_cell` is `(row, col)` of the crossing cell, or `None` for the first word
    - _Requirements: 3.5_
  - [ ]* 2.3 Write unit tests for `causes_collision` and `causes_adjacency`
    - Test: clean grid → no collision; occupied matching cell → no collision; occupied mismatched cell → collision
    - Test: word placed parallel and side-touching → adjacency; word abutting head-on → adjacency; isolated word → no adjacency
    - _Requirements: 3.4, 3.5_

- [x] 3. Implement `can_place` and the core placement helpers in `placer.py`
  - [x] 3.1 Implement `can_place(grid, entries, word, row, col, direction) -> bool`
    - Returns `True` iff neither `causes_collision` nor `causes_adjacency` fires for the given position
    - _Requirements: 3.4, 3.5_
  - [x] 3.2 Implement `place_first(grid, entries, candidate) -> None`
    - Place the first candidate at `(0, 0)` across, unconditionally; write letters into grid; append `Entry` to entries
    - _Requirements: 3.1_
  - [x] 3.3 Implement `try_place(grid, entries, candidate) -> bool`
    - Enumerate all candidate positions by intersecting each letter of the new word with each letter of each existing entry (perpendicular direction only)
    - For each computed position, call `can_place`; commit the first valid position and return `True`; return `False` if none found
    - _Requirements: 3.2, 3.3_

- [x] 4. Implement `build_grid` in `placer.py`
  - Implement `build_grid(candidates, attempts=50, seed=None) -> tuple[Grid, list[Entry]]`
  - Run up to `attempts` shuffled placement attempts; use `random.seed(seed)` when seed is given
  - Each attempt: shuffle candidates, call `place_first` for the first, `try_place` for each subsequent; dropped candidates are silently skipped
  - Track density (number of entries, tie-break: filled-cell count); keep the best result
  - Return `({}, [])` if candidates is empty
  - _Requirements: 3.1, 3.2, 3.3, 3.6, 3.7_

- [x] 5. Checkpoint — verify placement logic before continuing
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Create `verifier.py` with the `Failure` named tuple and `verify_grid`
  - [x] 6.1 Define `Failure = collections.namedtuple("Failure", "entry check detail")` in `verifier.py`
    - Valid `check` values: `"symbol"`, `"grid-word"`, `"clue-containment"`, `"crossing"`
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  - [x] 6.2 Implement the `"symbol"` and `"grid-word"` checks inside `verify_grid`
    - symbol: `entry.answer not in symbols_set` → append `Failure(..., "symbol", ...)`
    - grid-word: read cells from grid along the entry's direction; joined string ≠ answer → append `Failure(..., "grid-word", ...)`
    - _Requirements: 4.1, 4.2_
  - [x] 6.3 Implement the `"clue-containment"` check inside `verify_grid`
    - Resolve clue: `clues_cache[answer]` if present, else `symbol doc` if non-empty, else skip
    - Fail if `entry.answer.lower() in clue.lower()` (Req 4.3); skip entirely when no clue (Req 4.7)
    - _Requirements: 4.3, 4.7_
  - [x] 6.4 Implement the `"crossing"` check inside `verify_grid`
    - For each cell of the entry covered by another entry, recompute the other entry's required letter at that cell and compare; mismatch → `Failure(..., "crossing", ...)`
    - _Requirements: 4.4_
  - [x] 6.5 Implement `verify_grid(grid, entries, symbols, clues) -> list[Failure]`
    - Run all four checks for every entry; collect all failures; return the list (empty = all passed)
    - _Requirements: 4.5, 4.6_

- [x] 7. Create `renderer.py`
  - [x] 7.1 Implement `number_entries(entries) -> dict[tuple[int, int], int]`
    - Scan bounding-box cells in row-major order; assign the next number to any cell that starts an across or down entry; across and down entries starting in the same cell share one number
    - _Requirements: 5.2_
  - [x] 7.2 Implement `render(grid, entries) -> str`
    - Compute bounding box from grid keys; render rectangle: filled cells show the letter, empty cells show `·` (or `#` if `sys.stdout.encoding` is not UTF-8), one space between columns
    - Prefix each entry's first cell with `[n]` where `n` is its number
    - After the grid, print `ACROSS` and `DOWN` sections: each line is `  n. ANSWER  (file:line)`
    - Return the full string; the CLI prints it
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  - [ ]* 7.3 Write unit tests for `number_entries` and `render`
    - Test: two entries sharing a start cell get the same number; row-major ordering; across before down in list
    - Test: empty-cell character used for unfilled cells; `file:line` origin appears in output
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 8. Create `crossbones.py` (CLI entry point)
  - [x] 8.1 Implement `select_candidates(symbols, limit=25) -> list[dict]`
    - Filter: answer must be alphabetic and 4–15 letters (defensive re-check)
    - Sort key: `(doc present descending, answer length descending)`; drop duplicate answers; cap at `limit`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  - [x] 8.2 Implement `main(argv) -> int`
    - Parse `argv[1]` as `repo_path`; missing/non-directory/no-arg → usage message to stderr, return non-zero
    - Call `extract_symbols(repo_path)`; empty → "no symbols found" message, return 0
    - Call `select_candidates`, `placer.build_grid`; zero entries → "no symbols found" message, return 0
    - Load `clues_cache.json` if present; malformed JSON → warn to stderr, treat as `{}`
    - Call `verifier.verify_grid`; print each failure (answer, origin, check name) to stdout before the grid
    - Print `renderer.render(grid, entries)` to stdout; return 0
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 4.6, 5.4, 5.5_
  - [x] 8.3 Add `if __name__ == "__main__": sys.exit(main(sys.argv))` guard
    - _Requirements: 1.1_
  - [ ]* 8.4 Write unit tests for `select_candidates`
    - Test: docstring symbols preferred; 25-cap enforced; duplicate answers dropped; longest first; 4–15 letter filter
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 9. Create the fixture repo in `tests/fixtures/`
  - Create `tests/fixtures/sample_repo/utils.py` with two functions and a class, each with docstrings, chosen so their normalized answers are ≥ 4 letters and do not overlap
  - Create `tests/fixtures/sample_repo/models.py` with two classes with docstrings
  - Ensure the fixture yields ≥ 5 usable symbols via `extract_symbols`, enough to build a small grid
  - _Requirements: (supports P5 round-trip tests)_

- [x] 10. Write P1 grid-legality tests in `tests/test_placer.py`
  - [x] 10.1 `test_p1_first_word_placed`: `build_grid` with one candidate; assert one entry; grid cells spell the answer
    - _Requirements: P1, 3.1_
  - [x] 10.2 `test_p1_crossing_entries_agree`: two candidates sharing a letter; assert both entries' letters agree at the shared cell
    - _Requirements: P1, 3.2, 6.3_
  - [x] 10.3 `test_p1_no_collision_or_adjacency`: multi-candidate grid; assert no two entries conflict at any cell; assert no illegal adjacency by running `causes_adjacency` on each entry against the final grid
    - _Requirements: P1, 3.4, 3.5_
  - [x] 10.4 `test_p1_dropped_candidates_absent`: a candidate that cannot legally cross any placed entry must not appear in the final entries list
    - _Requirements: P1, 3.3_

- [x] 11. Write P4 verification-detection tests in `tests/test_verifier.py`
  - [x] 11.1 `test_p4_symbol_check`: entry whose answer is absent from the symbol set → failure with check `"symbol"`
    - _Requirements: P4, 4.1_
  - [x] 11.2 `test_p4_grid_word_check`: grid letters differ from entry answer → failure with check `"grid-word"`
    - _Requirements: P4, 4.2_
  - [x] 11.3 `test_p4_clue_containment`: clue containing the answer → failure `"clue-containment"`; clue without it → no failure
    - _Requirements: P4, 4.3_
  - [x] 11.4 `test_p4_crossing`: two entries requiring different letters at a shared cell → failure `"crossing"`
    - _Requirements: P4, 4.4_
  - [x] 11.5 `test_p4_no_clue_skipped`: entry with no clue and no doc → no `"clue-containment"` failure
    - _Requirements: P4, 4.7_

- [x] 12. Write P5 round-trip and CLI end-to-end tests in `tests/test_integration.py`
  - [x] 12.1 `test_p5_placer_output_accepted`: run full pipeline on fixture repo; `verify_grid` returns empty failures list
    - _Requirements: P5_
  - [x] 12.2 `test_p5_cli_end_to_end`: call `crossbones.main` with fixture repo path (patch `sys.argv`); capture stdout; assert exit code 0, grid block present, each entry line has `file:line` origin
    - _Requirements: P5, 1.1, 5.4, 5.5_
  - [ ]* 12.3 Write CLI usage-error tests in `tests/test_cli.py`
    - Test: no args → non-zero exit, usage on stderr
    - Test: non-directory path → non-zero exit, usage on stderr
    - Test: empty repo → exit 0 with "no symbols" message
    - _Requirements: 1.2, 1.3, 1.4_

- [ ] 13. Final checkpoint — all tests pass
  - Run `python -m unittest discover tests` and confirm zero failures before marking this task complete.
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at natural boundaries
- No third-party libraries; all tests use `unittest` only (no hypothesis)
- `extractor.py` is never modified; it is imported as-is
- The placer is deterministic when `seed` is passed (used in all unit tests)
- The sparse-dict grid means no resizing; bounding box is computed only at render time

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["2.3", "3.1"] },
    { "id": 3, "tasks": ["3.2", "3.3"] },
    { "id": 4, "tasks": ["4"] },
    { "id": 5, "tasks": ["5"] },
    { "id": 6, "tasks": ["6.1"] },
    { "id": 7, "tasks": ["6.2", "6.3", "6.4"] },
    { "id": 8, "tasks": ["6.5"] },
    { "id": 9, "tasks": ["7.1", "8.1"] },
    { "id": 10, "tasks": ["7.2"] },
    { "id": 11, "tasks": ["7.3", "8.2"] },
    { "id": 12, "tasks": ["8.3"] },
    { "id": 13, "tasks": ["8.4", "9"] },
    { "id": 14, "tasks": ["10.1", "10.2", "10.3", "10.4", "11.1", "11.2", "11.3", "11.4", "11.5"] },
    { "id": 15, "tasks": ["12.1", "12.2", "12.3"] },
    { "id": 16, "tasks": ["13"] }
  ]
}
```
