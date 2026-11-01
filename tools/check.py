"""check.py: the repo's one-command check (the pre-commit hook runs it). Exit non-zero on any failure.

Runs every tests/test_*.py through unittest discovery. Tests that need the ROM skip when rom/ is absent.
The merged-script test includes strict measured-width coverage. --phase7 remains an accepted legacy
alias for the same full check; ordinary checks and the commit hook enforce the same gate."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT))
    ok = unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful()
    sys.exit(0 if ok else 1)
