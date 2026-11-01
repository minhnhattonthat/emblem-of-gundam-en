"""Reviewed UI layout operands in BBQ bytecode; offsets and preimages belong to the pinned original.

MAKERLOGO's sound submenu calls setup helper 0x1000f with layout mode 0.
Mode 0 uses the narrow buttons; mode 1 is the title menu's medium layout.
The row position arguments remain unchanged; the shared setup centres the buttons.
"""
import struct

OPERANDS = {
    81: [(0x20c0, 0, 1, "Sound submenu medium-width layout")],
}


def apply(index, original):
    data = bytearray(original)
    for off, before, after, name in OPERANDS.get(index, []):
        actual = struct.unpack_from("<I", original, off)[0]
        if actual != before:
            raise ValueError(f"{index}:{off:#x} {name}: expected {before}, got {actual}")
        struct.pack_into("<I", data, off, after)
    return bytes(data)
