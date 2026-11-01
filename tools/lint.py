"""lint.py: the phase 7 text lint over script/ against the ROM's Japanese (the pre-commit check runs it).

    python -X utf8 tools/lint.py [-v]      # errors one per line, warnings rolled into one summary; exit 1 on any error

Per string whose English differs from the Japanese:
  - every character is in the VWF font and encodes to Shift-JIS; no Japanese left (keys with `&` are data);
  - control codes match: `\\n`, `$L`, `$Pnn`, `%s`/`%d`, a literal percent (`%%` in a printf string);
  - no ordinal suffix glued to a variable (`%dth`);
  - a non-story string never becomes empty (story blocks may reflow, D11);
  - a trailing ASCII space in the Japanese (label + value layouts) stays;
  - width: each line's px (tools/fit.py) against its box budget from tbl/windows.json `tables` (first regex over the
    id `EEEE_NAME:IIII` / `a9:XXXXXXXX` that matches). Over a measured budget = error; over a guessed one, or no
    budget, = one summary warning line (`-v` lists them);
  - stub last line: a story block's last line under 6 characters that continues a sentence (` kid."`, `area.`).
Strings still equal to the Japanese must be non-text (empty, blank, numeric, `&` keys) or listed in
script/keep_jp.txt (`ID  reason`)."""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches  # noqa: E402
import fit  # noqa: E402

KEEP = ROOT / "script" / "keep_jp.txt"
ORDINAL = re.compile(r"(%s|%d|\$P\d\d|\$L)(st|nd|rd|th)\b")
DATA = re.compile(r"^(00[01]\d|002[0-3]|008[0-4])_")  # system/data tables; MAPnn have their own rule
STUB_END = re.compile(r"^(\s|[a-z])")  # a continuation: starts with the speech indent or lowercase


def keep_list():
    if not KEEP.is_file():
        return set()
    return {ln.split()[0] for ln in KEEP.read_text(encoding="utf-8").splitlines() if ln.strip() and ln[0] != "#"}


def budgets():
    """[(match(id, jp) -> bool, variant name, variant dict)] in file order. A `tables` row is [id regex, variant]
    plus an optional condition: {"mod": [m, r]} (string index % m == r) and/or {"jp": regex} (searched in the JP)."""
    w = json.loads(fit.WINDOWS.read_text(encoding="utf-8"))
    v = w["variants"]
    out = []
    for row in w["tables"]:
        rx, name, cond = re.compile(row[0]), row[1], (row[2] if len(row) > 2 else {})
        jrx = re.compile(cond["jp"]) if "jp" in cond else None

        def match(sid, jp, rx=rx, mod=cond.get("mod"), jrx=jrx):
            if not rx.search(sid):
                return False
            if mod and int(sid.rsplit(":", 1)[1], 16 if sid.startswith("a9:") else 10) % mod[0] != mod[1]:
                return False
            return not jrx or bool(jrx.search(jp))
        out.append((match, name, v.get(name)))
    return out


def width(line):
    """px with the variables at a wide value: %s 8 W, %d / $Pnn 3 digits, $L (level) 2 digits."""
    line = re.sub(r"\$P\d\d|%d", "000", line.replace("%s", "W" * 8)).replace("$L", "00")
    return fit.px(line.replace("%%", "%"))


def strings(jp, cur):
    """Yield (id, jp, en, is_story) for every string of script/ (BBQ then arm9)."""
    for stem in sorted(k for k in cur if k != "arm9"):
        story = not DATA.match(stem) and not re.search(r"_MAP\d\d$", stem)
        for i, (j, e) in enumerate(zip(jp[stem], cur[stem])):
            yield f"{stem}:{i:04d}", j, e, story
    for at, j in jp["arm9"]:
        yield f"a9:{at}", j, cur["arm9"].get(at, j), False


