# Requirements Document

## Introduction

Crossbones is a CLI tool that turns a Python codebase into a crossword that teaches the code. The user runs `python crossbones.py <repo_path>`. The tool extracts symbols from the repository (via the existing `extractor.py`, which is out of scope for rewrite), places symbol names into a crossword grid using a greedy placer, verifies every grid entry against the extracted symbol set, and prints the solved grid to the terminal with numbered across/down entries and each answer's `file:line` origin.

This spec covers the CLI entry point, candidate selection, greedy crossword placement, entry verification, and terminal output. Clue generation, HTML output, non-Python languages, and difficulty levels are out of scope.

## Glossary

- **Crossbones**: The CLI tool defined by this document.
- **Repo**: The Python codebase directory passed as `<repo_path>` on the command line.
- **Symbol**: A function, class, or file name found in the Repo by `extractor.py`'s `extract_symbols`.
- **Answer**: A symbol name normalized to uppercase with underscores removed, between 4 and 15 letters, deduplicated across the grid.
- **Candidate**: A symbol selected for possible placement, carrying `answer`, `name`, `kind`, `file`, `line`, `doc` (as returned by `extract_symbols`).
- **Grid**: The two-dimensional character grid holding placed Answers.
- **Entry**: An Answer placed into the Grid, with a direction (across or down), a starting row and column, and a length.
- **Intersection**: A cell shared by two Entries where both entries place the same letter.
- **Collision**: A cell claimed by two entries whose required letters differ.
- **Illegal adjacency**: A placed entry touching another entry's letters along its side (orthogonally adjacent, parallel words) or abutting an unrelated word head-on at its start or end, forming unintended words.
- **Clue**: The text associated with an entry, taken from `clues_cache.json` or a docstring. Clue generation is out of scope; this spec only consumes clues when they exist.
- **Placement attempt**: One pass of the greedy placer over the shuffled candidate list. 50 attempts are run; the densest result is kept.
- **Density**: The number of Entries in a Grid, used to rank placement attempts. Ties are broken by the number of filled cells.
- **Crossing letter conflict**: An intersection where the two entries' letters differ; equivalent to a Collision.
- **clues_cache.json**: The cache file of LLM-generated clues keyed by answer, maintained outside this feature, read by verification when present.

## Requirements

### Requirement 1: CLI Entry Point

**User Story:** As a developer, I want to run `python crossbones.py <repo_path>` so that I get a crossword of my codebase without any setup.

#### Acceptance Criteria

1. WHEN Crossbones is run as `python crossbones.py <repo_path>` with an existing directory, THE Crossbones CLI SHALL extract symbols, place the crossword, verify all entries, and print the output to the terminal, then exit with status 0.
2. WHEN Crossbones is run with a missing or non-directory `<repo_path>` argument, THE Crossbones CLI SHALL print a usage message to stderr and exit with a non-zero status.
3. WHEN Crossbones is run with no arguments, THE Crossbones CLI SHALL print a usage message to stderr and exit with a non-zero status.
4. WHEN the Repo contains no usable symbols, THE Crossbones CLI SHALL print a message stating that no symbols were found and exit with status 0.

### Requirement 2: Candidate Selection

**User Story:** As a crossword author, I want the placer to work from real, documented symbols so that the crossword teaches the code.

#### Acceptance Criteria

1. WHEN candidates are selected, THE Candidate Selector SHALL prefer symbols that have a docstring over symbols without a docstring.
2. WHEN candidates are selected, THE Candidate Selector SHALL take at most 25 candidates.
3. WHEN candidates are selected, THE Candidate Selector SHALL sort them longest Answer first.
4. WHERE an Answer would duplicate an already-selected Answer, THE Candidate Selector SHALL drop the duplicate.
5. WHEN candidates are selected, every candidate's Answer SHALL be 4 to 15 letters, alphabetic, and uppercase with underscores removed.
6. WHEN candidates are selected, every candidate SHALL correspond to a symbol returned by `extract_symbols(repo_path)`, and Crossbones SHALL NOT modify `extractor.py`.

### Requirement 3: Greedy Placement

**User Story:** As a crossword author, I want intersecting words placed without collisions so that the grid is a legal crossword.

#### Acceptance Criteria

