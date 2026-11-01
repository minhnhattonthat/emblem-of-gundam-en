"""pairs.py: reviewer input -- the JP/EN pairs of translated batches, one block (speech or sentence) per entry.

    python -X utf8 tools/pairs.py OUT.txt b010 b011 ...

Entry: `>> first-id [form] (speaker) | JP lines joined by " / "` then `   EN lines joined by " / "`.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batches  # noqa: E402


def pairs(names):
    out = []
    for name in names:
        rows = batches.read_in(name)
        en, _ = batches.read_out(name)
        out.append(f"## {name}")
        cur = []

        def flush():
            if cur:
                i, sp, form = cur[0][:3]
                kind = re.sub(r"\d+/\d+$", "", form)
                jp = " / ".join(r[4].replace("\n", "\\n") for r in cur)
                e = " / ".join((en.get(r[0], "<MISSING>") or "<empty>").replace("\n", "\\n") for r in cur)
                out.append(f">> {i} [{kind}]{f' ({sp})' if sp else ''} | {jp}\n   {e}")
                cur.clear()

        for r in rows:
            m = re.match(r"\D+(\d+)/", r[2])
            if not m or m.group(1) == "1":
                flush()
            cur.append(r)
        flush()
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    Path(sys.argv[1]).write_text(pairs(sys.argv[2:]), encoding="utf-8", newline="\n")
    print("wrote", sys.argv[1])
