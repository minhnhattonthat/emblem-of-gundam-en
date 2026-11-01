-- QA-only capture route: normal assignment purchase, then retire that real pool entry.
-- Load before warp.lua with SCENE='prep_assign', --frames 3600 (QA fork exec hooks support JIT).
-- Static call-path review: docs/re/retirement-route.md. This is not a return-to-game route.
local armed, character_at, unit_at = false, nil, nil
L.on_exec(0x0202ae98, function() L.log("RETIRE: purchased character") end)
L.on_exec(0x02052a94, function()
  L.log(string.format("RETIRE: native entry mask=%d chars=%d units=%d",
    memory.getregister("arm9.r1"), memory.readbyte(0x02196108), memory.readbyte(0x02196109)))
end)
L.on_exec(0x02052030, function()
  if not character_at then character_at = L.frame; L.log("RETIRE: character heading drawn") end
end)
L.on_exec(0x02052404, function()
  if not unit_at then unit_at = L.frame; FRAMES = L.frame + 1200; L.log("RETIRE: unit heading drawn") end
end)
L.on_frame(function(n)
  if not armed and FRAMES < 1e9 then
    local map = memory.readdword(0x021986d8)
    -- WARP_DONE finishes queued input, before the asynchronous assignment task is necessarily drawn.
    if memory.readdword(0x021918f4) ~= 2 or memory.readword(map + 0x2b56c) ~= 62 then
      if n == FRAMES - 1 then L.fail("assignment task did not become ready") end
      return
    end
    if memory.readword(0x02195b22) ~= 0
        or memory.readbyte(0x02196108) ~= 0 or memory.readbyte(0x02196109) ~= 0 then
      L.shot("unexpected.png")
      L.fail(string.format("retirement fixture: mode=%d first=%d merit=%d char=%d unit=%d map=%08X",
        memory.readdword(0x021918f4), memory.readword(map + 0x2b56c), memory.readword(0x02195b22),
        memory.readbyte(0x02196108), memory.readbyte(0x02196109), map)); return
    end
    for _, patch in ipairs({{0x02030258, 0xe3a00001, 0xe3a01000},
                            {0x020302c0, 0xeb001fb4, 0xeb0089f3}}) do
      if memory.readdword(patch[1]) ~= patch[2] then L.fail("retirement preimage mismatch"); return end
    end
    memory.writeword(0x02195b22, 45)
    memory.writedword(0x02030258, 0xe3a01000)
    memory.writedword(0x020302c0, 0xeb0089f3)
    armed = true
    FRAMES = n + 4200
    L.press("-", 180); L.press("a", 4); L.press("-", 240); L.press("a", 4); L.press("-", 180)
    L.press("b", 4)
    L.log("RETIRE: funded first purchase and armed return redirect")
  end
  if character_at and n == character_at + 1200 then
    L.shot("characters.png")
    L.press("a", 4)
  end
  if armed and n == FRAMES - 1 and not unit_at then
    L.shot("failed.png"); L.fail("retirement headings were not both reached")
  end
end)
