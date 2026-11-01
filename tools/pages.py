"""pages.py: message pages as the script VM builds them, to catch lines a page borrows from elsewhere.

A message page pushes its lines last-first as `push-str op, source line, string id, 0x1280e` word groups (the op
is 0x12000 for a str16 literal, 0x12400 for str32; bbq.widen may change it, so read the original files in work/ez).
Most pages are a run of consecutive ids; some reuse one line of another page (ST02 tutorial: 0450-0452 open with
0412 "この状態で、"). A reflowed translation of the original run then reads wrong on the borrowing page.

    python -X utf8 tools/pages.py [EZ ...]          # pages whose ids are not one consecutive run, JP | EN
    python -X utf8 tools/pages.py --all 93          # every page of one table"""
import json
import re
import sys
from pathlib import Path

from bbq import sections, strtab
from vmdump import code

ROOT = Path(__file__).resolve().parents[1]
END = 0x1280e
DEV = re.compile(r"^00(1[7-9]|2\d|3[0-8])_|_BATTLE\d\d$|^0084_")  # developer rooms (batches.DEV)
PUSH = {0x10000 | t << 10 for t in range(8, 13)}  # push a str16..str256 literal (bbq.SIZES); 0x12000/0x12400 here


def pages(d):
    """[[string id, ...] in display order] for every page of a BBQ file's script (empty if it has none)."""
    if not any(s["type"] == 6 for s in sections(d)):
        return []
    w = code(d)
    out, cur, last = [], [], -99
    for k in range(len(w) - 3):
        if w[k] in PUSH and w[k + 3] == END:
            if k - last > 6 and cur:
                out.append(cur[::-1])
                cur = []
            cur.append(w[k + 2])
            last = k
    if cur:
        out.append(cur[::-1])
    return out


def odd(page):
    return any(b != a + 1 for a, b in zip(page, page[1:]))


def shape(jp, en):
    """Problems with one line's speech shape: a borrowed line must open, continue and close a quote the way its
    Japanese does, or the borrowing page shows a stray or missing quote mark."""
    out = []
    body = jp.strip("　 ")
    if "「" in body[1:] or "」" in body[:-1]:  # an inline quote (「３」だ。), not speech
        return out
    if body.startswith("「") != en.startswith('"'):
        out.append("opening quote")
    if jp.startswith("　") and not jp.startswith("　　") and body and not en.startswith(" "):
        out.append("continuation indent")  # one fullwidth space = speech continuation; more = centring
    if body.endswith("」") != en.rstrip().endswith('"'):
        out.append("closing quote")
    return out


def shape_problems(original=None):
    """[(table, id, problem, jp, en)] for every line of a borrowing page whose speech shape differs from its JP.
    original = {ez index: original file bytes} (default: work/ez)."""
    ez = ROOT / "work" / "ez"
    out = []
    for f in files():
        idx = int(f.name[:4])
        en = json.loads(f.read_text(encoding="utf-8"))["strings"]
        d = original[idx] if original else (ez / f"{idx:04d}.bin").read_bytes()
        jp = [s.decode("cp932", "replace") for s in strtab(d)[1]]
        ids = sorted({i for p in pages(d) if odd(p) for i in p if i < len(en)})
        for i in ids:
            for prob in shape(jp[i], en[i]):
                out.append((f.stem, i, prob, jp[i].rstrip("　"), en[i]))
    return out


def files():
    return sorted((ROOT / "script" / "bbq").glob("*.json"))


def main(argv):
    if "--shape" in argv:
        bad = shape_problems()
        for row in bad:
            print(*row, sep="\t")
        print(f"{len(bad)} borrowed lines out of shape", file=sys.stderr)
        return 1 if bad else 0
    show_all, narration = "--all" in argv, "--narration" in argv
    want = {int(a) for a in argv if a.isdigit()}
    ez = ROOT / "work" / "ez"
    n = 0
    for f in files():
        idx = int(f.name[:4])
        if want and idx not in want:
            continue
        en = json.loads(f.read_text(encoding="utf-8"))["strings"]
        d = (ez / f"{idx:04d}.bin").read_bytes()
        jp = [s.decode("cp932", "replace").rstrip("　 ") for s in strtab(d)[1]]
        ps = pages(d)
        if narration and DEV.search(f.stem):
            continue
        for p in ps:
            if narration and any(c in jp[i] for i in p if i < len(jp) for c in "「」"):
                continue  # speech: battle quotes reuse whole self-contained lines, checked by shape()
            if (show_all or odd(p)) and all(i < len(en) for i in p):
                n += 1
                print(f"{f.stem} {p}")
                for i in p:
                    print(f"    {i:4d} {jp[i]:<16}\t| {en[i]}")
                if show_all:
                    continue
                for q in ps:  # every other page that shows one of these lines
                    if q != p and set(q) & set(p):
                        print(f"  also {q}: " + " / ".join(en[i] for i in q if i < len(en)))
    print(f"{n} pages", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])
