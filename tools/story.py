"""story.py: story-pass chapter files -- every story block of 3 consecutive stages, in file order.

    python -X utf8 tools/story.py [OUT_DIR]   (default work/qa/story/chapters)

Entry: `>> first-id | speaker | JP lines joined by " / "` then `   EN lines joined by " / "` (one speech, or prose
to a sentence end). A page that borrows a line from another page (`pages.py`, D23) follows as
`   [page in game 605,606,465,607: EN / EN ...]`, the order the player reads it.
A stage's files run STAGE (cards, briefings), EV events, then BATTLE/MILITARY (in-battle lines).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batches  # noqa: E402
import pages  # noqa: E402

EZ = Path(__file__).resolve().parents[1] / "work" / "ez"  # original BBQ files (pages.py reads the same)
PER = 3  # stages per chapter: ~45 KB, one reviewer read
ORDER = {"STAGE": 0, "EV": 1, "BATTLE": 2, "MILITARY": 3}


def stage_files(jp):
    st = {}
    for stem in jp:
        m = re.match(r"\d{4}_ST(\d\d)(STAGE|EV|BATTLE|MILITARY)", stem)
        if m:
            st.setdefault(int(m.group(1)), []).append((ORDER[m.group(2)], stem))
    return {n: [s for _, s in sorted(v)] for n, v in st.items()}


def borrowed(stem, js):
    """{first id of a page: page} for pages that borrow a line from elsewhere (pages.py; its page split is a
    heuristic and misses some lines, so these only annotate the complete line blocks)."""
    d = (EZ / f"{stem[:4]}.bin").read_bytes()
    out = {}
    for p in pages.pages(d):
        if pages.odd(p) and all(i < len(js) for i in p) and any(batches.is_text(js[i]) for i in p):
            out.setdefault(p[0], p)
    return out


def chapter(stems, jp, cur):
    out = []
    for stem in stems:
        js, es = jp[stem], cur[stem]
        out.append(f"## {stem}")
        odd = borrowed(stem, js)
        speaker, cur_ = "", []

        def flush():
            if cur_:
                j = " / ".join(js[i] for i in cur_).replace("\n", "\\n")
                e = " / ".join(es[i] or "<empty>" for i in cur_).replace("\n", "\\n")
                sp = speaker if js[cur_[0]].startswith("「") else ""
                out.append(f">> {stem[:4]}:{cur_[0]:04d} | {sp} | {j}\n   {e}")
                for i in cur_:
                    if i in odd:
                        p = odd.pop(i)
                        out.append(f"   [page in game {','.join(map(str, p))}: "
                                   + " / ".join(es[k] or "<empty>" for k in p) + "]")
                cur_.clear()

        for i, s in enumerate(js):
            nxt = js[i + 1] if i + 1 < len(js) else ""
            if not batches.is_text(s):
                flush()
                continue
            if not cur_ and not s.startswith(("「", "　")) and nxt.startswith("「") and len(s) <= 12 \
                    and not s.rstrip().endswith(("。", "、")) and not re.search("」.", nxt):
                flush()
                speaker = es[i]  # name label: names every speech until the next label or narration
                continue
            if s.startswith("「") or (cur_ and js[cur_[0]].startswith("「") and not s.startswith("　")):
                flush()
                if not s.startswith("「"):
                    speaker = ""
            elif not cur_:
                speaker = ""
            cur_.append(i)
            speech = js[cur_[0]].startswith("「")
            if s.rstrip().endswith("」" if speech else "。") or len(cur_) >= 8:
                flush()
        flush()
    return "\n".join(out) + "\n"


def main(out=Path("work/qa/story/chapters")):
    jp, cur = batches.jp_tables(), batches.current()
    st = stage_files(jp)
    nums = sorted(st)
    out.mkdir(parents=True, exist_ok=True)
    for k in range(0, len(nums), PER):
        grp = nums[k:k + PER]
        name = f"ch{k // PER + 1:02d}_st{grp[0]:02d}-{grp[-1]:02d}.txt"
        (out / name).write_text(chapter([s for n in grp for s in st[n]], jp, cur), encoding="utf-8")
        print(name)


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("work/qa/story/chapters"))
