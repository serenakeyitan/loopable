"""Deterministic manual-retry detector. No LLM calls, no prompt text stored.

The catalog answers WHAT loop to suggest; this module adds a second WHEN
trigger: the user is visibly re-running the same task by hand. Two signals,
both computed from local session state only:

  retry:    a short retry-vocabulary message right after another one
            ("run it again" then "still failing" = third attempt)
  similar:  token-set Jaccard >= 0.6 against two recent messages

State keeps per-message token hashes and a retry flag for the last 6
messages. Raw prompt text is not written to disk (DESIGN: privacy).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

RETRY_PHRASES = (
    "try again",
    "try it again",
    "run it again",
    "run again",
    "do it again",
    "once more",
    "one more time",
    "still failing",
    "still fails",
    "still broken",
    "still not working",
    "still doesnt work",
    "still happening",
    "still the same",
    "same error",
    "same issue",
    "same problem",
    "didnt work",
    "doesnt work",
    "not fixed",
    "no luck",
    "nope still",
    "再试一次",
    "再来一次",
    "还是不行",
    "还是报错",
    "又失败",
)
RETRY_MAX_TOKENS = 8
AGAIN_MAX_TOKENS = 5
SIMILAR_MIN_TOKENS = 4
SIMILAR_JACCARD = 0.6
SIMILAR_NEEDED = 2  # current message is the third look-alike
HISTORY_CAP = 6

SIGNAL_RETRY = "two retry-style messages in a row"
SIGNAL_SIMILAR = "three similar messages this session"


def _tokens(text: str) -> list[str]:
    out: list[str] = []
    for raw in text.split():
        tok = "".join(ch for ch in raw if ch.isalnum())
        if tok:
            out.append(tok)
    return out


def _hash(token: str) -> str:
    return hashlib.sha1(token.encode("utf-8")).hexdigest()[:10]


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def is_retry(text: str) -> bool:
    """Short message in retry vocabulary; long messages are new asks."""
    toks = _tokens(text)
    if not toks or len(toks) > RETRY_MAX_TOKENS:
        return False
    joined = " ".join(toks)
    if any(p in joined or p in text for p in RETRY_PHRASES):
        return True
    return "again" in toks and len(toks) <= AGAIN_MAX_TOKENS


def _load(path: Path) -> list[tuple[frozenset[str], bool]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        out: list[tuple[frozenset[str], bool]] = []
        for item in raw if isinstance(raw, list) else []:
            if not isinstance(item, dict):
                continue
            toks = item.get("tokens")
            if not isinstance(toks, list):
                continue
            out.append((frozenset(str(t) for t in toks), bool(item.get("retry"))))
        return out
    except Exception:
        return []


def observe(state_dir: Path, session_id: str, text: str) -> str:
    """Record one normalized prompt; return a signal description or "".

    The caller owns rendering and session dedupe. Errors degrade to ""
    (fail open) and a best-effort state write.
    """
    cur = frozenset(_hash(t) for t in _tokens(text))
    retry = is_retry(text)
    path = state_dir / f"recent-{session_id}.json"
    history = _load(path)

    signal = ""
    if retry and history and history[-1][1]:
        signal = SIGNAL_RETRY
    elif len(cur) >= SIMILAR_MIN_TOKENS:
        similar = sum(
            1
            for prev, _ in history
            if len(prev) >= SIMILAR_MIN_TOKENS and _jaccard(cur, prev) >= SIMILAR_JACCARD
        )
        if similar >= SIMILAR_NEEDED:
            signal = SIGNAL_SIMILAR

    history.append((cur, retry))
    serialized = [{"tokens": sorted(p), "retry": r} for p, r in history[-HISTORY_CAP:]]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(serialized), encoding="utf-8")
    except Exception:
        pass
    return signal
