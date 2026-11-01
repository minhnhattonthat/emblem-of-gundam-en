"""insert.py: script/ (the translation) -> the patches build.py applies.

One JSON per BBQ string table (script/bbq/<ez index>_<name>.json) and script/arm9.json for the ARM9 strings.
A table whose text still matches the ROM is left alone, so an untouched script/ builds a byte-identical ROM
(tests/test_identity.py).

    python -X utf8 tools/insert.py --status    # changed tables/strings against the ROM"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import arm9  # noqa: E402
import bbq  # noqa: E402

SCRIPT = ROOT / "script"
BBQ_DIR = SCRIPT / "bbq"


def tables(directory=BBQ_DIR):
    """{ez index: [string]} from script/bbq."""
    out = {}
    for path in sorted(directory.glob("*.json")):
        obj = json.loads(path.read_text(encoding="utf-8"))
        out[obj["ez_index"]] = obj["strings"]
    return out


def arm9_texts(path=SCRIPT / "arm9.json"):
    """{file offset: string} from script/arm9.json."""
    if not path.is_file():
        return {}
    return {int(s["at"], 16) - arm9.BASE: s["text"] for s in json.loads(path.read_text(encoding="utf-8"))["strings"]}


def ez_edits(unpacked, script=None):
    """{ez index: new file bytes} for the tables whose text changed; an empty dict means no edit.

    Rebuilt files are padded to a multiple of 16, the size the archive's size word reports (ez.repack): the game
    mallocs that many bytes, so the padding is what the parser sees after the table's own tail."""
    script = tables() if script is None else script
    out, problems = {}, []
    for i, strs in script.items():
        if i not in unpacked:
            raise KeyError(f"script/bbq has ez_index {i}, which is not a text table in this ROM")
        raw = unpacked[i]
        enc = [s.encode("cp932") for s in strs]
        widened, bad = bbq.widen(raw, enc)  # string pushes sized for the Japanese (docs/re/bbq.md)
        widened = bbq.stage_name(widened, bbq.strtab(raw)[1], enc)  # the map panel's copy of the stage name
        problems += [f"{i:04d}:{k:04d} needs {n} bytes, the script call takes {lim}: {strs[k]!r}" for k, n, lim in bad]
        new = bbq.rebuild(widened, enc)
        if new != raw:
            out[i] = new + bytes(-len(new) % 16)
    if problems:
        raise ValueError("strings too long for their script slot (shorten them):\n" + "\n".join(problems))
    return out


def arm9_edit(data, texts=None):
    """arm9 bytes with the changed strings written back: in place where the English fits, otherwise moved into the
    ITCM autoload tail (arm9.relocate)."""
    texts = arm9_texts() if texts is None else texts
    old = {off: t for off, t in arm9.strings(data)}
    edits = {off: t for off, t in texts.items() if old.get(off) != t}
    if not edits:
        return data
    fits, grow = {}, {}
    for off, text in edits.items():
        room = data.find(b"\0", off) - off
        (fits if len(text.encode("cp932")) <= room else grow)[off] = text
    out = arm9.replace(data, fits) if fits else data
    return arm9.relocate(out, grow) if grow else out


if __name__ == "__main__" and sys.argv[1:] == ["--status"]:
    import extract

    data = extract.ROM.read_bytes()
    rom, tbl, dat = extract._load(data)
    got = extract.bbq_files(tbl, dat)
    unpacked = {i: raw for i, (_, raw, _) in got.items()}
    changed = ez_edits(unpacked)
    script = tables()
    n = sum(1 for i in changed for a, b in zip(script[i], got[i][2]) if a != b)
    print(f"{len(changed)} of {len(unpacked)} tables changed, {n} strings")
    old = {off: t for off, t in arm9.strings(rom.arm9)}
    want = arm9_texts()
    print(f"{sum(1 for off, t in want.items() if old.get(off) != t)} of {len(old)} arm9 strings changed")
