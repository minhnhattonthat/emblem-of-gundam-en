"""Lint regressions and content audit. Full phase acceptance additionally requires tools/lint.py to exit zero;
the content audit explicitly separates known unresolved width research from translation correctness."""
import sys
import unittest
from unittest.mock import patch
import tempfile
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches  # noqa: E402
import build  # noqa: E402
import lint  # noqa: E402
import bbq  # noqa: E402
import extract  # noqa: E402


@unittest.skipUnless(build.ROM.is_file(), "no ROM")
class Lint(unittest.TestCase):
    def test_layout_spaces(self):
        for original, translated, good in [(" 選択", "Select", " Select"),
                                           ("　選択", "Select", " Select"),
                                           ("選択　 ", "Select ", "Select  ")]:
            jp = {"arm9": [["02076d98", original]]}
            errors, _ = lint.lint(jp, {"arm9": {"02076d98": translated}}, set())
            self.assertTrue(any("layout spaces" in e for e in errors), errors)
            errors, _ = lint.lint(jp, {"arm9": {"02076d98": good}}, set())
            self.assertEqual(errors, [])

    def test_speech_indent_follows_reflow_not_source_index(self):
        jp = {"0086_ST00STAGE": ["「見える、", "　まだ見える、", "　見える」"], "arm9": []}
        cur = {"0086_ST00STAGE": ['"I see it,', "", 'still see it."'], "arm9": {}}
        self.assertTrue(lint.continuation_spaces(jp, cur))
        cur["0086_ST00STAGE"][2] = '  still see it."'
        self.assertTrue(lint.continuation_spaces(jp, cur))
        cur["0086_ST00STAGE"][2] = ' still see it."'
        self.assertEqual(lint.continuation_spaces(jp, cur), [])
        cur["0086_ST00STAGE"] = ["", '"I see it, still see it."', ""]
        self.assertEqual(lint.continuation_spaces(jp, cur), [])

    def test_quoted_narration_does_not_acquire_speech_indent(self):
        jp = {"0086_ST00STAGE": ["「未来」と", "呼ばれるもの。"], "arm9": []}
        cur = {"0086_ST00STAGE": ['What we call "the future"', "is before us."], "arm9": {}}
        self.assertEqual(lint.continuation_spaces(jp, cur), [])

    def test_chart_footer_limit(self):
        jp = {"arm9": [["02076d98", "ステージを選択"]]}
        errors, _ = lint.lint(jp, {"arm9": {"02076d98": "W" * 30}}, set())
        self.assertTrue(any("chart_footer_hint" in e for e in errors), errors)

    def test_glossary_in_merged_script(self):
        jp = {"0086_ST00STAGE": ["アムロ", "「見える」"], "arm9": []}
        cur = {"0086_ST00STAGE": ["Amro", '"I see."'], "arm9": {}}
        errors, _ = lint.lint(jp, cur, set())
        self.assertTrue(any("avoid 'Amro'" in e for e in errors), errors)
        self.assertTrue(any("'Amuro' missing" in e for e in errors), errors)

    def test_reflow_cannot_erase_block(self):
        jp = {"0086_ST00STAGE": ["見える。"], "arm9": []}
        errors, _ = lint.lint(jp, {"0086_ST00STAGE": [""], "arm9": {}}, set())
        self.assertTrue(any("empty English block" in e for e in errors), errors)
        jp["0086_ST00STAGE"] = ["「……」"]
        errors, _ = lint.lint(jp, {"0086_ST00STAGE": [""], "arm9": {}}, set())
        self.assertTrue(any("empty English outside a reflow block" in e for e in errors), errors)
        jp["0086_ST00STAGE"] = ["「見える、", "　見える」"]
        cur = {"0086_ST00STAGE": ['"I can see it, I can see it."', ""], "arm9": {}}
        errors, _ = lint.lint(jp, cur, set())
        self.assertFalse(errors, errors)

    def test_coverage_cannot_skip_new_id(self):
        jp = {"arm9": [["02072150", "ユニットの売却"], ["02072160", "ユニットの購入"]]}
        errors, _ = lint.lint(jp, {"arm9": {"02072160": "Buy Units"}}, set())
        self.assertTrue(any("coverage mismatch" in e for e in errors), errors)

    def test_disk_cache_cannot_hide_new_extraction(self):
        with tempfile.TemporaryDirectory() as d:
            stale = Path(d) / "jp.json"
            stale.write_text(json.dumps({"arm9": []}), encoding="utf-8")
            batches.jp_tables.cache_clear()
            with patch.object(batches, "JP_CACHE", stale):
                self.assertIn("02072150", dict(batches.jp_tables()["arm9"]))
                self.assertIn("02072160", dict(batches.jp_tables()["arm9"]))

    def test_script_content_apart_from_width_coverage(self):
        errs, _ = lint.lint(require_measured=False)
        self.assertEqual(errs, [], "\n" + "\n".join(errs[:30]))

    def test_unknown_width_fails_phase_gate(self):
        jp = {"arm9": [["0207ffff", "新しい項目"]]}
        errors, _ = lint.lint(jp, {"arm9": {"0207ffff": "Future Item"}}, set())
        self.assertTrue(any("unmeasured width budget" in e for e in errors), errors)

    def test_map_name_cannot_overrun_native_copy(self):
        jp = {"0060_MAP01": ["荒地"], "arm9": []}
        cur = {"0060_MAP01": ["i" * 32], "arm9": {}}
        errors, _ = lint.lint(jp, cur, set())
        self.assertTrue(any("31-byte native text field" in e for e in errors), errors)

    def test_gallery_native_return_cannot_overrun_vm_string(self):
        jp = {"0013_EVMOVTABLE": ["空中"], "arm9": []}
        cur = {"0013_EVMOVTABLE": ["i" * 32], "arm9": {}}
        errors, _ = lint.lint(jp, cur, set())
        self.assertTrue(any("31-byte native text field" in e for e in errors), errors)

    def test_description_exclusions_match_record_fields(self):
        _, table, data = extract._load(build.ROM.read_bytes())
        files = extract.bbq_files(table, data)
        rules = lint.budgets()
        for table_id, stride, variant in [(3, 0x24, "char_desc"), (5, 0x34, "unit_desc")]:
            name, raw, strings = files[table_id]
            records = next(s for s in bbq.sections(raw) if s["type"] == 5)
            expected = {2} | {struct.unpack_from("<I", raw, records["data"] + off + 8)[0]
                              for off in range(0, records["size"], stride)}
            stem = extract.stem(table_id, name)
            actual = {i for i, j in enumerate(strings)
                      if next(n for match, n, _ in rules if match(f"{stem}:{i:04d}", j)) == variant}
            self.assertEqual(actual, expected, variant)

    def test_exclusion_needs_evidence_and_preserves_other_checks(self):
        with self.assertRaises(ValueError):
            lint.width_excluded({"excluded": True})
        jp = {"0003_SETABLE": ["", "", "アムロの説明"], "arm9": []}
        cur = {"0003_SETABLE": ["", "", "Amro %d"], "arm9": {}}
        errors, _ = lint.lint(jp, cur, set())
        self.assertTrue(any("codes" in e for e in errors), errors)
        self.assertTrue(any("avoid 'Amro'" in e for e in errors), errors)
        self.assertFalse(any("unmeasured" in e for e in errors), errors)

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
