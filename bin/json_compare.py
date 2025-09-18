#!/usr/bin/env python3
"""Lightweight JSON structural comparator.

Loads two JSON files into Python dictionaries and recursively compares them,
emitting a simple text report of differences:
  + add, - remove, ~ change, ! type mismatch

This is intentionally standalone (no Click dependency) for quick ad-hoc use.

Usage:
  python bin/json_compare.py old.json new.json
  python bin/json_compare.py old.json new.json --max-list 10

Exit code is always 0 (non-breaking); adapt as needed.
"""
from __future__ import annotations
import json
import argparse
from pathlib import Path
from typing import Any, List, Dict, Tuple, Optional
import sys

DiffRecord = Dict[str, Any]


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_scalar(v: Any) -> bool:
    return isinstance(v, (str, int, float, bool)) or v is None


def diff_values(
    a: Any, b: Any, path: str, out: List[DiffRecord], list_key: Optional[str] = None
):
    if type(a) != type(b):  # noqa: E721
        out.append(
            {
                "op": "type",
                "path": path or "/",
                "oldType": type(a).__name__,
                "newType": type(b).__name__,
                "old": a,
                "new": b,
            }
        )
        return
    if isinstance(a, dict):
        diff_dicts(a, b, path, out, list_key=list_key)
    elif isinstance(a, list):
        diff_lists(a, b, path, out, list_key=list_key)
    else:  # scalar
        if a != b:
            out.append(
                {
                    "op": "change",
                    "path": path or "/",
                    "old": a,
                    "new": b,
                }
            )


def diff_dicts(
    a: Dict[str, Any],
    b: Dict[str, Any],
    path: str,
    out: List[DiffRecord],
    list_key: Optional[str] = None,
):
    a_keys = set(a.keys())
    b_keys = set(b.keys())
    for k in sorted(a_keys - b_keys):
        out.append(
            {
                "op": "remove",
                "path": f"{path}/{k}" if path else f"/{k}",
                "old": a[k],
            }
        )
    for k in sorted(b_keys - a_keys):
        out.append(
            {
                "op": "add",
                "path": f"{path}/{k}" if path else f"/{k}",
                "new": b[k],
            }
        )
    for k in sorted(a_keys & b_keys):
        sub_path = f"{path}/{k}" if path else f"/{k}"
        diff_values(a[k], b[k], sub_path, out, list_key=list_key)


def diff_lists(
    a: List[Any],
    b: List[Any],
    path: str,
    out: List[DiffRecord],
    list_key: Optional[str] = None,
):
    # If list_key provided and both lists look like list-of-dicts with that key, align by key.
    if list_key and _is_alignable(a, b, list_key):
        a_map = {
            str(item[list_key]): item
            for item in a
            if isinstance(item, dict) and list_key in item
        }
        b_map = {
            str(item[list_key]): item
            for item in b
            if isinstance(item, dict) and list_key in item
        }
        a_keys = set(a_map.keys())
        b_keys = set(b_map.keys())
        for key in sorted(a_keys - b_keys):
            out.append(
                {
                    "op": "remove",
                    "path": f"{path}[{key}]" if path else f"/[{key}]",
                    "old": a_map[key],
                }
            )
        for key in sorted(b_keys - a_keys):
            out.append(
                {
                    "op": "add",
                    "path": f"{path}[{key}]" if path else f"/[{key}]",
                    "new": b_map[key],
                }
            )
        for key in sorted(a_keys & b_keys):
            sub_path = f"{path}[{key}]" if path else f"/[{key}]"
            diff_values(a_map[key], b_map[key], sub_path, out, list_key=list_key)
        return
    # Fallback positional comparison
    max_len = max(len(a), len(b))
    for idx in range(max_len):
        sub_path = f"{path}[{idx}]" if path else f"/[{idx}]"
        if idx >= len(a):
            out.append(
                {
                    "op": "add",
                    "path": sub_path,
                    "new": b[idx],
                }
            )
            continue
        if idx >= len(b):
            out.append(
                {
                    "op": "remove",
                    "path": sub_path,
                    "old": a[idx],
                }
            )
            continue
        diff_values(a[idx], b[idx], sub_path, out, list_key=list_key)


