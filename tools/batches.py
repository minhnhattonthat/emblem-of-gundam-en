"""batches.py: phase 6 translation batches -- split the untranslated script into agent-sized batches, check a
translator's output, merge it back into script/.

    python -X utf8 tools/batches.py split [--chars 3000] [--max 150]   # work/tl/bNNN.tsv + terms_bNNN.txt
    python -X utf8 tools/batches.py check bNNN [bNNN..]                 # exit 1 on any error
    python -X utf8 tools/batches.py merge [bNNN..]                       # checked outputs -> script/ (+ duplicates)
    python -X utf8 tools/batches.py status                               # translated / left, per table class

Ids: `EEEE:IIII` (BBQ ez index : string index) and `a9:XXXXXXXX` (arm9 RAM address).
A string counts as translated once its script/ text differs from the ROM's Japanese, so `split` only queues what is
left. Dedup: story text is cut into blocks (one speech or one sentence, docs/translator-brief.md); a block whose
Japanese already appeared earlier is not queued again, `merge` copies the first block's English to every copy.
Input `id<TAB>speaker<TAB>form<TAB>limit<TAB>jp`, output `id<TAB>en` (`<empty>` = draw nothing on that line).
"""
import json
from functools import lru_cache
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fit  # noqa: E402

TL = ROOT / "work" / "tl"
BBQ_DIR = ROOT / "script" / "bbq"
ARM9 = ROOT / "script" / "arm9.json"
JP_CACHE = TL / "jp.json"
GLOSSARY = ROOT / "glossary.md"
STORY_PX = 180  # story_dialogue / stage_card_narration budget, tbl/windows.json (measured)
JP_RE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff\uff66-\uff9f\uff01-\uff5e]")
TOKEN_RE = re.compile(r"\$L|\$P\d\d|%%|%[ds]|%|\n")  # %% = one literal percent in a printf string
END = tuple("」』。！？!?）)♪")
# Developer test rooms and their copies of the stage text: translated last (the release never reaches them).
DEV = re.compile(r"^00(1[7-9]|2\d|3[0-8])_|_BATTLE\d\d$|^0084_")
STORY = re.compile(r"STAGE|MILITARY|EV_EVENT|BATTLE|BTLDIR|NAKAMURA|SHIKATA|TAKESHITA|SUZUKI|KOYAMA|FUKE")
EMPTY = "<empty>"


@lru_cache(maxsize=1)
def jp_tables():
    """Authoritative ROM extraction, cached only within this process.

    Never trust work/tl/jp.json: it predates extractor changes on some workspaces.
    A new check process always uses the current extractor and pinned original ROM.
    """
    import build
    import check_rom
    import extract
    check_rom.check()
    rom, tbl, dat = extract._load(build.ROM.read_bytes())
    out = {extract.stem(i, n): s for i, (n, _, s) in extract.bbq_files(tbl, dat).items()}
    out["arm9"] = [[f"{0x02000000 + off:08x}", t] for off, t in extract.arm9_text(rom.arm9)]
    return out


def current():
    """{stem: [script/ strings]} and {'arm9': {at: text}}."""
    out = {p.stem: json.loads(p.read_text(encoding="utf-8"))["strings"] for p in sorted(BBQ_DIR.glob("*.json"))}
    out["arm9"] = {s["at"][2:].rjust(8, "0"): s["text"] for s in json.loads(ARM9.read_text(encoding="utf-8"))["strings"]}
    return out


def is_text(s):
    return bool(JP_RE.search(s)) and "&" not in s


