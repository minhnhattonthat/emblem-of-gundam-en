"""The phase 7 text lint (tools/lint.py) over script/: no errors. Warnings (boxes not measured yet) are allowed."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches  # noqa: E402
import build  # noqa: E402
import lint  # noqa: E402


@unittest.skipUnless(build.ROM.is_file() or batches.JP_CACHE.is_file(), "no ROM")
class Lint(unittest.TestCase):
    def test_script_is_clean(self):
        errs, _ = lint.lint()
        self.assertEqual(errs, [], "\n" + "\n".join(errs[:30]))

    def test_catches(self):
        jp = {"0086_ST00STAGE": ["「見える」", "敵全滅", "　次へ"], "arm9": []}
        cur = {"0086_ST00STAGE": ["\"I see %d\"", "W" * 40, "見え"], "arm9": {}}
        errs, _ = lint.lint(jp, cur, set())
        text = "\n".join(errs)
        self.assertIn("codes", text)
        self.assertIn("> story_dialogue", text)
        self.assertIn("Japanese left", text)

    def test_percent(self):
        """A literal ％ in a printf string is its own token: %d%% passes, a dropped or added percent fails."""
        self.assertEqual(*batches.codes("%d％", "%d%%"))
        self.assertNotEqual(*batches.codes("%d％", "%d"))
        self.assertNotEqual(*batches.codes("%d％", "%d%%%%"))
        self.assertEqual(*batches.codes("50％", "50%"))

    def test_honorifics(self):
        h = batches.honorifics
        self.assertEqual(h("「ブライトさん、閣下が」", '"Bright-san, His Excellency is"'), [])
        self.assertTrue(h("「ブライトさん」", '"Bright."'))
        self.assertTrue(h("「キシリア閣下、御采配を」", '"Your orders, Lady Kycilia."'))
        self.assertEqual(h("「父さん」", '"Dad."'), [])  # kanji kin terms are not names
        jp = {"0086_ST00STAGE": ["「レコアさん、", "　レコアさんを」"], "arm9": []}
        errs, _ = lint.lint(jp, {"0086_ST00STAGE": ['"Reccoa,', ' her."'], "arm9": {}}, set())
        self.assertIn("honorific", "\n".join(errs))
        errs, _ = lint.lint(jp, {"0086_ST00STAGE": ['"Reccoa-san,', ' her."'], "arm9": {}}, set())
        self.assertNotIn("honorific", "\n".join(errs))

    def test_units_keep_jp(self):
        """Every unit's (id, jp) is the ROM string for that id, including the tail after an 8-line sentence cut."""
        jp = batches.jp_tables()
        by = {k[:4]: v for k, v in jp.items() if k != "arm9"}
        a9 = dict(jp["arm9"])
        for u in batches.units():
            for sid, t in u[2]:
                a, b = sid.split(":")
                self.assertEqual(t, a9[b] if a == "a9" else by[a][int(b)], sid)


if __name__ == "__main__":
    unittest.main()