def lint(jp=None, cur=None, keep=None):
    """(errors, warnings): errors a list of lines, warnings {kind: [lines]}."""
    jp = batches.jp_tables() if jp is None else jp
    cur = batches.current() if cur is None else cur
    keep = keep_list() if keep is None else keep
    rules, t = budgets(), fit.table()
    errs, warns = [], {}
    for sid, j, e, story in strings(jp, cur):
        if j == e:
            if batches.is_text(j) and sid not in keep:
                errs.append(f"{sid}: still Japanese (translate it or list it in script/keep_jp.txt): {j!r}")
            continue
        if batches.JP_RE.search(e) and "&" not in e and sid not in keep:
            errs.append(f"{sid}: Japanese left: {e!r}")
        bad = sorted({c for c in e if c != "\n" and ord(c) not in t and not batches.JP_RE.match(c)})
        if bad:
            errs.append(f"{sid}: characters the font lacks: {''.join(bad)!r}")
        try:
            e.encode("cp932")
        except UnicodeEncodeError as x:
            errs.append(f"{sid}: not Shift-JIS: {x}")
        tj, te = batches.codes(j, e)
        if tj != te:
            errs.append(f"{sid}: codes {tj} != {te}: {e!r}")
        if ORDINAL.search(e):
            errs.append(f"{sid}: ordinal suffix glued to a variable: {e!r}")
        if not e and j.strip() and not story:
            errs.append(f"{sid}: empty English for {j!r}")
        if j.endswith(" ") and not e.endswith(" ") and not story:  # story lines: a stray JP space, nothing follows
            errs.append(f"{sid}: lost the trailing space of {j!r}: {e!r}")
        lim = name = None
        for match, n, var in rules:
            if match(sid, j):
                name, lim = n, var
                break
        if name == "dev":  # developer menus and test rooms: the release never shows them
            continue
        for ln in e.split("\n"):
            w = width(ln)
            if lim is None:
                warns.setdefault(f"no measured box ({name})", []).append(f"{sid}: {w}px {ln!r}")
            elif w > lim["px"]:
                msg = f"{sid}: {w}px > {name} {lim['px']}px: {ln!r}"
                if lim.get("measured"):
                    errs.append(msg)
                else:
                    warns.setdefault(f"over a guessed budget", []).append(msg)
    errs += stubs(jp, cur)
    errs += honorifics(jp, cur)
    return errs, warns


def honorifics(jp, cur):
    """Story blocks whose English dropped a -san/-kun/-chan or 閣下 (batches.honorifics)."""
    out = []
    for stem in sorted(k for k in cur if k != "arm9"):
        for form, idx in batches.blocks(stem, jp[stem]):
            j, e = "".join(jp[stem][i] for i in idx), " ".join(cur[stem][i] for i in idx)
            if not batches.JP_RE.search(e):  # Japanese left is reported (or keep-listed) above
                out += [f"{stem}:{idx[0]:04d}: {p}: {e!r}" for p in batches.honorifics(j, e)]
    return out


def stubs(jp, cur):
    """Story blocks whose last English line is a stub (under 6 characters) continuing the sentence before it."""
    out = []
    for stem in sorted(k for k in cur if k != "arm9"):
        if DATA.match(stem) or re.search(r"_MAP\d\d$", stem):
            continue
        strs = cur[stem]
        for form, idx in batches.blocks(stem, jp[stem]):
            en = [strs[i] for i in idx if strs[i].strip()]
            if form == "name" or len(en) < 2:
                continue
            last = en[-1]
            if len(last.strip()) < 6 and STUB_END.match(last) and re.search(r"[A-Za-z]", last) \
                    and not re.search(r"[.!?\"]$", en[-2].rstrip()):
                out.append(f"{stem}:{idx[0]:04d}: stub last line {last!r} after {en[-2]!r}")
    return out


if __name__ == "__main__":
    errs, warns = lint()
    for e in errs:
        print(e)
    for kind, rows in warns.items():
        print(f"warning: {len(rows)} lines {kind}" + ("" if "-v" in sys.argv else " (-v lists them)"))
        if "-v" in sys.argv:
            for r in rows:
                print("  " + r)
    print(f"{len(errs)} errors")
    sys.exit(1 if errs else 0)
