"""ctx.py: JP/EN lines around a string id, plus every other string with the same Japanese (its copies) and their px.

    python -X utf8 tools/ctx.py 0228:0739 [N]     # N lines either side (default 5)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batches  # noqa: E402
import fit  # noqa: E402

jp, cur = batches.jp_tables(), batches.current()
sid = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
a, b = sid.split(":")
b = int(b)
stem = next(k for k in jp if k.startswith(a + "_"))
print(stem)
for i in range(max(0, b - n), min(len(jp[stem]), b + n + 1)):
    print(f"{'>' if i == b else ' '}{i:04d} {jp[stem][i]!r:40} {fit.px(cur[stem][i]):3}px {cur[stem][i]!r}")
t = jp[stem][b]
copies = [f"{s}:{i:04d} {cur[s][i]!r}" for s in sorted(k for k in jp if k != "arm9")
          for i, x in enumerate(jp[s]) if x == t and (s, i) != (stem, b)]
if copies:
    print("same JP elsewhere (a copy shares the EN only if the scene is the same):")
    print("\n".join("  " + c for c in copies))
