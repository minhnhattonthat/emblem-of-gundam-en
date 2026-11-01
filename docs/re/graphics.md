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

| ? (found in phase 8) | 勝利条件 / 敗北条件 green/purple banners on the win/lose condition screen | briefNN scene | not in BG or OAM: engine A BG0 is the **3D layer** (DISPCNT bit 3 in every UI scene), so these are textured quads from `\0DLG` files (below) |
| 0444 other quadrants | the 0446 NSCR is 512x512 = 4 screens: TL team info (done), **BL 編成チーム情報** (prep_team: 攻戦/防戦/移動/消費/補給, 陸荒水空宇), TR and BR (other team screens) | NSCR atlas | add rects at y >= 256 / x >= 256 to `gfx.LABELS[444]`; coordinates = shot + (0,256) for BL |
| 0340 cells 12-17, 0344 cells 10-12, 25-26 | 攻 防 移 消 補 機 icons; 前進 / 後退 / 連戦, 攻 / 防 | OBJ cells (NCER 0343 / 0347, 4bpp 1D, cells listed by `ncer.py`-style render) | single-kanji icons beside English labels |

## `\0DLG` textures (found phase 8, 2026-11-01): NOT 3D models
The 1019 `\0DLG` files (ids 2127-4171, odd) are **textures** for the 3D layer, each paired with the `\0LGA` file
before it (layout: quads with anchor, size, UVs). DLG header: u32 magic `\0DLG`, u32 1, u32 total size, 2 x u32 0,
u32 pixel bytes P, u32 palette bytes L; pixels at 0x1c, then the BGR555 palette. LGA u16 at 0x34 = texture width
(256/512; 0 in some). Format not fully decoded: palette sizes of 200/136 colours suggest several sub-textures per
file (table in the LGA). Clear cases:
- **4137-4169 (17 files): staff roll pages**, 256x192 4bpp 16 colours, Japanese roles and names (【脚本】 芝村 裕吏 ...)
  as white serif text. 4133/4135/4171 blank/plain. **Done** (`tools/dlg.py`, in the build, seen in-game
  `work/qa/credits_en/`).
- UI group finds so far: 2197 戦闘開始, 2199 戦闘結果, 2203/2205 スキル発動 + ユニットスキル/キャラクタースキル,
  2233 勝利条件/敗北条件 banners, 2235 result panel (戦果合計/獲得ポイント...), 2245 選択 banners; 2193/2239/2243 small
  text to zoom. These hold several sub-textures of different widths packed back to back (2233 at width 256 shows
  the banner rows shifted), so each needs its (byte offset, width) found before editing; the LGA tail has UV rects.
- **2127-2245 (UI group g9):** win/lose and result banners, 2203/2205 スキル習得 panels, "MISSION CLEAR / FAIL",
  "DELAZ FLEET" bars, buttons... to survey at the right width/format.
- 2248-4131 (g10-g12): unit battle sprites and cut-ins (to survey for text).

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
