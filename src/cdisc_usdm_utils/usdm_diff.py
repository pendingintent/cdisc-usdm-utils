import json
from typing import Any, List, Dict, Optional, Tuple
from collections import defaultdict

# Change record structure:
# {
#   'op': 'add' | 'remove' | 'change' | 'type',
#   'path': '/Study/Design/Arms[0]/Name',
#   'old': <value or None>,
#   'new': <value or None>,
#   'note': optional explanatory string
# }


def load_json_file(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _path_join(base: str, key: str) -> str:
    if not base:
        return f"/{key}" if not key.startswith("[") else f"{key}"
    return f"{base}{key}" if key.startswith("[") else f"{base}/{key}"


def _index_path(base: str, idx: int) -> str:
    return f"{base}[{idx}]" if base else f"[{idx}]"


def _align_lists(
    a: List[Any], b: List[Any], list_key: Optional[str]
) -> List[Tuple[Optional[int], Optional[int]]]:
    """Return alignment of indices between a and b.
    If list_key provided and elements are dicts containing that key, align by key value.
    Else align positionally.
    Returns list of tuples: (index_in_a or None, index_in_b or None)."""
    if not list_key:
        pairs: List[Tuple[Optional[int], Optional[int]]] = []
        length = max(len(a), len(b))
        for i in range(length):
            pairs.append((i if i < len(a) else None, i if i < len(b) else None))
        return pairs
    # key-based
    a_map = {
        elem.get(list_key): i
        for i, elem in enumerate(a)
        if isinstance(elem, dict) and list_key in elem
    }
    b_map = {
        elem.get(list_key): i
        for i, elem in enumerate(b)
        if isinstance(elem, dict) and list_key in elem
    }
    all_keys = list(dict.fromkeys(list(a_map.keys()) + list(b_map.keys())))
    pairs = []
    used_a = set()
    used_b = set()
    for k in all_keys:
        ai = a_map.get(k)
        bi = b_map.get(k)
        if ai is not None:
            used_a.add(ai)
        if bi is not None:
            used_b.add(bi)
        pairs.append((ai, bi))
    # add remaining unmatched positional (if any)
    for i in range(len(a)):
        if i not in used_a:
            pairs.append((i, None))
    for i in range(len(b)):
        if i not in used_b:
            pairs.append((None, i))
    return pairs


def _record_type_mismatch(a: Any, b: Any, path: str, out: List[Dict[str, Any]]) -> None:
    out.append(
        {
            "op": "type",
            "path": path or "/",
            "old": type(a).__name__,
            "new": type(b).__name__,
            "note": "Type mismatch",
        }
    )


def _diff_dict(
    a: Dict[str, Any],
    b: Dict[str, Any],
    path: str,
    list_key: Optional[str],
    out: List[Dict[str, Any]],
):
    a_keys = set(a.keys())
    b_keys = set(b.keys())
    for k in sorted(a_keys - b_keys):
        out.append(
            {"op": "remove", "path": _path_join(path, k), "old": a[k], "new": None}
        )
    for k in sorted(b_keys - a_keys):
        out.append({"op": "add", "path": _path_join(path, k), "old": None, "new": b[k]})
    for k in sorted(a_keys & b_keys):
        _diff(a[k], b[k], _path_join(path, k), list_key, out)


def _diff_list(
    a: List[Any],
    b: List[Any],
    path: str,
    list_key: Optional[str],
    out: List[Dict[str, Any]],
):
    for ai, bi in _align_lists(a, b, list_key):
        if ai is not None and bi is not None:
            _diff(
                a[ai], b[bi], _index_path(path, bi if list_key else ai), list_key, out
            )
        elif ai is not None:
            out.append(
                {
                    "op": "remove",
                    "path": _index_path(path, ai),
                    "old": a[ai],
                    "new": None,
                }
            )
        elif bi is not None:
            out.append(
                {"op": "add", "path": _index_path(path, bi), "old": None, "new": b[bi]}
            )


def _diff(
    a: Any, b: Any, path: str, list_key: Optional[str], out: List[Dict[str, Any]]
):  # noqa: C901 (now simplified but keep safeguard)
    if a is None or b is None:
        # None handled naturally below; only mismatch if types differ and not both None
        if (a is None) ^ (b is None):
            _record_type_mismatch(a, b, path, out)
        return
    if a.__class__ is not b.__class__:
        _record_type_mismatch(a, b, path, out)
        return
    if isinstance(a, dict):
        _diff_dict(a, b, path, list_key, out)
    elif isinstance(a, list):
        _diff_list(a, b, path, list_key, out)
    else:
        if a != b:
            out.append({"op": "change", "path": path or "/", "old": a, "new": b})


def diff_structured(
    a: Any, b: Any, list_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    _diff(a, b, "", list_key, out)
    return out


def format_text(changes: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    counts = defaultdict(int)
    for ch in changes:
        counts[ch["op"]] += 1
    summary = f"Added: {counts['add']}  Removed: {counts['remove']}  Changed: {counts['change']}  Type Mismatch: {counts['type']}"
    lines.append(summary)
    for ch in changes:
        op = ch["op"]
        if op == "add":
            lines.append(f"+ {ch['path']}: {ch['new']!r}")
        elif op == "remove":
            lines.append(f"- {ch['path']}: {ch['old']!r}")
        elif op == "change":
            lines.append(f"~ {ch['path']}: {ch['old']!r} -> {ch['new']!r}")
        elif op == "type":
            lines.append(f"! {ch['path']}: {ch['old']} -> {ch['new']} (type mismatch)")
    return "\n".join(lines)


def summarize(changes: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = defaultdict(int)
    for ch in changes:
        counts[ch["op"]] += 1
    return {
        "added": counts["add"],
        "removed": counts["remove"],
        "changed": counts["change"],
        "typeMismatches": counts["type"],
        "total": len(changes),
    }


def group_summary(changes: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """Group counts by top-level section.

    Top-level section is the first component after the leading slash in path,
    e.g. /Study/Design/Arms[0]/Name -> Study
    Paths beginning with '[' (root-level list) are grouped under '__root_list__'.
    The root path '/' (empty) grouped under '__root__'.
    Returns mapping section -> counts dict (added, removed, changed, type, total).
    """
    section_counts: Dict[str, Dict[str, int]] = {}
    for ch in changes:
        p = ch.get("path") or "/"
        if p == "/" or p == "":
            section = "__root__"
        else:
            # strip leading slash
            if p.startswith("/"):
                p2 = p[1:]
            else:
                p2 = p
            # if path starts with '[' treat separately
            if p2.startswith("["):
                section = "__root_list__"
            else:
                section = p2.split("/", 1)[0]
        sc = section_counts.setdefault(
            section, {"add": 0, "remove": 0, "change": 0, "type": 0, "total": 0}
        )
        sc[ch["op"]] += 1
        sc["total"] += 1
    # post-process to standard names
    result: Dict[str, Dict[str, int]] = {}
    for section, c in sorted(section_counts.items()):
        result[section] = {
            "added": c["add"],
            "removed": c["remove"],
            "changed": c["change"],
            "typeMismatches": c["type"],
            "total": c["total"],
        }
    return result


def format_markdown(changes: List[Dict[str, Any]]) -> str:
    summary = summarize(changes)
    lines = [
        f"**Summary**: Added {summary['added']} · Removed {summary['removed']} · Changed {summary['changed']} · Type {summary['typeMismatches']} · Total {summary['total']}",
        "",
        "| Op | Path | Old | New |",
        "| --- | ---- | --- | --- |",
    ]

    def _fmt(v: Any) -> str:
        if isinstance(v, (dict, list)):
            s = json.dumps(v, separators=(",", ":"), ensure_ascii=False)
            if len(s) > 60:
                s = s[:57] + "…"
            return s.replace("|", "\\|")
        return (repr(v) if v is not None else "").replace("|", "\\|")

    op_map = {"add": "+", "remove": "-", "change": "~", "type": "!"}
    for ch in changes:
        op = op_map.get(ch["op"], "?")
        lines.append(
            f"| {op} | {ch['path']} | {_fmt(ch.get('old'))} | {_fmt(ch.get('new'))} |"
        )
    return "\n".join(lines)


def colorize_text(text: str, enable: bool) -> str:
    if not enable:
        return text

    def repl(line: str) -> str:
        if line.startswith("+ "):
            return f"\x1b[32m{line}\x1b[0m"
        if line.startswith("- "):
            return f"\x1b[31m{line}\x1b[0m"
        if line.startswith("~ "):
            return f"\x1b[33m{line}\x1b[0m"
        if line.startswith("! "):
            return f"\x1b[35m{line}\x1b[0m"
        if line.startswith("Added: "):
            return f"\x1b[36m{line}\x1b[0m"
        return line

    return "\n".join(repl(line) for line in text.splitlines())


def diff_usdm_json(
    file1: str, file2: str, list_key: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], str]:
    a = load_json_file(file1)
    b = load_json_file(file2)
    changes = diff_structured(a, b, list_key=list_key)
    return changes, format_text(changes)


__all__ = [
    "diff_usdm_json",
    "diff_structured",
    "format_text",
    "format_markdown",
    "summarize",
    "group_summary",
    "colorize_text",
]