1. WHEN a placement attempt runs, THE Placer SHALL place the first candidate in the candidate list into an empty Grid.
2. WHEN a subsequent candidate is placed, THE Placer SHALL place it at a letter intersection with a previously placed Entry.
3. WHEN a candidate cannot be placed at any legal intersection, THE Placer SHALL drop the candidate from that attempt.
4. WHEN a candidate's placement would cause a Collision, THE Placer SHALL reject that placement.
5. WHEN a candidate's placement would cause Illegal adjacency, THE Placer SHALL reject that placement.
6. WHEN all 50 placement attempts have run, THE Placer SHALL keep the Grid with the highest Density (number of Entries, ties broken by filled-cell count).
7. WHILE fewer than 50 placement attempts have run, THE Placer SHALL shuffle the candidate list and run another attempt.
8. THE Placer SHALL place every Entry either across or down.

### Requirement 4: Entry Verification

**User Story:** As a crossword solver, I want every entry checked against the real codebase so that I can trust what the crossword teaches.

#### Acceptance Criteria

1. THE Verifier SHALL fail any Entry whose Answer is not in the extracted symbol set, and SHALL report that the "symbol" check failed.
2. THE Verifier SHALL fail any Entry whose Grid letters do not spell the Answer, and SHALL report that the "grid-word" check failed.
3. WHEN a Clue is provided for an Entry (from `clues_cache.json` or a docstring), THE Verifier SHALL fail that Entry if the Clue contains the Answer, and SHALL report that the "clue-containment" check failed.
4. THE Verifier SHALL fail any Entry with a Crossing letter conflict, and SHALL report that the "crossing" check failed.
5. WHEN an Entry passes all applicable checks, THE Verifier SHALL accept the Entry.
6. WHEN one or more Entries fail verification, THE Crossbones CLI SHALL report each failed Entry together with the name of the failed check, and SHALL still print the remaining output.
7. WHERE no Clue is available for an Entry, THE Verifier SHALL skip the clue-containment check for that Entry.

### Requirement 5: Terminal Output

**User Story:** As a crossword solver, I want a printed grid with numbered entries so that I can read the crossword in my terminal.

#### Acceptance Criteria

1. WHEN output is printed, THE Crossbones CLI SHALL render the Grid as a rectangle of characters to the terminal, with empty cells visually distinct from filled cells.
2. WHEN output is printed, THE Crossbones CLI SHALL number the Entries using standard crossword numbering (row-major order of entry starts, across and down sharing a number when they start in the same cell).
3. WHEN output is printed, THE Crossbones CLI SHALL list the across Entries and the down Entries with their numbers.
4. WHEN output is printed, THE Crossbones CLI SHALL show, for every Entry, the Answer's `file:line` origin.
5. THE Crossbones CLI SHALL maintain a map of Answer to `file:line` for all placed Entries and use it for the printed origins.

### Requirement 6: Answer Constraints (Cross-Cutting)

**User Story:** As the project owner, I want every crossword answer to be a real, well-formed symbol so that the crossword teaches the actual code.

#### Acceptance Criteria

1. THE Crossbones CLI SHALL place only Answers that are uppercase, alphabetic, 4 to 15 letters, and deduplicated.
2. THE Crossbones CLI SHALL place only Answers that are real symbols (functions, classes, or file names) from the Repo.
3. WHERE two entries cross, THE Grid SHALL hold one letter per cell, with the letters agreeing at every Intersection.

### Requirement 7: Scope Exclusions

**User Story:** As the project owner, I want this feature to stay small so that it ships quickly.

#### Acceptance Criteria

1. THE Crossbones CLI SHALL provide no clue generation, no web application, no difficulty levels, and no HTML output in this feature.

## Correctness Properties

> **Testing note:** All tests use Python's built-in `unittest` module only. No hypothesis or third-party testing libraries are used. Tests are plain example-based tests.

These properties define testable invariants for the placer and verifier. They are inputs to the design and tasks phases.

### P1: Grid legality (invariant)

For every placement attempt result: reading each placed Entry's cells from the Grid spells exactly the Entry's Answer; every cell holds at most one letter; every pair of crossing Entries agrees on the shared letter; no two Entries are Illegally adjacent (parallel side-touching or head/tail abutment forming unintended words).

### P4: Verification detection (error condition)

For each of the four failure modes, constructing a deliberately broken entry causes the Verifier to fail with the corresponding check name: (a) an answer absent from the symbol set fails "symbol"; (b) a grid word not matching the answer fails "grid-word"; (c) a clue containing the answer fails "clue-containment"; (d) a crossing with mismatched letters fails "crossing".

### P5: Verification acceptance (round trip)

For every Grid produced by the Placer from a valid Repo, the Verifier accepts every Entry (all placed entries satisfy all applicable checks, with clue-containment skipped where no clue exists).

## Out of Scope

- Clue generation (LLM or otherwise); `clues_cache.json` is only read, never written, by this feature.
- Languages other than Python; HTML or web output; difficulty levels.
- Rewriting or modifying `extractor.py`.
