"""Enumerate native format inputs from the pinned ROM and current translations.

Caller/record evidence: docs/re/width-callers.md. These are display strings, including any
prefix concatenated by the caller, so byte and pixel checks apply after substitution.
"""
from functools import lru_cache
from itertools import product
import struct

import batches
import build
import extract
import fit

UNIT_FORMATS = {"02072208", "0207221c", "0207237c", "020723a4", "020723e0", "020723fc"}
CHAR_FORMATS = {"02072268", "02072284"}
LEVEL_PARTS = ("020743a8", "020743ac", "020743b0", "020743b4")
ENV_PARTS = ("02076f44", "02076f4c", "02076f54", "02076f24")
DIR_PARTS = ("02076f2c", "02076f04", "02076f18", "02076f34", "02076f14", "02076f20",
             "02076f08", "02076f10", "02076f3c", "02076f1c", "02076f0c")
CHOICE_HOSTS = {"02073308", "02073320", "02073cbc", "02073cd0", "02073d00", "02073d1c"}


@lru_cache(maxsize=1)
def record_sources():
    batches.jp_tables()  # verifies the pinned ROM before using its record indices
    rom, table, data = extract._load(build.ROM.read_bytes())
    files = extract.bbq_files(table, data)
    sources = {}
    for name, index, count, stride in [("unit", 5, 141, 0x34), ("character", 3, 147, 0x24)]:
        filename, raw, _ = files[index]
        sources[name] = (extract.stem(index, filename),
                         sorted({struct.unpack_from("<I", raw, 0x8c + stride * i)[0] for i in range(count)}))
    sources["team"] = tuple(f"{struct.unpack_from('<I', rom.arm9, 0x73380 + 4 * i)[0]:08x}"
                            for i in range(0x4e, 0x9c))
    return sources


def names(kind, current):
    stem, indices = record_sources()[kind]
    return sorted({current[stem][i] for i in indices})


def widest_integer(high):
    """Choose a value maximizing both current digit width and byte count in 0..high."""
    digits = str(high)
    wide = max("0123456789", key=fit.px)
    first = max("123456789", key=fit.px)
    candidates = {"0", digits}
    candidates.update(first + wide * (n - 1) for n in range(1, len(digits)))
    for i, digit in enumerate(digits):
        for smaller in range(1 if i == 0 else 0, int(digit)):
            candidates.add(digits[:i] + str(smaller) + wide * (len(digits) - i - 1))
    return int(max(candidates, key=lambda s: (fit.px(s), len(s))))


def renderings(sid, template, current):
    """Full rendered alternatives, or None when the native caller has not been modeled."""
    if not sid.startswith("a9:"):
        return None
    address = sid[3:]
    native = current["arm9"]
    if address in CHOICE_HOSTS:
        return [template + native["020747f4"]]
    if address == "02072c6c":
        # 020350cc rejects nonpositive signed words; sprintf at 020350ec uses %s%d.
        return [template + str(widest_integer(0x7fffffff))]
    if address in UNIT_FORMATS | CHAR_FORMATS:
        return [template % name for name in names("unit" if address in UNIT_FORMATS else "character", current)]
    if address == "020744a0":
        return [template % native[at] for at in LEVEL_PARTS]
    if address in {"02072b9c", "02072ba4"}:
        return [template % n for n in (80, 90, 100, 110, 120)]
    if address in {"02073248", "020732f0"}:
        return [native[at] + template for at in record_sources()["team"]]
    if address in {"02074b88", "02074bb8"}:
        stages = next(v for k, v in current.items() if k.startswith("0000_"))
        args = (widest_integer(256), widest_integer(19884), widest_integer(59), widest_integer(59))
        return [template % (args[0], stage, *args[1:]) for stage in stages]
    if address == "020770cc":
        return [" " + template % (weapon, native[env], native[direction])
                for weapon, env, direction in product(range(1, 9), ENV_PARTS, DIR_PARTS)]
    return None
