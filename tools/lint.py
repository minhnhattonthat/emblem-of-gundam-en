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
    budget, = error; diagnostic callers can separately audit content with require_measured=False;
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
SPACE_EXCEPTIONS = {
    # Quoted terminology inside narration, not a speaker's dialogue (D20).
    "0186_ST28MILITARY:0168": "Alex acronym expansion: (Armor / Layered / EXamination).",
}


def keep_list():
    if not KEEP.is_file():
        return set()
    return {ln.split()[0] for ln in KEEP.read_text(encoding="utf-8").splitlines() if ln.strip() and ln[0] != "#"}


def budgets():
    """[(match(id, jp) -> bool, variant name, variant dict)] in file order. A `tables` row is [id regex, variant]
    plus optional conditions: mod = [m, r], ids = exact numeric indices, jp = source regex."""
    w = json.loads(fit.WINDOWS.read_text(encoding="utf-8"))
    v = w["variants"]
    out = []
    for row in w["tables"]:
        rx, name, cond = re.compile(row[0]), row[1], (row[2] if len(row) > 2 else {})
        jrx = re.compile(cond["jp"]) if "jp" in cond else None

        def match(sid, jp, rx=rx, mod=cond.get("mod"), ids=cond.get("ids"), jrx=jrx):
            if not rx.search(sid):
                return False
            if mod and int(sid.rsplit(":", 1)[1], 16 if sid.startswith("a9:") else 10) % mod[0] != mod[1]:
                return False
            if ids is not None and int(sid.rsplit(":", 1)[1], 16 if sid.startswith("a9:") else 10) not in ids:
                return False
            return not jrx or bool(jrx.search(jp))
        out.append((match, name, v.get(name)))
    return out


def width(line):
    """px with the variables at a wide value: %s 8 W, %d / $Pnn 3 digits, $L (level) 2 digits."""
    line = re.sub(r"\$P\d\d|%d", "000", line.replace("%s", "W" * 8)).replace("$L", "00")
    return fit.px(line.replace("%%", "%"))


def width_excluded(variant):
    """Only explicit, evidenced non-player classifications waive width, not any other lint rule."""
    if not variant or not variant.get("excluded"):
        return False
    if not variant.get("reason") or not variant.get("evidence"):
        raise ValueError("width exclusion requires a reason and evidence")
    return True


def strings(jp, cur):
    """Yield (id, jp, en, is_story) for every string of script/ (BBQ then arm9)."""
    for stem in sorted(k for k in cur if k != "arm9"):
        story = not DATA.match(stem) and not re.search(r"_MAP\d\d$", stem)
        for i, (j, e) in enumerate(zip(jp[stem], cur[stem])):
            yield f"{stem}:{i:04d}", j, e, story
    for at, j in jp["arm9"]:
        yield f"a9:{at}", j, cur["arm9"].get(at, j), False


def lint(jp=None, cur=None, keep=None, require_measured=True):
    """(errors, warnings). The phase gate requires measured coverage; diagnostic callers may audit other rules
    with require_measured=False, which is never sufficient to certify phase 7."""
    jp = batches.jp_tables() if jp is None else jp
    cur = batches.current() if cur is None else cur
    keep = keep_list() if keep is None else keep
    coverage = coverage_errors(jp, cur)
    if coverage:
        return coverage, {}
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
        if not story and j.strip():
            for side, pattern in [("leading", r"^[ \u3000]+"), ("trailing", r"[ \u3000]+$")]:
                padding = re.search(pattern, j)
                expected = padding[0].replace("\u3000", " ") if padding else ""
                if expected and not (e.startswith(expected) if side == "leading" else e.endswith(expected)):
                    errs.append(f"{sid}: lost {side} layout spaces ({len(expected)} ASCII required): {e!r}")
        lim = name = None
        for match, n, var in rules:
            if match(sid, j):
                name, lim = n, var
                break
        if name == "dev" or width_excluded(lim):  # proven non-player destinations only
            continue
        if lim and "bytes" in lim and len(e.encode("cp932", errors="replace")) > lim["bytes"]:
            errs.append(f"{sid}: exceeds {name} {lim['bytes']}-byte native text field")
        for ln in e.split("\n"):
            w = width(ln)
            if lim is None or not lim.get("measured"):
                msg = f"{sid}: unmeasured width budget ({name}): {w}px {ln!r}"
                if require_measured:
                    errs.append(msg)
                else:
                    warns.setdefault(f"no measured box ({name})", []).append(msg)
            if lim is not None and w > lim["px"]:
                msg = f"{sid}: {w}px > {name} {lim['px']}px: {ln!r}"
                if lim.get("measured"):
                    errs.append(msg)
                else:
                    warns.setdefault(f"over a guessed budget", []).append(msg)
    errs += stubs(jp, cur)
    errs += honorifics(jp, cur)
    errs += stage_names(jp, cur)
    errs += block_checks(jp, cur, keep)
    errs += continuation_spaces(jp, cur)
    return errs, warns