def blocks(stem, strs):
    """[(form, [index..])] for one table's text strings. Story: speaker names alone, a speech from 「 to 」, prose to
    the end of a sentence (max 8 lines). Data tables: every string alone."""
    out, cur = [], []
    story = bool(STORY.search(stem))
    for i, s in enumerate(strs):
        if not is_text(s):
            if cur:
                out.append(("dlg" if strs[cur[0]].startswith("「") else "narration", cur))
                cur = []
            continue
        if not story:
            out.append(("menu", [i]))
            continue
        nxt = strs[i + 1] if i + 1 < len(strs) else ""
        if not cur and nxt.startswith("「") and not s.startswith("「") and len(s) <= 12 and not s.endswith(END):
            out.append(("name", [i]))
            continue
        if s.startswith("「") and cur:
            out.append(("dlg" if strs[cur[0]].startswith("「") else "narration", cur))
            cur = []
        cur.append(i)
        if s.rstrip().endswith(END) or nxt.startswith("「") or len(cur) >= 8:
            out.append(("dlg" if strs[cur[0]].startswith("「") else "narration", cur))
            cur = []
    if cur:
        out.append(("dlg" if strs[cur[0]].startswith("「") else "narration", cur))
    return out


def units():
    """Every text block in queue order, deduplicated: [(stem, form, [(id, jp)], speaker, limit, [dup id lists])]."""
    jp = jp_tables()
    order = sorted((k for k in jp if k != "arm9"), key=lambda k: (bool(DEV.search(k)), not k < "0086", k))
    seen, out = {}, []
    for stem in order:
        strs = jp[stem]
        ez = stem[:4]
        speaker, name_at, prev = "", -2, []
        for form, idx in blocks(stem, strs):
            ids = [f"{ez}:{i:04d}" for i in idx]
            if form == "name":
                speaker, name_at = strs[idx[0]], idx[0]
            elif name_at != idx[0] - 1:
                speaker = ""  # a speaker label only names the speech right after it
            text = tuple(strs[i] for i in idx)
            key = text
            if len(prev) >= 8 and prev[-1] + 1 == idx[0] and not strs[prev[-1]].rstrip().endswith(END):
                key = (stem,) + text  # tail of a sentence cut at 8 lines: its English depends on the lines before
            prev = idx
            if key in seen:
                seen[key][5].append(ids)
                continue
            story = bool(STORY.search(stem))
            limit = f"{STORY_PX}px" if story else f"~{max(fit.px(strs[i]) for i in idx)}px"
            u = (stem, form, list(zip(ids, text)), speaker if form == "dlg" else "", limit, [])
            seen[key] = u
            out.append(u)
    for at, t in jp["arm9"]:
        if not is_text(t):
            continue
        key = (t,)
        if key in seen:
            seen[key][5].append([f"a9:{at}"])
            continue
        u = ("arm9", "menu", [(f"a9:{at}", t)], "", f"~{fit.px(t)}px", [])
        seen[key] = u
        out.append(u)
    return out


def get(cur, id_):
    a, b = id_.split(":")
    if a == "a9":
        return cur["arm9"][b]
    stem = next(k for k in cur if k.startswith(a + "_"))
    return cur[stem][int(b)]


def esc(s):
    return s.replace("\\", "\\\\").replace("\n", "\\n").replace("\t", " ")


def unesc(s):
    return re.sub(r"\\(.)", lambda m: "\n" if m.group(1) == "n" else m.group(1), s)


# ---- glossary ----------------------------------------------------------------------------------------------------
def glossary():
    """[(jp forms, en, avoid forms)] from every table row of glossary.md (`| JP | EN | max | notes | Avoid |`;
    several JP forms separated by `;`, several avoided spellings by `;`)."""
    rows = []
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 2 or not line.startswith("|") or c[0] in ("JP", "") or set(c[0]) <= set("-: "):
            continue
        rows.append(([j.strip() for j in c[0].split(";") if j.strip()], c[1],
                     [a.strip() for a in (c[4] if len(c) > 4 else "").split(";") if a.strip()]))
    return rows


KATA = re.compile(r"[\u30a1-\u30fa\u30fc]")


