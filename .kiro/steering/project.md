# Crossbones
Turns a Python codebase into a crossword that teaches the code.

## Rules
- Python 3 only. Standard library only (use `ast`), except for the LLM client.
- Keep code simple and short. No frameworks.
- Every crossword answer MUST be a real symbol (function, class, or file name) from the repo.
- Answers: uppercase, underscores removed, 4-15 letters, deduplicated.
- Keep a map of answer -> file:line.
- Clues must never contain their own answer.
- Cache all LLM clues in clues_cache.json.
- Put tests in tests/ and make them pass before finishing a task.
- Do one task at a time. Do not refactor unrelated files.
- extractor.py already exists. Do not rewrite it.
- Run tests with `python -m unittest discover tests`. Never use pytest. Never run pip install.