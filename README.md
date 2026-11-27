# Crossbones

Turns a Python codebase into a crossword that teaches you the code.
Every answer is a real symbol from the repo, and a verifier guarantees the puzzle can't invent things.

**Live puzzle:** https://vishakha-2811.github.io/crossbones/crossword.html

## The stitch (Frankenstein)
Three things that don't belong together:
1. **Static analysis:** `extractor.py` pulls function, class and file names from a repo using Python's `ast`.
2. **A crossword layout algorithm:** `placer.py` is a greedy placer, best of 50 shuffled attempts.
3. **An LLM clue writer:** `clues.py` writes one-line clues from docstrings, cached in `clues_cache.json`.

The **verifier** (`verifier.py`) holds them together. It checks that every answer is in the extracted symbol set, every grid word matches its answer, no clue contains its own answer, and every crossing letter agrees.

## Run it
Requires Python 3 and nothing else (standard library only).

```
python crossbones.py <path-to-a-python-repo>
```

This prints the verified grid and clue lists, and writes `crossword.html` (open it in a browser to play).

Optional live clues: set `GROQ_API_KEY` in your terminal first. Without a key, clues fall back to the docstring or a template. Clues are cached, so reruns are free.

## Show the verifier catching a fake answer
```
python demo_verifier.py <path-to-a-python-repo>
```

## Tests
```
python -m unittest discover tests
```

## How Kiro was used
- **Steering** (`.kiro/steering/project.md`): stack rules, "answers must be real symbols", "don't rewrite extractor.py".
- **Spec-driven development** (`.kiro/specs/crossbones-cli/`): requirements, design and tasks. Kiro built the placer and verifier (with their tests) from the task list, run in batches in Supervised mode.
- Not used: hooks, custom agents, MCP, powers.

## License
MIT