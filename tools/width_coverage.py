"""List unresolved width coverage without running the glossary/translation checks.

    python -X utf8 tools/width_coverage.py [--ids]

Read-only diagnostic; exit 1 while any changed player-facing line lacks a measured budget.
This deliberately does not infer a budget from the translated line's current length.
"""
import sys
from collections import defaultdict

import batches
import lint


def unresolved(jp=None, cur=None):
    jp = batches.jp_tables() if jp is None else jp
    cur = batches.current() if cur is None else cur
    problems = lint.coverage_errors(jp, cur)
    if problems:
        raise ValueError("\n".join(problems))
    rules = lint.budgets()
    missing = defaultdict(list)
    for sid, original, translated, _ in lint.strings(jp, cur):
        if original == translated:
            continue
        name, variant = next(((n, v) for match, n, v in rules if match(sid, original)), (None, None))
        if name == "dev" or lint.width_excluded(variant):
            continue
        if variant is None or not variant.get("measured"):
            missing[name].extend((sid, line) for line in translated.split("\n"))
    return dict(missing)


if __name__ == "__main__":
    missing = unresolved()
    for name, rows in missing.items():
        print(f"{name}: {len(rows)} lines; first {rows[0][0]}")
        if "--ids" in sys.argv:
            for sid, line in rows:
                print(f"  {sid}\t{line}")
    total = sum(map(len, missing.values()))
    print(f"{total} lines require measured budgets or proven exclusions with reasons")
    sys.exit(bool(total))
