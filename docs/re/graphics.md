# Graphics text survey

Static sweep (phase 1): every NCGR in the archive (584) rendered with its neighbouring NCLR/NSCR by
`tools/nitro2d.py survey` -> `work/gfx/<id>.png` + 98 contact sheets, read by three read-only reviewer subagents
(2026-11-01). Nothing skipped (`work/gfx/skipped.txt` empty). Sheets crop each image at 512x256; the reviewers said
screen content sits in the top-left ~256x192 of each 512x512 map, but lower atlas halves were not all opened (risk).
In-game tour of the marker build (phase 5/8) must add any screen missing here. Archive ids = `work/ez/NNNN.bin`.

Edit path for all rows: NCGR tiles (+ NSCR map) inside the EZ archive, LZ10-recompressed by the archive writer.

## Japanese drawn as graphics (to translate, D5)
| id(s) | text | kind | notes |
|---|---|---|---|
| 1111-1312 (every 3rd id, 68 cards) | stage title cards: オープニングセレモニー, 小さな戦い ... 帰るべき処 (full list matches BBQ 0000 stage names plus 三つ巴, 倒れる巨神, 帰るべき処) | NSCR screen, 512 wide for 1150/1270 | series logo bottom right (Gundam / 08th MS Team / 0080 / 0083 / Zeta) with small JP inside the logo art; caption is the translatable part. Logos: keep official logo art unless an official English logo exists (D5). 1129 shows only "06" (unused test stage). |
| 0375 | ステージ情報, ターン, 物資量(x3), 武器補正, 攻撃補正, 防御補正, 地形属性 | stage info screen | EN "AREA INFO", "TEAM", "UNIT" already there |
| 0378 | 戦闘結果予測, 戦闘前, 戦闘後 (several colours), 機 | battle forecast panel | |
| 0444 | チーム情報, 機数, 武器補正, 攻撃補正, 防御補正, 地形属性, 物資量, terrain strip 隠蔽/水/空/宇 | team info screen atlas | EN RESULT/CHARA/AREA present; strips repeat in the lower atlas half |
| 0450 | シナリオ メニュー, シナリオの流れを確認できます, (B) 戻る | scenario menu screen | button captions are drawn as text, not baked |
| 0340 | small kanji labels among map/battle UI icons and digits | tile sheet (sprites, RECN 0343) | read zoomed in phase 8 |
| 0344 | 前進 / 後退 (approx) + other kanji, big digits | tile sheet (sprites, RECN 0347) | EN "ATION", "NEUTRAL" bar labels |
| 0402 | 建物 (x2) beside LAND_06 | terrain label | looks like debug/placeholder; check whether shown |
| 0360 / 0372 | title: "EMBLEM of GUNDAM" logo (English) + エンブレム オブ ガンダム katakana subtitle; © 創通・サンライズ | title screen | logo is already English; subtitle reading: translate/remove per D5; © line: "© SOTSU・SUNRISE" |
| 2121 | 株式会社 バンダイナムコゲームス under "Produced by" | credit card | -> "BANDAI NAMCO Games Inc." |

| ? (found in phase 8) | 勝利条件 / 敗北条件 green/purple banners on the win/lose condition screen | briefNN scene | not in the static sweep: source to find (sprite? NCER) |

Done in the build (`tools/gfx.py`): the 68 cards (1129 "06" kept), 0375, 0378, 0450 labels.

## Already English (no work)
0363 "No Data" save cards, 0366 "Please choose data performing reading ...", 0381 TEAM/AREA/POWER BALANCE,
0453/0456 OFFENSE/DEFENSE SIDE ATTACK, 0459/0462/2118 publisher logos, 1429-1444 faction cards (Earth Federation
Space Force, Principality of Zeon, AEUG, Titans, "Delaz Freet" [sic, official art], AXIS), 1357 street sign.

## No text
0467-0938 character portraits, 0348-0432 terrain/backgrounds, 1315-1426 backgrounds/maps, 1447-1534 and 1537-1894
event stills, 1899-2115 map/terrain tiles and mecha vignettes.

## Fonts
No glyph font among the NCGRs; text is drawn from the NFTR fonts 0336/0337 (`font.md`).