def has_term(text, term):
    """Katakana terms match whole runs only (ミン is not in タイミング); others match as substrings."""
    if not KATA.fullmatch(term[0]) or not KATA.fullmatch(term[-1]):
        return term in text
    for m in re.finditer(re.escape(term), text):
        a, b = m.start(), m.end()
        if (a == 0 or not KATA.match(text[a - 1])) and (b == len(text) or not KATA.match(text[b])):
            return True
    return False


@lru_cache(maxsize=1)
def glossary_short_forms():
    """Optional sixth glossary column: approved alternatives for menu labels only."""
    out = {}
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) >= 6:
            out[cells[1]] = [s.strip() for s in cells[5].split(";") if s.strip()]
    return out


def glossary_errors(jp, lines, terms=None, short=False):
    """Shared block validator for batch drafts and the merged script; permits line reflow."""
    en = " ".join(" ".join(lines).split())
    low = en.lower()
    out = []
    for forms, e, avoid in glossary() if terms is None else terms:
        alternatives = glossary_short_forms().get(e, []) if short else []
        if any(has_term(jp, x) for x in forms) and e and e.lower() not in low \
                and not any(a.lower() in low for a in alternatives) \
                and not (e.endswith("y") and e[:-1].lower() + "ies" in low):
            out.append(f"glossary {forms[0]} -> '{e}' missing")
        for a in avoid:
            if any(re.search(r"\b" + re.escape(a) + r"\b", ln) for ln in lines):
                out.append(f"avoid '{a}' (glossary: {e})")
    return out


# ---- split -------------------------------------------------------------------------------------------------------
def split(chars=3000, most=150):
    TL.mkdir(parents=True, exist_ok=True)
    cur = current()
    jp = jp_tables()
    todo = [u for u in units() if any(get(cur, i) == t for i, t in u[2])]
    existing = sorted(TL.glob("b[0-9][0-9][0-9].tsv"))
    n = int(existing[-1].stem[1:]) if existing else 0
    queued = set()
    for p in existing:
        if not (TL / f"{p.stem}.merged").is_file():
            queued |= {ln.split("\t")[0] for ln in p.read_text(encoding="utf-8").splitlines()[1:]}
    todo = [u for u in todo if u[2][0][0] not in queued]
    gl = glossary()
    batches, b, size = [], [], 0
    for u in todo:
        c = sum(len(t) for _, t in u[2])
        if b and (size + c > chars or sum(len(x[2]) for x in b) + len(u[2]) > most):
            batches.append(b)
            b, size = [], 0
        b.append(u)
        size += c
    if b:
        batches.append(b)
    dups = json.loads((TL / "dups.json").read_text(encoding="utf-8")) if (TL / "dups.json").is_file() else {}
    for b in batches:
        n += 1
        name = f"b{n:03d}"
        path = TL / f"{name}.tsv"
        assert not path.exists(), path
        lines, text = ["id\tspeaker\tform\tlimit\tjp"], []
        last = None
        for stem, form, items, speaker, limit, dl in b:
            if stem != last:
                lines.append(f"# {stem}")
                last = stem
            for k, (i, t) in enumerate(items):
                f = form if len(items) == 1 else f"{form}{k + 1}/{len(items)}"
                lines.append(f"{i}\t{speaker}\t{f}\t{limit}\t{esc(t)}")
                text.append(t)
            for d in dl:
                dups.setdefault(items[0][0], []).append(d)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        joined = "\n".join(text)
        terms = [f"{'; '.join(j)} -> {e}" for j, e, _ in gl if any(has_term(joined, x) for x in j)]
        (TL / f"terms_{name}.txt").write_text("\n".join(terms) + "\n", encoding="utf-8", newline="\n")
        print(name, sum(len(x[2]) for x in b), "lines", sum(len(t) for t in text), "chars", b[0][0], "..", b[-1][0])
    (TL / "dups.json").write_text(json.dumps(dups), encoding="utf-8")


