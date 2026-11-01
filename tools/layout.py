"""Reviewed UI layout operands in BBQ bytecode; offsets and preimages belong to the pinned original.

MAKERLOGO's sound submenu calls setup helper 0x1000f with layout mode 0.
Mode 0 uses the narrow buttons; mode 1 is the title menu's medium layout.
The row position arguments remain unchanged; the shared setup centres the buttons.
"""
import struct

OPERANDS = {
    81: [(0x20c0, 0, 1, "Sound submenu medium-width layout")],
}

# Trait fields start at x168: eleven tiles reach the screen edge and hold the full English term.
ARM9_OPERANDS = [(off, 0xE3A0100A, 0xE3A0100B, "Unit trait surface 80 to 88 px")
                for off in (0x49a5c, 0x49a9c, 0x49adc)]
STRING_COPIES = [
    (0x2c110, 0x72550, [0xE3A0201F, 0xE5D31000, 0xE5D30001, 0xE2833002,
                       0xE5C41000, 0xE5C40001, 0xE2844002, 0xE2522001,
                       0x1AFFFFF7, 0xE5D31000, 0xE28D0000, 0xE5C41000],
     0xE1A00004, "Terrain-lineup error literal"),  # destination r4
    (0x4f174, 0x7480c, [0xE3A0201E, 0xE5D31000, 0xE5D30001, 0xE2833002,
                       0xE2522001, 0xE5CC1000, 0xE5CC0001, 0xE28CC002,
                       0x1AFFFFF7, 0xE5D30000, 0xE5CC0000],
     0xE1A0000C, "Retirement conversion literal"),  # destination ip
]


def arm9_writes(original, edits):
    """Exact native writes. Replace two fixed-count copies with the game's strcpy helper.

    The reviewed dialog text member has at least 256 bytes. Validate the complete literal before
    permitting an unbounded native copy. Replacing the whole old loop also removes its odd tail
    read, which would read past even-sized relocated strings after merely increasing its count.
    """
    if not edits:
        return []
    operands = list(ARM9_OPERANDS)
    writes = []
    for off, before, after, name in operands:
        expected = struct.pack("<I", before)
        if original[off:off + 4] != expected:
            raise ValueError(f"ARM9 {off:#x} {name}: unexpected original instruction")
        writes.append((off, expected, struct.pack("<I", after), name))
    for off, source, before, destination, name in STRING_COPIES:
        if source not in edits:
            continue
        if len(edits[source].encode("cp932")) + 1 > 256:
            raise ValueError(f"{name}: translated literal exceeds its native destination")
        expected = struct.pack(f"<{len(before)}I", *before)
        if original[off:off + len(expected)] != expected:
            raise ValueError(f"ARM9 {off:#x} {name}: unexpected original copy loop")
        call_at = 0x02000000 + off + 8
        branch = 0xEB000000 | (((0x020102EC - call_at - 8) >> 2) & 0xFFFFFF)
        # mov r0,destination; mov r1,r3; bl strcpy; nop...; restore dispatcher argument if needed.
        after = [destination, 0xE1A01003, branch] + [0xE1A00000] * (len(before) - 3)
        if source == 0x72550:
            after[-1] = 0xE1A0000D  # mov r0,sp, for the following dialog-dispatch call
        writes.append((off, expected, struct.pack(f"<{len(after)}I", *after), name + " terminated copy"))
    return writes


def apply_arm9(original, translated, edits):
    data = bytearray(translated)
    for off, _, after, _ in arm9_writes(original, edits):
        data[off:off + len(after)] = after
    return bytes(data)


def apply(index, original):
    data = bytearray(original)
    for off, before, after, name in OPERANDS.get(index, []):
        actual = struct.unpack_from("<I", original, off)[0]
        if actual != before:
            raise ValueError(f"{index}:{off:#x} {name}: expected {before}, got {actual}")
        struct.pack_into("<I", data, off, after)
    return bytes(data)
