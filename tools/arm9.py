"""arm9.py: the ARM9's own Shift-JIS strings, their pointers, and growing them into the ITCM autoload tail.

The strings live NUL-terminated in the main code section's tail, file 0x72170-0x77140 (RAM 0x02072170 upward):
shop, team-building, save/load, options, turn prompts and the leftover debug menu. Every one is reached from a
4-byte literal pointer (ARM's literal pools; a pointer table for a few menus), stored in arm9 itself, so a string can
be extracted by scanning the region and told apart from the binary data around it by requiring a pointer to its start.

`replace()` writes a string back in place and refuses to grow it. `relocate()` moves strings whose English is longer
into the free tail of the ITCM autoload block (docs/re/text.md): the arm9 file is laid out

    [main section][ITCM source][DTCM source][autoload list]

with 12-byte autoload entries (RAM address, size, bss) at file 0x78300 and the module params at file 0xba0 pointing
at it (+0x00 list address, +0x04 list end). ITCM is 32 KiB and the game loads only 0x1160, so ~27 KiB are free:
the moved strings go right after the ITCM source, that section's size grows, the DTCM source and the list slide up,
and the old string's pointers are rewritten to 0x01FF8000 + the old size. No code changes: this is data.

    python -X utf8 tools/arm9.py work/fs/arm9.bin    # print every string with its pointers"""
import struct
import sys
import unicodedata

BASE = 0x02000000
LO, HI = 0x72170, 0x77140  # file offsets of the string region (main section tail)
ITCM_RAM = 0x01FF8000
ITCM_LIMIT = 0x8000  # 32 KiB of ITCM


def valid(text):
    """True if text is something the game can draw: no controls but \\n, no private-use or unassigned codepoints."""
    for c in text:
        o = ord(c)
        if c == "\n":
            continue
        if o < 0x20 or o == 0x7F or 0xE000 <= o <= 0xF8FF:
            return False
        if unicodedata.category(c) in ("Cc", "Cs", "Cn", "Co"):
            return False
    return True


def decode(b):
    """cp932 bytes -> str, or None when they aren't SJIS text."""
    try:
        s = b.decode("cp932")
    except UnicodeDecodeError:
        return None
    return s if valid(s) else None


def runners(d, lo=LO, hi=HI):
    """Yield (offset, end, text or None) for every NUL-terminated run in the region."""
    off = lo
    while off < min(hi, len(d)):
        if d[off] == 0:
            off += 1
            continue
        end = d.find(b"\0", off)
        if end < 0:
            return
        yield off, end, decode(d[off:end])
        off = end + 1


def pointers(d, off):
    """File offsets of the 4-aligned words holding the RAM address BASE + off (empty if unreferenced)."""
    want = struct.pack("<I", BASE + off)
    out, at = [], d.find(want, 0, len(d) - 3)
    while at >= 0:
        if at % 4 == 0:
            out.append(at)
        at = d.find(want, at + 1)
    return out


def strings(d):
    """[(file offset, text)] for every string a pointer reaches, in address order. Runs below two bytes are
    binary data whose address a table happens to hold, not text."""
    return [(off, t) for off, end, t in runners(d) if t and end - off >= 2 and pointers(d, off)]


def replace(d, edits):
    """Return arm9 with {file offset: text} replaced in place. A replacement must not be longer than the original
    plus its NUL: growing one needs `relocate`."""
    out = bytearray(d)
    byoff = {off: t for off, t in strings(d)}
    for off, text in edits.items():
        if off not in byoff:
            raise KeyError(f"{off:#x} is not a string start")
        old = d.find(b"\0", off) - off
        new = text.encode("cp932")
        if len(new) > old:
            raise ValueError(f"{BASE + off:#x}: {len(new)} bytes do not fit in {old}: {text!r}")
        out[off:off + old + 1] = new + bytes(old + 1 - len(new))
    return bytes(out)


def layout(d):
    """(params file offset, autoload list file offset, [(ram, size, bss)]) for the autoload list, or None."""
    at = d.find(struct.pack("<I", ITCM_RAM))
    while at >= 0:
        want = struct.pack("<I", BASE + at)
        params = d.find(want)
        while params >= 0:
            if params % 4 == 0 and params + 8 <= len(d):
                end = struct.unpack_from("<I", d, params + 4)[0]
                span = end - (BASE + at)
                if span > 0 and span % 12 == 0 and span // 12 <= 8 and at + span <= len(d):
                    ents = [struct.unpack_from("<3I", d, at + 12 * i) for i in range(span // 12)]
                    # entry 0 is ITCM by construction; entry 1 must be the DTCM block after it
                    if (len(ents) > 1 and ents[0][1] <= ITCM_LIMIT
                            and 0x02700000 <= ents[1][0] <= 0x03000000):
                        return params, at, ents
            params = d.find(want, params + 1)
        at = d.find(struct.pack("<I", ITCM_RAM), at + 1)
    return None


def itcm_room(d):
    """Bytes free in the ITCM autoload block after the code the game already loads."""
    got = layout(d)
    return None if got is None else ITCM_LIMIT - got[2][0][1]


def relocate(d, texts):
    """Return arm9 with {file offset: text} moved into the ITCM tail: the ITCM section grows by the data, the DTCM
    source and the autoload list slide up, the list's own address moves in the module params, and every 4-byte
    pointer to a moved string is rewritten. The old slot is zeroed. Raises when ITCM would overflow."""
    got = layout(d)
    if got is None:
        raise ValueError("no autoload list found: cannot grow arm9 strings")
    params, lst, ents = got
    itcm, dtcm = ents[0], ents[1]
    src = lst - dtcm[1] - itcm[1]  # the ITCM source starts here; its data ends at lst - dtcm[1]
    at = src + itcm[1]

    data, room = bytearray(), itcm[1]
    where = {}
    for off, text in texts.items():
        blob = text.encode("cp932") + b"\0"
        where[off] = (ITCM_RAM + room, room)
        room += len(blob)
        data += blob
    data += bytes(-len(data) % 4)  # the autoload list must stay 4-aligned (the game loads it with LDR)
    if room > ITCM_LIMIT:
        raise ValueError(f"{len(data)} bytes of strings do not fit in {itcm_room(d)} free ITCM bytes")

    out = bytearray(d[:at] + bytes(data) + d[at:])
    new_lst = lst + len(data)
    struct.pack_into("<I", out, new_lst + 4, itcm[1] + len(data))  # ITCM section size
    struct.pack_into("<I", out, params, BASE + new_lst)
    struct.pack_into("<I", out, params + 4, BASE + new_lst + 12 * len(ents))
    for off, (addr, _) in where.items():
        old_slot = d.find(b"\0", off) - off + 1
        for p in pointers(d, off):
            struct.pack_into("<I", out, p, addr)
        out[off:off + old_slot] = bytes(old_slot)
    return bytes(out)


def fits(d, edits, texts=None):
    """{file offset: text} for the edits a plain `replace` can take (the rest need `relocate`)."""
    byoff = dict(strings(d))
    out = {}
    for off, text in edits.items():
        old = d.find(b"\0", off) - off
        out[off] = text if len(text.encode("cp932")) <= old else None
    return out


if __name__ == "__main__":
    d = open(sys.argv[1], "rb").read()
    for off, text in strings(d):
        print(f"{BASE + off:#09x} {[hex(p) for p in pointers(d, off)]} {text}")
