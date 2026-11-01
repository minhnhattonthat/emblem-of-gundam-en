"""check.py: the repo's one-command check (the pre-commit hook runs it). Exit non-zero on any failure.

Runs every tests/test_*.py through unittest discovery. Tests that need the ROM skip when rom/ is absent.
--phase7 additionally requires the strict measured-width coverage gate; unit-test success alone does not
certify a phase while width research remains incomplete (docs/status.md)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT))
    ok = unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful()
    if ok and "--phase7" in sys.argv:
        import lint
        errors, _ = lint.lint()
        for error in errors[:30]:
            print(error)
        print(f"Phase 7 strict lint: {len(errors)} errors")
        ok = not errors
    sys.exit(0 if ok else 1)
