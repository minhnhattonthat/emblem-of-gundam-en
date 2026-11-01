""".BBQ1.00 table files (see docs/re/bbq.md): sections and the string table.

Header: 0x00 '.BBQ1.00', 0x08 u32 timestamp, 0x0C u32 1, 0x10 u32 0x18 (descriptor table offset), 0x14 u32 nsec,
then nsec descriptors of 5 u32 at 0x18 + 20*i: (type, index_off, count, data_off, data_size); both offsets are
relative to the descriptor's own start. Type 7 is the string table: count u32 offsets (into the pool) + a pool of
NUL-terminated Shift-JIS strings.

    python -X utf8 tools/bbq.py FILE        # print sections and the first strings"""
import struct
import sys


def sections(d):
    assert d[:8] == b".BBQ1.00", d[:8]
    base, n = struct.unpack_from("<2I", d, 0x10)
    out = []
    for i in range(n):
        at = base + 20 * i
        typ, io, cnt, do, dsz = struct.unpack_from("<5I", d, at)
        out.append({"type": typ, "at": at, "index": at + io, "count": cnt, "data": at + do, "size": dsz})
    return out


def strtab(d):
    """Return (section, list of raw bytes strings) for the type-7 section, or (None, [])."""
    for s in sections(d):
        if s["type"] == 7:
            offs = struct.unpack_from(f"<{s['count']}I", d, s["index"])
            pool = d[s["data"]:s["data"] + s["size"]]
            return s, [pool[o:pool.index(b"\0", o)] for o in offs]
    return None, []


def rebuild(d, strs):
    """Return the file with its type-7 pool replaced by `strs` (raw bytes per string, no NUL), any length.

    The type-7 section is last, so only its index + pool move: the index keeps its offset, the pool is padded to a
    multiple of 4 like the original, and the file's trailing bytes (24 zero bytes) are kept. The descriptor's size
    word is updated; the count must not change (one string per id)."""
    s = next(s for s in sections(d) if s["type"] == 7)
    if len(strs) != s["count"]:
        raise ValueError(f"string count changed: {len(strs)} != {s['count']}")
    pool, offs = b"", []
    for b in strs:
        if b"\0" in b:
            raise ValueError(f"NUL inside a string: {b!r}")
        offs.append(len(pool))
        pool += b + b"\0"
    pool += bytes(-len(pool) % 4)
    index = struct.pack(f"<{len(offs)}I", *offs)
    out = bytearray(d[:s["index"]] + index + pool + d[s["data"] + s["size"]:])
    struct.pack_into("<I", out, s["at"] + 16, len(pool))
    return bytes(out)


SIZES = [4] * 8 + [16, 32, 64, 128, 256]  # VM type -> bytes (arm9 0x02070F6C); 8-12 are str16..str256
NATIVE = 0x0E  # op: hand the string on top of the stack to a native function, as its own type


def code_words(d):
    """(section, list of u32) of the type-6 bytecode, or (None, [])."""
    for s in sections(d):
        if s["type"] == 6:
            return s, list(struct.unpack_from(f"<{s['size'] // 4}I", d, s["data"]))
    return None, []


def instructions(w):
    """Yield (word index, op word, args): each instruction is [op][source line][args]; op = code | type << 10 |
    nargs << 16 (arm9 decoder 0x02046E84)."""
    i = 0
    while i < len(w):
        n = w[i] >> 16
        yield i, w[i], w[i + 2:i + 2 + n]
        i += 2 + n


