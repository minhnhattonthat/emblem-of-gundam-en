# Debug tool: developer menu, stage jump, script engine

## Script engine (verified: Lua exec/read hooks under --debugger, 2026-11-01)
- Game flow runs as BBQ scripts (type-6 bytecode, `tools/vmdump.py`). EZ file id = `group << 12 | index`;
  entry = group base + index (group bases: g0 0, g1 17, g2 336, g3 340, g4 354, g5 467, g6 1111, g7 1899,
  g8 2091, g9 2126, g10 2248, g11 2516, g12 2944, g13 4132). Lookup 0x0203BC00, whole-file load 0x0203BD34.
- 0x02042850 switch to script r0 (loads it via 0x02048970 into ctx 0x02196818, buffer 0x02206818);
  u16 0x02197100 = current script id, u16 0x02197102 = pending jump (run by 0x0204298C), call/return stack
  0x02197104 (0x020429D8 / 0x02042A08).
- Boot init 0x02022D54 starts script 0x1042 (the master flow) from the literal at **0x02022DAC**.
- Normal New Game: 0x1042 -> 0x103E (tutorial? prompt) -> 0x1042 -> 0x1044 (ST00 intro).
- Stage scripts sit in group 1 from 0x1044 in groups of 3-4: intro (story text), battle (string 0
  `シナリオ名未設定`), small result script (`名称未設定`), optional event script (type 3/6/7 only). ST00 intro
  0x1044, ST01 intro 0x1047, ST05 0x1055 (seen in warps). Swapping only the script id plays the new text under
  the old stage card, so stage state lives outside the script id: use the stage jump below.

## Developer main menu (verified: warp_all 2026-11-01, all 68 stage cards shown from cold boot)
Script **0x1000** (BBQ 0017, also 0x1001 = 0018 with the system-flag submenu). Reached by writing 0x1000 to
0x02022DAC before frame ~29 (`tools/debug/devmenu.lua`, `warp.lua`); no ROM change. Items:
0 ゲーム開始(ロゴ～), 1 ゲーム開始(タイトル～), 2 ゲーム開始(ステージ??～) (script 0x1002, stage list ST00-ST67
then phase オープニング/戦闘/エンディング; later stages first ask each route branch, e.g. ST05 B 宇宙軍/D 地上軍,
ST16 F 東アジア/G 東南アジア), 3 戦闘演出動画ビュア, 4 イベント動画ビュア, 5 マップビュア, 6 システムフラグ操作
(フラグ個別ON, おまけコンプリート, 全てOFF, カードへ書き込み), 7 オプション設定, 8 スタッフ ロール, then
実験ステージ00 and developer test rooms (小山さんち ...). Menu input: 4 frames on / 4 off works.

Other leftover test scripts: 0x1006 画面呼び出しテスト (message window, full-screen message, result, save/load
test, tutorial cursor...), 0x1009 テスト開始, 0x100B イベント画像チェック.

## Warp tool (`tools/debug/`)
`warp.lua` + `scenes.lua`: boot to the dev menu, then steps (menu presses, wait for a script id, or wait until
the game reads a menu's item table: battle prep 0x02070EB0, map menu 0x02070D44; Lua read hooks fire under
JIT). `warp_all.py` runs every scene, saves `work/states/<scene>.dst`, a named proof shot and sheets per group.

The stage scenes boot **straight into the stage-jump list** (script 0x1002, `scenes.lua` sets `boot = 0x1002`)
instead of pressing through the dev menu: the dev menu is drawn at f~23 but ignores input for another second on a
slow boot, so its first presses were silently dropped and ~1 warp in 3 hung. Scenes that need the dev menu use the
`{"menu", N}` step, which re-runs "up to the top, down N, A" until the script leaves 0x1000.
Scenes: `stNN_open|battle|end|prep` (NN 00-67), battle-prep screens (`prep_mapcheck prep_team shop prep_brief
chart save`, on ST30 where all are enabled), `map mapmenu debugmenu victory gameover` (ST30, map menu with
デバッグ), `title title_menu load extras` (extras unlocked through system flags → おまけコンプリート), `logo
credits battle_movies event_movies mapview sysflags options devmenu`.
Gotchas: emu.py `--mash` presses whenever the press queue is empty, so warp.lua holds MASH (and FRAMES) back
until WARP_DONE. Battle phase of a later stage first asks every route branch; the warp takes the first option.
Game input: map menu = A on an empty cell, X = team edit, Y = character info; the win/lose conditions screen
closes with B.

## Map command menu debug item (verified: shown and used in the `debugmenu`/`gameover` warps)
Map menu 0x02029598 builds items from string ids at 0x02070D44 (31 ターン終了, 32 作戦内容確認, 33 シナリオチャート,
34 セーブ, 35 ギブアップ, 37 デバッグ); `cmp r8, #4` at **0x02029678** stops before デバッグ. Writing 0xE3580005
there (`debugmenu.lua`, warp `GOD=1`) adds it; it runs 0x02032890: 強制終了 (勝利/敗北), イベントトリガー,
キャラレベル操作, 適正レベル設定, オプション (自軍/敵軍ダメージ 有効/無効), 未行動に戻す, supply ±100.
Strings 0x02072914-0x02072B18, tables 0x02072790-0x02072808.
