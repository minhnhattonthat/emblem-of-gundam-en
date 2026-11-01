-- QA-only native notification/selector ruler, after scenes.lua and before warp.lua.
-- Use SCENE='map', --debugger, --frames 1200. The native toast expires after 120 frames;
-- this captures it 60 frames after entry. No release ROM bytes are changed.
-- Current translated ITCM autoload ends at 01ff97e4; this guard also checks the scratch.
local code = {
  0xe92d5fff, 0xe10f4000, 0xe92d0030, 0xe3a00001, 0xe59f1020, 0xeb009010,
  0xe59f401c, 0xe59f501c, 0xe5845000, 0xe8bd0030, 0xe128f004, 0xe8bd5fff,
  0xe92d4010, 0xea013a1e, 0x01fff800, 0x0204d8b0, 0xe92d4010,
}
-- Save registers/flags, call 0202305c(mode=1,text), restore the one-shot branch,
-- replay AreaInfoUpdater's displaced push, and resume at 0204d8b4.
local armed = false
L.on_exec(0x01fff000, function()
  L.log("WIDTH: native UI probe entered")
  FRAMES = L.frame + (BASKET_PROBE and 1200 or 60)
end)
L.on_frame(function(n)
  if armed or FRAMES >= 1e9 then return end
  if memory.readdword(0x0204d8b0) ~= 0xe92d4010 then
    L.fail("notification probe: unexpected AreaInfoUpdater preimage")
    return
  end
  for at = 0x01fff000, 0x01fff8fc, 4 do
    if memory.readdword(at) ~= 0 then L.fail("notification scratch is not free"); return end
  end
  local text = NOTIFICATION_TEXT or "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
  if BASKET_PROBE then
    -- Native162 wrapper0205a4d8 passes a zero-mode structure to02057730.
    -- The normal constructor allocates its own0x8c object; scratch is only the input.
    text = ""
    code[4], code[5] = 0xe59f0024, 0xe3a01000
    code[6] = 0xeb000000 + (0x02057730 - 0x01fff01c) / 4
  end
  if #text > 255 then L.fail("notification text exceeds probe storage"); return end
  for i, word in ipairs(code) do memory.writedword(0x01fff000 + (i - 1) * 4, word) end
  for i = 1, #text do memory.writebyte(0x01fff800 + i - 1, string.byte(text, i)) end
  memory.writebyte(0x01fff800 + #text, 0)
  memory.writedword(0x0204d8b0, 0xeafec5d2)
  armed = true
  L.press("right", 4)
  L.log("WIDTH: native UI one-shot armed at frame " .. n)
end)
