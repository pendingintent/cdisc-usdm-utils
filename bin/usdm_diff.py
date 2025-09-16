#!/usr/bin/env python3
"""Deprecated script: use the enriched CLI instead.

This legacy `bin/usdm_diff.py` utility has been retired in favor of the
primary CLI commands that provide richer, object-centric diff features:

  1. python -m cdisc_usdm_utils diff <old.json> <new.json> --objects-only \
         [--object-id-key id --object-id-filter REF]
     Produces a summarized object-level diff (add/remove/change) with
     optional filtering.

  2. python -m cdisc_usdm_utils diff-html <old.json> <new.json> \
         --output diff.html [--list-key reference]
     Generates a side-by-side HTML report for changed objects.

  3. Lightweight scripts (optional):
       bin/json_compare.py  (structured change records / JSON output)
       bin/comparator.py    (normalization equality + diagnostics)

Exit codes of this stub:
  0 – Always, after printing deprecation message (no diff performed)

Rationale: The CLI now handles object grouping, ID filtering, list
alignment, and multiple output formats (text, HTML) more effectively
than this older normalization diff.
"""
from __future__ import annotations
import sys

DEPRECATION_MESSAGE = """
[DEPRECATED] bin/usdm_diff.py has been retired.

Please use one of the new commands instead:
  python -m cdisc_usdm_utils diff OLD.json NEW.json --objects-only
  python -m cdisc_usdm_utils diff-html OLD.json NEW.json --output diff.html

For help:
  python -m cdisc_usdm_utils --help
""".strip()


def main() -> int:
    print(DEPRECATION_MESSAGE, file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