def widen(d, strs):
    """Return (file, problems) with every string push grown to fit its new text (docs/re/bbq.md §VM strings).

    Op 0 with a string type pushes string #arg as a temp of that type's size: a longer string is cut without a NUL,
    and the native call that takes it (op 0x0E, its own type) then reads the next stack bytes as text. The compiler
    sized each push from the Japanese, so English needs a bigger type: the smallest that holds bytes + NUL, never
    above the consuming native's type (a temp bigger than that is a VM type error). A push that feeds anything else
    (a script-function argument, ops 0x2D/0x2E) can't grow; it is reported as (string index, bytes + NUL, limit)."""
    s, w = code_words(d)
    if s is None:
        return d, []
    out, problems = list(w), []
    ins = list(instructions(w))
    for k, (i, op, args) in enumerate(ins):
        typ = (op >> 10) & 0x1F
        if op & 0x3FF or not 8 <= typ <= 12 or not args or args[0] >= len(strs):
            continue
        need = len(strs[args[0]]) + 1
        if need <= SIZES[typ]:
            continue
        nxt = ins[k + 1][1] if k + 1 < len(ins) else 0
        cap = (nxt >> 10) & 0x1F if nxt & 0x3FF == NATIVE else typ
        fit = next((t for t in range(typ, cap + 1) if SIZES[t] >= need), None)
        if fit is None:
            problems.append((args[0], need, SIZES[cap] - 1))
            continue
        out[i] = op & ~0x7C00 | fit << 10
    if out == w:
        return d, problems
    b = bytearray(d)
    struct.pack_into(f"<{len(out)}I", b, s["data"], *out)
    return bytes(b), problems


TUTOR_FN = 201  # script fn 201 = tutorial box: 4 lines (pushed last-first), y = Y*8, x = X*8 (docs/re/bbq.md)


def tutorial_box_words(w, strs):
    """(words, problems): each fn-201 box sizes itself at 7 px per half-width byte (13 per full-width char), rounded
    to 8, with its fill starting at 8X - 4 (measured, phase 8); English made boxes run off the right edge. Lower X
    until the fill ends by x 251; a box that still doesn't fit at X = 1 is reported as (a line id, fill right)."""
    out, problems = list(w), []
    ins = list(instructions(w))
    for k, (i, op, args) in enumerate(ins):
        if op & 0x3FF != 0x2E or list(args[:1]) != [TUTOR_FN] or k < 6:
            continue
        xpush = ins[k - 3]  # push Y; push 8; mul; push X; push 8; mul; call
        ids, j = [], k - 7
        while j >= 1 and ins[j][1] & 0x3FF == NATIVE and ins[j - 1][1] & 0x3FF == 0 and len(ids) < 4:
            ids.append(ins[j - 1][2][0])
            j -= 2
        if not ids or xpush[1] & 0x3FF or not xpush[2]:
            continue
        px = max(sum(13 if ord(c) > 0x7F else 7 for c in strs[s].decode("cp932")) for s in ids)
        width = (px + 4) // 8 * 8
        x = min(xpush[2][0], (256 - width) // 8)
        if x < 1:
            problems.append((ids[0], 4 + width - 1))
            x = 1
        out[xpush[0] + 2] = x
    return out, problems


def tutorial_boxes(d, strs):
    """Return (file, problems) with tutorial_box_words applied to the bytecode."""
    s, w = code_words(d)
    if s is None:
        return d, []
    out, problems = tutorial_box_words(w, strs)
    if out == w:
        return d, problems
    b = bytearray(d)
    struct.pack_into(f"<{len(out)}I", b, s["data"], *out)
    return bytes(b), problems


NAME_FIELD = 64  # stage record (type 5, entry 0, 84 bytes): char name[64] + 5 words


def stage_name(d, old, new):
    """Return the file with its stage record's name field set to the new text of the pool string that held the
    same Japanese (all 90 stage tables have one, #351 mostly). The stage-info panel on the map reads this field, not
    the pool (docs/re/bbq.md). Files without the 84-byte record come back unchanged."""
    s = next((x for x in sections(d) if x["type"] == 5), None)
    if s is None:
        return d
    lo, hi = struct.unpack_from("<2I", d, s["index"]) if s["count"] > 1 else (0, s["size"])
    at = s["data"] + lo
    if hi - lo != 84:
        return d
    name = d[at:at + NAME_FIELD].split(b"\0")[0]
    if name not in old:
        raise ValueError(f"stage record name {name!r} has no pool copy")
    text = new[old.index(name)]
    if len(text) >= NAME_FIELD:
        raise ValueError(f"stage name {text!r} is over {NAME_FIELD - 1} bytes")
    b = bytearray(d)
    b[at:at + NAME_FIELD] = text.ljust(NAME_FIELD, b"\0")
    return bytes(b)


if __name__ == "__main__":
    d = open(sys.argv[1], "rb").read()
    for s in sections(d):
        print({k: hex(v) for k, v in s.items()})
    _, strs = strtab(d)
    for i, s in enumerate(strs[:20]):
        print(i, s.decode("cp932", "backslashreplace"))