def _is_alignable(a: List[Any], b: List[Any], key: str) -> bool:
    if not a and not b:
        return False
    samples = [*(a[:10]), *(b[:10])]
    dicts = [x for x in samples if isinstance(x, dict) and key in x]
    if not dicts:
        return False

    # ensure uniqueness of key values in each list
    def unique_values(lst: List[Any]) -> bool:
        vals = [str(x[key]) for x in lst if isinstance(x, dict) and key in x]
        return len(vals) == len(set(vals))

    return unique_values(a) and unique_values(b)


def summarize(changes: List[DiffRecord]) -> Dict[str, int]:
    s = {"add": 0, "remove": 0, "change": 0, "type": 0}
    for c in changes:
        op = c["op"]
        if op in s:
            s[op] += 1
    s["total"] = sum(s.values())
    return s


def format_text(changes: List[DiffRecord], max_list: Optional[int]) -> str:
    lines: List[str] = []
    for c in changes:
        op = c["op"]
        marker = {"add": "+", "remove": "-", "change": "~", "type": "!"}.get(op, "?")
        path = c["path"]
        if op == "change":
            lines.append(f"{marker} {path}: {c['old']} -> {c['new']}")
        elif op == "type":
            lines.append(f"{marker} {path}: {c['oldType']} -> {c['newType']}")
        elif op == "add":
            val = c.get("new")
            lines.append(f"{marker} {path}: +{_val_repr(val, max_list)}")
        elif op == "remove":
            val = c.get("old")
            lines.append(f"{marker} {path}: -{_val_repr(val, max_list)}")
    return "\n".join(lines)


def _val_repr(v: Any, max_list: Optional[int]) -> str:
    if is_scalar(v):
        return json.dumps(v)
    if isinstance(v, list):
        if max_list is not None and len(v) > max_list:
            return f"[... {len(v)} items ...]"
        return json.dumps(v)
    if isinstance(v, dict):
        keys = list(v.keys())
        if max_list is not None and len(keys) > max_list:
            shown = keys[:max_list]
            # Need to escape closing brace in f-string segment
            return "{" + ", ".join(shown) + f", ... {len(keys)} keys ...}}"  # type: ignore
        return "{" + ", ".join(keys) + "}"
    return json.dumps(v)


def main():
    ap = argparse.ArgumentParser(description="Lightweight JSON structural comparator")
    ap.add_argument("old", help="Old (baseline) JSON file")
    ap.add_argument("new", help="New (comparison) JSON file")
    ap.add_argument(
        "--max-list", type=int, default=20, help="Limit displayed list/dict detail"
    )
    ap.add_argument(
        "--json", action="store_true", help="Emit machine JSON output instead of text"
    )
    ap.add_argument(
        "--list-key",
        help="Align list of objects by this key to ignore positional reordering",
    )
    args = ap.parse_args()

    a = load_json(args.old)
    b = load_json(args.new)
    changes: List[DiffRecord] = []
    diff_values(a, b, "", changes, list_key=args.list_key)
    summ = summarize(changes)

    try:
        if args.json:
            payload = {
                "summary": summ,
                "changes": changes,
            }
            print(json.dumps(payload, indent=2))
        else:
            print(
                f"Added: {summ['add']} Removed: {summ['remove']} Changed: {summ['change']} Type: {summ['type']} Total: {summ['total']}"
            )
            if changes:
                print(format_text(changes, args.max_list))
    except BrokenPipeError:  # piping through head/less
        try:
            sys.stdout.close()
        except Exception:
            pass
    except IOError as e:  # pragma: no cover
        if getattr(e, "errno", None) != 32:
            raise


if __name__ == "__main__":  # pragma: no cover
    main()
