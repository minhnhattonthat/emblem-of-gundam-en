import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom" / "Emblem of Gundam (Japan).nds"


@unittest.skipUnless(ROM.is_file(), "no ROM")
class RomHash(unittest.TestCase):
    def test_rom_matches_pin(self):
        want = [l.split()[0] for l in (ROOT / "rom.sha1").read_text().splitlines() if l and not l.startswith("#")][0]
        self.assertEqual(hashlib.sha1(ROM.read_bytes()).hexdigest(), want)