# ---- check -------------------------------------------------------------------------------------------------------
def codes(jp, en):
    """Sorted control-code tokens of both sides. A JP full-width ％ is a literal percent: `%%` in a printf string
    (one with %d/%s), else `%`; each literal percent stays its own token, so a dropped or added one shows."""
    pct = "%%" if re.search(r"%[ds]", jp) else "%"
    return sorted(TOKEN_RE.findall(jp.replace("％", pct))), sorted(TOKEN_RE.findall(en))


# Honorifics (D1/D10, style-reference): a katakana name + さん/くん/君/ちゃん keeps -san/-kun/-chan; 閣下 -> Excellency.
# Per block, so reflow and a pronoun for a repeated mention pass: each distinct name+honorific needs one EN hit.
HON_NAME = r"[ァ-ヺー・]{2,}"
HONORIFICS = [(HON_NAME + r"さん", r"-san\b"), (HON_NAME + r"(?:くん|君)", r"-kun\b"),
              (HON_NAME + r"ちゃん", r"-chan\b"), (r"閣下", r"Excellency")]


def honorifics(jp, en):
    """Problems for one block (JP lines joined, EN lines joined): honorifics the English dropped."""
    out = []
    for jrx, erx in HONORIFICS:
        need = len(set(re.findall(jrx, jp)))
        if erx == "Excellency":
            need = min(need, 1)
        got = len(re.findall(erx, en))
        if got < need:
            out.append(f"honorific: {need} x {jrx.replace(HON_NAME, 'Name')} in JP, {got} x {erx} in EN")
    return out


def read_in(name):
    rows = []
    for ln in (TL / f"{name}.tsv").read_text(encoding="utf-8").splitlines()[1:]:
        if ln.startswith("#") or not ln.strip():
            continue
        i, sp, form, limit, t = ln.split("\t")
        rows.append((i, sp, form, limit, unesc(t)))
    return rows


def read_out(name):
    out, errs = {}, []
    p = TL / f"{name}.out.tsv"
    if not p.is_file():
        return None, [f"{p.name} missing"]
    for n, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not ln.strip() or ln.startswith("#") or ln.startswith("id\t"):
            continue
        if "\t" not in ln:
            errs.append(f"line {n}: no TAB")
            continue
        i, en = ln.split("\t", 1)
        if "\t" in en:
            errs.append(f"{i}: TAB inside the English")
        if i in out:
            errs.append(f"{i}: duplicate id")
        out[i] = "" if en.strip() == EMPTY else unesc(en)
    return out, errs


def check(name):
    rows = read_in(name)
    out, errs = read_out(name)
    warns = []
    if out is None:
        return errs, warns
    ids = [r[0] for r in rows]
    for i in ids:
        if i not in out:
            errs.append(f"{i}: missing")
    for i in out:
        if i not in ids:
            errs.append(f"{i}: not in the batch")
    gl = glossary()
    t = fit.table()
    block_jp, block_en = [], []

    def flush():
        if not block_jp:
            return
        jp, en = "".join(block_jp), " ".join(" ".join(block_en).split())  # a term may wrap across lines
        errs.extend(f"{block_ids[0]}: {p}" for p in glossary_errors(jp, block_en, gl, short=block_short[0]))
        errs.extend(f"{block_ids[0]}: {p}" for p in honorifics(jp, en))
        block_jp.clear()
        block_en.clear()
        block_ids.clear()

    block_ids = []
    block_short = [False]
    for i, sp, form, limit, jp in rows:
        m = re.match(r"\D+(\d+)/", form)
        if not m or m.group(1) == "1":
            flush()
            block_short[0] = form == "menu"
        if i not in out:
            continue
        en = out[i]
        block_jp.append(jp)
        block_en.append(en)
        block_ids.append(i)
        if not en and "/" not in form:
            errs.append(f"{i}: empty English (a single line must not vanish)")
        bad = sorted({c for c in en if c != "\n" and ord(c) not in t})
        if bad:
            errs.append(f"{i}: characters the font lacks or non-ASCII: {''.join(bad)!r}")
        if "\\u" in en:
            errs.append(f"{i}: \\u escape")
        if JP_RE.search(en):
            errs.append(f"{i}: Japanese left")
        tj, te = codes(jp, en)
        if tj != te:
            errs.append(f"{i}: codes {tj} != {te}")
        if re.search(r"(%s|%d|\$P\d\d|\$L)(st|nd|rd|th)\b", en):
            errs.append(f"{i}: ordinal suffix glued to a variable")
        lim = int(re.sub(r"\D", "", limit))
        for ln in en.split("\n"):
            w = fit.px(ln.replace("%s", "W" * 8).replace("%d", "000"))
            if w > lim:
                (errs if not limit.startswith("~") else warns).append(f"{i}: {w}px > {limit}: {ln}")
    flush()
    return errs, warns