def coverage_errors(jp, cur):
    """Reject missing/extra tables or IDs before zip/get can silently skip them."""
    out = []
    if set(jp) != set(cur):
        out.append(f"table coverage mismatch: {sorted(set(jp) ^ set(cur))}")
    for stem in set(jp) & set(cur):
        if stem == "arm9":
            expected = {at for at, _ in jp[stem]}
            if expected != set(cur[stem]):
                out.append(f"arm9 ID coverage mismatch: {sorted(expected ^ set(cur[stem]))}")
        elif len(jp[stem]) != len(cur[stem]):
            out.append(f"{stem}: ID coverage mismatch ({len(jp[stem])} != {len(cur[stem])})")
    return out


def continuation_spaces(jp, cur):
    """D11: nonempty English speech continuations have one ASCII space, after reflow.

    A Japanese quote can also introduce a term in narration. Only blocks with the source speech
    indentation convention qualify; the documented acronym exception retains its prose layout.
    """
    out = []
    for stem in sorted(k for k in cur if k != "arm9"):
        for form, idx in batches.blocks(stem, jp[stem]):
            if form != "dlg" or not any(jp[stem][i].startswith(("\u3000", " ")) for i in idx[1:]):
                continue
            lines = [(i, cur[stem][i]) for i in idx if cur[stem][i].strip()]
            for i, line in lines[1:]:
                sid = f"{stem}:{i:04d}"
                if sid not in SPACE_EXCEPTIONS and (not line.startswith(" ") or line.startswith("  ")):
                    out.append(f"{sid}: speech continuation requires one leading ASCII space: {line!r}")
    return out


def block_checks(jp, cur, keep):
    """Reflow may blank a line, never an entire source block; glossary follows that same block."""
    out, terms = [], batches.glossary()
    for stem in sorted(k for k in cur if k != "arm9"):
        covered = set()
        for form, idx in batches.blocks(stem, jp[stem]):
            covered.update(idx)
            sid = f"{stem}:{idx[0]:04d}"
            j = "".join(jp[stem][i] for i in idx)
            lines = [cur[stem][i] for i in idx]
            if not any(e.strip() for e in lines) and sid not in keep:
                out.append(f"{sid}: empty English block for {j!r}")
            if not any(batches.JP_RE.search(e) for e in lines):
                out.extend(f"{sid}: {p}" for p in batches.glossary_errors(j, lines, terms, short=form == "menu"))
        # Punctuation-only utterances (e.g. 「……」) are not Japanese-letter matches, so the batch
        # splitter skips them. They cannot use the per-line reflow exception without an actual block.
        for i, j in enumerate(jp[stem]):
            sid = f"{stem}:{i:04d}"
            if i not in covered and j.strip() and not cur[stem][i].strip() and sid not in keep:
                out.append(f"{sid}: empty English outside a reflow block for {j!r}")
    for at, j in jp["arm9"]:
        if batches.is_text(j) and not batches.JP_RE.search(cur["arm9"][at]):
            out.extend(f"a9:{at}: {p}" for p in batches.glossary_errors(j, [cur["arm9"][at]], terms, short=True))
    return out


def stage_names(jp, cur):
    """A stage name reads the same in the stage list (0000) and in its STnnSTAGE table (string 351, which the
    title card is drawn from, tools/gfx.py)."""
    z = next((k for k in cur if k.startswith("0000_")), None)
    names = dict(zip(jp[z], cur[z])) if z else {}
    out = []
    for stem in sorted(k for k in cur if re.search(r"_ST\d\dSTAGE$", k) and len(cur[k]) > 351):
        j, e = jp[stem][351], cur[stem][351]
        if j in names and names[j] != e:
            out.append(f"{stem}:0351: stage name {e!r} != stage list {names[j]!r}")
        if fit.px(e) > STAGE_NAME_PX:
            out.append(f"{stem}:0351: stage name {e!r} {fit.px(e)} px > {STAGE_NAME_PX} (prep name bar)")
    return out


# shortcut: prep/brief name bar wraps past ~155 px (st61 at 156 lost the O's edge, visual QA 2026-11-01); margin kept
STAGE_NAME_PX = 150


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
    for e in errs if "-v" in sys.argv else errs[:30]:
        print(e)
    if len(errs) > 30 and "-v" not in sys.argv:
        print(f"... {len(errs) - 30} further errors (-v lists them)")
    for kind, rows in warns.items():
        print(f"warning: {len(rows)} lines {kind}" + ("" if "-v" in sys.argv else " (-v lists them)"))
        if "-v" in sys.argv:
            for r in rows:
                print("  " + r)
    print(f"{len(errs)} errors")
    sys.exit(1 if errs else 0)
