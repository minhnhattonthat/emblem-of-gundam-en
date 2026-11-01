-- Warp to a scene from a cold boot through the developer menu left in the game (docs/re/debug.md).
--   emu.py ROM --out D --script tools/debug/scenes.lua --script tools/debug/warp.lua --var "SCENE='st01_open'"
--          --frames 900 --sheet   (frames count from the moment the scene is reached; see WARP_DONE in log.txt)
-- Boot: the literal 0x1042 at 0x02022DAC (first script) is swapped for the scene's boot script: 0x1000 (the dev
-- main menu) by default, or 0x1002 (its stage-jump list) for the stage scenes, which then need no menu presses at
-- all -- the dev menu sometimes drops the first presses while it fades in (scenes.lua sets `boot`). Each scene in
-- scenes.lua is a list of steps run in order:
--   { "script", ID }     wait until the current script (u16 0x02197100) is ID, then 30 frames
--   { "menu", N }        pick developer-menu item N (0-based): up to the top, down N, A, repeated until the
--                        script leaves 0x1000 (a slow boot drops the first presses while the menu is still fading in)
--   { "press", SPEC, N } press SPEC (emu.py route button spec) N times, 4 frames on / 4 off (default N = 1)
--   { "leave", ID, SPEC } press SPEC (default a) every 40 frames until the current script is no longer ID
--   { "read", ADDR, {SPEC..} } press the SPECs in turn, 40 frames apart, until the game reads ADDR (menus read
--                        their item table when they open: 0x02070EB0 battle prep, 0x02070D44 map menu)
--   { "wait", F }        idle F frames
--   { "poke", ADDR, V }  write a u32
-- GOD=1 also loads debugmenu.lua's patch (map menu デバッグ item, with damage toggles).
-- The run's --frames counts from boot; the driver's FRAMES is shifted when the scene is reached, so --frames is
-- "frames to run after the warp". log.txt gets "WARP_DONE f<N> script <ID>".
local CUR = 0x02197100
local sc = SCENES[SCENE or ""]
if not sc then L.fail("unknown SCENE " .. tostring(SCENE) .. " (tools/debug/scenes.lua)") end
local after, mash = FRAMES, MASH
FRAMES = 1e9  -- the driver stops at FRAMES; re-armed once the warp is done (emu.py --timeout still applies)
MASH = nil    -- --mash presses whenever the press queue is empty: hold it back until the warp is done
local i, waitf, lastcur = 1, 0, -1
local BOOT = sc.boot or 0x1000

L.on_frame(function(n)
  if memory.readdword(0x02022DAC) == 0x1042 then memory.writedword(0x02022DAC, BOOT) end
  if (GOD or sc.god) and memory.readdword(0x02029678) == 0xE3580004 then memory.writedword(0x02029678, 0xE3580005) end
  local cur = memory.readword(CUR)
  if cur ~= lastcur then L.log(string.format("f%d script %04X", n, cur)); lastcur = cur end
  if i > #sc then return end
  if waitf > 0 then waitf = waitf - 1; return end
  if not L.route_done() then return end
  local s = sc[i]
  if s[1] == "script" then
    if cur ~= s[2] then return end
    waitf = 30
  elseif s[1] == "menu" then  -- select item N in the developer menu; retry until it leaves 0x1000
    -- A slow boot leaves the menu drawn but not yet listening (input dropped at f~50), so re-run the selection:
    -- up to the top (up clamps there), down N, A. Harmless when it had already worked: the script id changes
    -- and the next frame advances the step past the queued presses.
    if cur == 0x1000 then
      for _ = 1, 9 do L.press("up", 4); L.press("-", 4) end
      for _ = 1, s[2] or 0 do L.press("down", 4); L.press("-", 4) end
      L.press("a", 4)
      L.press("-", 56)
      return
    end
  elseif s[1] == "press" then
    for _ = 1, s[3] or 1 do L.press(s[2], 4); L.press("-", 4) end
  elseif s[1] == "leave" then  -- press SPEC every 40 frames while the current script is still ID
    if cur == s[2] then L.press(s[3] or "a", 4); L.press("-", 36); return end
  elseif s[1] == "read" then  -- cycle presses s[3] (40 frames apart) until the game reads ADDR (a menu table)
    if not s.hooked then
      s.hooked, s.k = true, 0
      L.on_read(s[2], s[2] + 1, function() s.hit = true end)
    end
    if not s.hit then
      local keys = s[3] or { "-" }
      s.k = s.k % #keys + 1
      L.press(keys[s.k], 4); L.press("-", 36)
      return
    end
    waitf = 30
  elseif s[1] == "wait" then
    waitf = s[2]
  elseif s[1] == "poke" then
    memory.writedword(s[2], s[3])
  else
    L.fail("bad step " .. tostring(s[1]))
  end
  i = i + 1
  if i > #sc then
    L.log(string.format("WARP_DONE f%d script %04X", n, cur))
    FRAMES = n + (after or 900)
    MASH = mash
  end
end)
