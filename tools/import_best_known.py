"""Convert Table 1 of Friedman's survey (Electron. J. Combin. DS#7, 2009 revision) to JSON.

The table lists best known upper bounds on s(n), the side of the smallest square holding n unit
squares, for n <= 100. Exact expressions are evaluated and checked against the printed 4-digit
approximations. Optimality marks are recorded as stated in that survey only.

Example::

    uv run python tools/import_best_known.py /tmp/ds7-2009.html \
        --output src/asquerix/lab/data/best-known-upper-bounds.json
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
from pathlib import Path

ROW = re.compile(r"<tr align=center\s*><td>(?P<n>[0-9]+(?:-[0-9]+)?)\s*<td\s+align=right>(?P<value>.*?)<td>(?P<optimal>.*?)<td>(?P<figure>.*?)<td>(?P<author>.*?)</tr>",
                 re.S | re.I)


def text(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def evaluate(expression: str) -> float:
    """Evaluate the table's sums: "p", "p/q", "p/√r", "p/q√r" = (p/q)√r and "√r/q"."""
    total = 0.0
    for term in expression.replace(" ", "").split("+"):
        if term.startswith("(") or "-" in term:
            raise ValueError(f"unsupported term {term!r}")
        match = re.fullmatch(r"(\d+)/√(\d+)", term)
        if match:
            total += int(match[1]) / math.sqrt(int(match[2]))
            continue
        match = re.fullmatch(r"(\d+)(?:/(\d+))?(?:√(\d+))?", term)
        if match:
            coefficient = int(match[1]) / (int(match[2]) if match[2] else 1)
            total += coefficient * (math.sqrt(int(match[3])) if match[3] else 1.0)
            continue
        match = re.fullmatch(r"(\d+)?√(\d+)(?:/(\d+))?", term)
        if match:
            total += (int(match[1]) if match[1] else 1) * math.sqrt(int(match[2])) / (int(match[3]) if match[3] else 1)
            continue
        raise ValueError(f"unsupported term {term!r}")
    return total


def parse(source: str) -> list[dict]:
    start = source.index('NAME="appendix"')
    table = source[start:source.index("Table 1. Best known upper bounds", start)]
    entries = []
    for row in ROW.finditer(table):
        first, _, last = row["n"].partition("-")
        cell = row["value"].replace("&radic;", "√")
        expression, _, approximation = cell.partition('<img')
        expression = text(expression)
        printed = text(approximation.split(">", 1)[1]) if approximation else ""
        if expression and printed:
            value = evaluate(expression)
            # Upper-bound approximations are printed rounded up to four decimals.
            if not 0 <= float(printed) - value < 1e-4:
                raise ValueError(f"n={row['n']}: {expression} = {value} disagrees with printed {printed}")
            kind = "exact-expression"
        elif expression:
            value, kind = float(expression), "exact-integer" if expression.isdigit() else "printed-decimal"
        else:
            value, kind = float(printed), "printed-decimal"
        author = text(row["author"]) or None
        figure = text(row["figure"]) or None
        for n in range(int(first), int(last or first) + 1):
            entries.append({"n": n, "upper_bound": value, "value_kind": kind, "expression": expression or None,
                            "printed": printed or expression, "optimal_in_source": "check.gif" in row["optimal"],
                            "author": author, "figure": figure})
    if [entry["n"] for entry in entries] != list(range(1, 101)):
        raise ValueError("Table 1 must cover n = 1..100 exactly once")
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("html", type=Path)
    parser.add_argument("--output", type=Path, default=Path("src/asquerix/lab/data/best-known-upper-bounds.json"))
    args = parser.parse_args()
    raw = args.html.read_bytes()
    document = {
        "schema": "asquerix-best-known-upper-bounds-v1",
        "quantity": "s(n): side of the smallest square containing n non-overlapping unit squares",
        "source": {"title": "Packing Unit Squares in Squares: A Survey and New Results", "author": "Erich Friedman",
                   "publication": "The Electronic Journal of Combinatorics, Dynamic Survey DS#7", "revision_year": 2009,
                   "table": "Table 1. Best known upper bounds for s(n)", "citation": "The Electronic Journal of Combinatorics (2009), DS#7", "journal_url": "http://www.combinatorics.org/",
                   "imported_file": args.html.name, "imported_sha256": hashlib.sha256(raw).hexdigest()},
        "caveats": ["Values and optimality marks are as stated in the 2009 revision; later results may improve or settle them.",
                    "printed-decimal values are the source's 4-digit approximations, which this table rounds up (checked against every exact expression), so they remain upper bounds.",
                    "Reference values are for display only and are never given to the search or the evaluator."],
        "entries": parse(raw.decode("latin-1")),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved {len(document['entries'])} entries to {args.output}")


if __name__ == "__main__":
    main()
