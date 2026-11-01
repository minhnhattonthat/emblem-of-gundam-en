-- Scene list for warp.lua (format in its header). All scenes start in the developer main menu (script 0x1000):
--   0 ゲーム開始(ロゴ～)  1 ゲーム開始(タイトル～)  2 ゲーム開始(ステージ??～) -> stage list ST00-ST67 -> phase
--   (0 オープニング / 1 戦闘 / 2 エンディング)  3 戦闘演出動画ビュア  4 イベント動画ビュア  5 マップビュア
--   6 システムフラグ操作  7 オプション設定  8 スタッフ ロール
-- Stage NN = title card NN (68 cards, proof sheets work/qa/warps/sheet_open*.png); ST06 is a scrapped stage.
SCENES = {}
local MENU = { "script", 0x1000 }

local function menu(item, ...)
  -- 180 frames: the dev menu is drawn at f~23 but ignores input for about a second on a slow boot, dropping the
  -- presses silently. Don't retry by pressing A until the script changes: the submenus (flags, options, name entry)
  -- run inside script 0x1000, so a retry would just drive them.
  local s = { MENU, { "wait", 180 } }
  if item > 0 then s[#s + 1] = { "press", "down", item } end
  s[#s + 1] = { "press", "a" }
  s[#s + 1] = { "wait", 30 }
  for _, x in ipairs({ ... }) do s[#s + 1] = x end
  return s
end

-- stNN_open / stNN_battle / stNN_end: stage jump, the way the game enters the stage (card + intro). Booted straight
-- into the stage list (script 0x1002) instead of going through the dev menu: fewer dropped-input retries, and the
-- list's cursor starts at ST00.
local function stage_ok(k) return k ~= 6 end  -- ST06 (没ステージ): no opening; battle/end jump to ST07/ST08
for k = 0, 67 do
  if stage_ok(k) then for ph, name in pairs({ [0] = "open", [1] = "battle", [2] = "end" }) do
    local steps = { boot = 0x1002, { "script", 0x1002 }, { "wait", 60 } }
    if k > 0 then steps[#steps + 1] = { "press", "down", k } end
    steps[#steps + 1] = { "press", "a" }
    steps[#steps + 1] = { "wait", 60 }
    if ph > 0 then steps[#steps + 1] = { "press", "down", ph } end
    steps[#steps + 1] = { "leave", 0x1002 }  -- route questions (ST05 B/D, ST16 F/G, ...): first option each
    SCENES[string.format("st%02d_%s", k, name)] = steps
  end end
end

local PREP, MAPMENU = 0x02070EB0, 0x02070D44  -- item tables read when the menu opens
local function extend(base, extra, god)
  local s = { god = god, boot = SCENES[base].boot }
  for _, x in ipairs(SCENES[base]) do s[#s + 1] = x end
  for _, x in ipairs(extra) do s[#s + 1] = x end
  return s
end

-- Battle prep (戦闘準備) and its screens: ST30 has every item enabled (ST00 greys most out).
for k = 0, 67 do
  if stage_ok(k) then
    SCENES[string.format("st%02d_prep", k)] =
      extend(string.format("st%02d_battle", k), { { "read", PREP, { "a", "b" } } })
  end
end
SCENES.prep_mapcheck = extend("st30_prep", { { "press", "a" } })              -- マップ確認
SCENES.prep_team = extend("st30_prep", { { "press", "down" }, { "press", "a" } })  -- オリジナル隊編成
SCENES.shop = extend("st30_prep", { { "press", "down", 2 }, { "press", "a" } })   -- 強化メニュー
SCENES.prep_brief = extend("st30_prep", { { "press", "down", 3 }, { "press", "a" } }) -- 作戦内容確認
-- briefNN: the same win/lose screen on stage NN (width/byte-cap checks of each stage's condition strings)
for k = 0, 67 do
  if stage_ok(k) then
    SCENES[string.format("brief%02d", k)] =
      extend(string.format("st%02d_prep", k), { { "press", "down", 3 }, { "press", "a" } })
  end
end
SCENES.chart = extend("st30_prep", { { "press", "down", 4 }, { "press", "a" } })  -- シナリオチャート
SCENES.save = extend("st30_prep", { { "press", "down", 5 }, { "press", "a" } })   -- セーブ
-- Map: start the battle, then open the map command menu (A on an empty cell), with its デバッグ item.
SCENES.map = extend("st30_prep", { { "press", "up" }, { "press", "a" }, { "wait", 400 } })
SCENES.map_team = extend("map", { { "press", "x" }, { "wait", 120 } }, true)  -- team info (0444 atlas)
SCENES.map_chara = extend("map", { { "press", "y" }, { "wait", 120 } }, true) -- character info (0444 atlas)
SCENES.map_unit = extend("map_chara", { { "press", "down" }, { "wait", 30 }, { "press", "left" }, { "wait", 120 } }, true) -- unit info (0444 atlas)
SCENES.mapmenu = extend("map", { { "press", "right", 30 }, { "read", MAPMENU, { "a" } } }, true)
SCENES.debugmenu = extend("mapmenu", { { "press", "down", 5 }, { "press", "a" } }, true)
SCENES.victory = extend("debugmenu", { { "wait", 30 }, { "press", "a" }, { "wait", 30 }, { "press", "a" } }, true)
SCENES.gameover = extend("debugmenu", { { "wait", 30 }, { "press", "a" }, { "wait", 30 }, { "press", "down" },
  { "press", "a" }, { "wait", 200 }, { "press", "a" }, { "wait", 60 }, { "press", "a" } }, true)

SCENES.devmenu = { MENU }
SCENES.messagetest = { boot = 0x1006, { "script", 0x1006 } }  -- leftover 画面呼び出しテスト: message windows, save/load
SCENES.logo = menu(0)
SCENES.title = menu(1, { "script", 0x1040 })                        -- PRESS START
SCENES.title_menu = extend("title", { { "wait", 120 }, { "press", "start" } })
SCENES.load = extend("title_menu", { { "wait", 60 }, { "press", "down", 2 }, { "press", "a" } })
-- おまけ (extras): system flags -> おまけコンプリート -> はい, back, then title -> おまけ.
SCENES.extras = menu(6, { "wait", 30 }, { "press", "down" }, { "press", "a" }, { "wait", 30 }, { "press", "left" },
  { "press", "a" }, { "wait", 90 }, { "press", "b" }, { "wait", 60 }, { "press", "up", 6 }, { "press", "down" },
  { "press", "a" }, { "script", 0x1040 }, { "wait", 120 }, { "press", "start" }, { "wait", 60 },
  { "press", "down", 3 }, { "press", "a" })
SCENES.battle_movies = menu(3)
SCENES.event_movies = menu(4)
SCENES.mapview = menu(5)
SCENES.sysflags = menu(6)
SCENES.options = menu(7)
SCENES.credits = menu(8)
