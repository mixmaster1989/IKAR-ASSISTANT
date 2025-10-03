"""
JSON Surgeon: aggressive extraction and repair of JSON from LLM outputs.

Goals:
- Extract the most likely JSON object/array even if surrounded by text, code fences,
  or prefixed markers like IMAGE!/SPEAK!.
- Repair common issues: trailing commas, single quotes, unquoted keys,
  Python booleans/None, smart quotes.
- Optionally parse via JSON5 if installed.
"""

from __future__ import annotations

import json
import re
from typing import Any, List, Optional, Tuple


SMART_QUOTES_MAP = {
    "\u201c": '"',  # left double smart quote
    "\u201d": '"',  # right double smart quote
    "\u2018": "'",  # left single smart quote
    "\u2019": "'",  # right single smart quote
    "\u00ab": '"',  # «
    "\u00bb": '"',  # »
}


def _strip_code_fences(text: str) -> str:
    t = text.strip()
    # Remove leading markers
    t = re.sub(r"^(?:SPEAK!|IMAGE!)\s*", "", t, flags=re.IGNORECASE)
    # Remove ```json or ``` fences
    if t.startswith("```json"):
        t = t[7:]
    elif t.startswith("```"):
        t = t[3:]
    if t.endswith("```"):
        t = t[:-3]
    return t.strip()


def _normalize_quotes(text: str) -> str:
    t = text
    for k, v in SMART_QUOTES_MAP.items():
        t = t.replace(k, v)
    return t


def _extract_json_candidates(text: str) -> List[Tuple[int, int, str]]:
    """
    Scan the text and extract substrings that look like top-level JSON
    objects or arrays using a stack-based approach. Returns list of
    (start, end, substring).
    """
    t = text
    candidates: List[Tuple[int, int, str]] = []

    in_str = False
    esc = False
    stack: List[str] = []
    start_idx: Optional[int] = None

    for i, ch in enumerate(t):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue

        # not in string
        if ch == '"':
            in_str = True
            esc = False
            continue

        if ch in '{[':
            if not stack:
                start_idx = i
            stack.append(ch)
        elif ch in '}]':
            if stack:
                opener = stack.pop()
                if (opener, ch) not in (('{', '}'), ('[', ']')):
                    # mismatched, reset
                    stack.clear()
                    start_idx = None
                elif not stack and start_idx is not None:
                    end_idx = i + 1
                    candidates.append((start_idx, end_idx, t[start_idx:end_idx]))
                    start_idx = None

    return candidates


def _remove_trailing_commas(s: str) -> str:
    # Remove , before } or ]
    return re.sub(r",\s*([}\]])", r"\1", s)


def _quote_unquoted_keys(s: str) -> str:
    # Quote keys that look like identifiers: { key: value } -> { "key": value }
    # Only when after { or , or [
    pattern = r"(?P<prefix>[{\[,]\s*)(?P<key>[A-Za-z_][A-Za-z0-9_\-]*)\s*:"
    return re.sub(pattern, r'\g<prefix>"\g<key>":', s)


def _replace_py_literals(s: str) -> str:
    s = re.sub(r"(?<![A-Za-z0-9_])None(?![A-Za-z0-9_])", "null", s)
    s = re.sub(r"(?<![A-Za-z0-9_])True(?![A-Za-z0-9_])", "true", s)
    s = re.sub(r"(?<![A-Za-z0-9_])False(?![A-Za-z0-9_])", "false", s)
    return s


def _to_double_quotes(s: str) -> str:
    # Convert single-quoted strings to double-quoted ones conservatively.
    # Replace '...'
    return re.sub(r"'([^'\\]*(?:\\.[^'\\]*)*)'", r'"\1"', s)


def _try_json5_load(s: str) -> Optional[Any]:
    try:
        import json5  # type: ignore
        return json5.loads(s)
    except Exception:
        return None


def _attempt_repairs(s: str) -> Optional[Any]:
    # Try sequence of repairs; return first successful parse
    # 1) Remove trailing commas
    t = _remove_trailing_commas(s)
    try:
        return json.loads(t)
    except Exception:
        pass

    # 2) Replace Python literals
    t2 = _replace_py_literals(t)
    try:
        return json.loads(t2)
    except Exception:
        pass

    # 3) Quote unquoted keys
    t3 = _quote_unquoted_keys(t2)
    try:
        return json.loads(t3)
    except Exception:
        pass

    # 4) Convert single quotes to double quotes
    t4 = _to_double_quotes(t3)
    try:
        return json.loads(t4)
    except Exception:
        pass

    # 5) Try JSON5 if available
    j5 = _try_json5_load(t4)
    if j5 is not None:
        return j5

    return None


def parse_all_json(text: str) -> List[Any]:
    """Extract and parse all JSON objects/arrays from text."""
    cleaned = _normalize_quotes(_strip_code_fences(text))
    cands = _extract_json_candidates(cleaned)
    results: List[Any] = []
    for _, _, c in cands:
        # Quick path
        try:
            results.append(json.loads(c))
            continue
        except Exception:
            pass
        repaired = _attempt_repairs(c)
        if repaired is not None:
            results.append(repaired)
    return results


def parse_first_json_object(text: str) -> Optional[dict]:
    """Extract first JSON object (dict) from text and parse it."""
    for item in parse_all_json(text):
        if isinstance(item, dict):
            return item
    return None


def parse_first_json_array(text: str) -> Optional[list]:
    """Extract first JSON array (list) from text and parse it."""
    for item in parse_all_json(text):
        if isinstance(item, list):
            return item
    return None