# ---- merge -------------------------------------------------------------------------------------------------------
def merge(names):
    dups = json.loads((TL / "dups.json").read_text(encoding="utf-8"))
    tables = {p.stem: (p, json.loads(p.read_text(encoding="utf-8"))) for p in sorted(BBQ_DIR.glob("*.json"))}
    a9 = json.loads(ARM9.read_text(encoding="utf-8"))
    a9i = {s["at"][2:].rjust(8, "0"): s for s in a9["strings"]}
    touched = set()

    def put(id_, en):
        a, b = id_.split(":")
        if a == "a9":
            a9i[b]["text"] = en
            touched.add("arm9")
            return
        stem = next(k for k in tables if k.startswith(a + "_"))
        tables[stem][1]["strings"][int(b)] = en
        touched.add(stem)

    done = 0
    for name in names:
        errs, _ = check(name)
        if errs:
            print(f"{name}: {len(errs)} errors, not merged")
            continue
        out, _ = read_out(name)
        rows = [r[0] for r in read_in(name)]
        for i in rows:
            put(i, out[i])
        # copies: a dup list holds the ids of a whole block, in the same order as the first block's ids
        heads = {r: k for k, r in enumerate(rows)}
        for head, lists in dups.items():
            if head not in heads:
                continue
            k = heads[head]
            for d in lists:
                for off, did in enumerate(d):
                    put(did, out[rows[k + off]])
        (TL / f"{name}.merged").write_text("", encoding="utf-8")
        done += 1
    import extract
    for stem in touched - {"arm9"}:
        extract.write_json(*tables[stem])
    if "arm9" in touched:
        extract.write_json(ARM9, a9)
    print(f"merged {done}/{len(names)} batches, {len(touched)} files")


def status():
    cur, jp = current(), jp_tables()
    tot = done = 0
    for stem, strs in jp.items():
        if stem == "arm9":
            for at, t in strs:
                if is_text(t):
                    tot += 1
                    done += cur["arm9"].get(at) != t
            continue
        for k, t in enumerate(strs):
            if is_text(t):
                tot += 1
                done += cur[stem][k] != t
    print(f"{done}/{tot} text strings translated ({100 * done / tot:.1f} %)")


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "split":
        kw = {}
        if "--chars" in args:
            kw["chars"] = int(args[args.index("--chars") + 1])
        if "--max" in args:
            kw["most"] = int(args[args.index("--max") + 1])
        split(**kw)
    elif cmd == "check":
        bad = 0
        for name in args:
            errs, warns = check(name)
            for w in warns:
                print(f"{name} WARN {w}")
            for e in errs:
                print(f"{name} ERROR {e}")
            bad += bool(errs)
            if not errs:
                print(f"{name} OK ({len(warns)} warnings)")
        sys.exit(1 if bad else 0)
    elif cmd == "merge":
        merge(args or sorted(p.stem[:4] for p in TL.glob("b[0-9][0-9][0-9].out.tsv")))
    elif cmd == "status":
        status()
    else:
        sys.exit(__doc__)
