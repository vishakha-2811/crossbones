import json
import os
import re
import urllib.request

CACHE = "clues_cache.json"


def _norm(text):
    return re.sub(r"[^a-z]", "", text.lower())


def leaks(clue, answer):
    """True if the clue contains the answer (ignoring spaces, underscores, case)."""
    return _norm(answer) in _norm(clue)


def template_clue(sym):
    """Free clue built from the docstring or the symbol's kind and file."""
    answer, n = sym["answer"], len(sym["answer"])
    doc = (sym.get("doc") or "").strip()
    if doc:
        first = re.split(r"(?<=[.!?])\s|\n\n", doc)[0].replace("\n", " ").strip()
        if len(first) > 110:
            first = first[:110].rsplit(" ", 1)[0] + "..."
        if first.endswith(":"):
            first = ""
        if first and not leaks(first, answer):
            return f"{first} ({n})"
    filename = os.path.basename(sym["file"])
    if leaks(filename, answer):
        return f"A {sym['kind']} in this repo ({n})"
    return f"A {sym['kind']} in {filename} ({n})"


def llm_clue(sym, key):
    prompt = (
        "Write a one-line crossword clue (max 12 words) for this code symbol. "
        "Do not use the symbol's name or any part of it. Reply with only the clue.\n"
        f"Kind: {sym['kind']}\nName: {sym['name']}\nDocstring: {sym.get('doc') or '(none)'}"
    )
    body = json.dumps({
        "model": "openai/gpt-oss-20b",
        "max_tokens": 400,
        "reasoning_effort": "low",
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions", data=body,
        headers={"content-type": "application/json",
                 "authorization": f"Bearer {key}",
                 "user-agent": "crossbones/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["choices"][0]["message"]["content"].strip().strip('"')


def make_clue(sym, key):
    if key:
        try:
            clue = llm_clue(sym, key)
            if clue and not leaks(clue, sym["answer"]):
                return f"{clue} ({len(sym['answer'])})"
        except Exception as err:
            detail = err.read().decode()[:200] if hasattr(err, "read") else ""
            print(f"LLM clue failed for {sym['answer']}: {err} {detail}")
    return template_clue(sym)


def get_clues(entries, symbol_map):
    """Return {answer: clue}. Cached on disk so reruns are free."""
    cache = {}
    if os.path.exists(CACHE):
        try:
            with open(CACHE, encoding="utf-8") as f:
                cache = json.load(f)
        except json.JSONDecodeError:
            cache = {}
    key = os.environ.get("GROQ_API_KEY")
    for e in entries:
        if e.answer not in cache:
            cache[e.answer] = make_clue(symbol_map[e.answer], key)
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
    return {e.answer: cache[e.answer] for e in entries}