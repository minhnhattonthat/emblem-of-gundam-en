-- Boot into the developer main menu left in the game (QA only, never in the release build).
-- Boot init (0x02022D88) starts script 0x1042 from the literal at 0x02022DAC; writing DEV there before frame ~29
-- boots script DEV instead (default 0x1000 = メインメニュー: start from logo/title/stage ??, movie viewers, map
-- viewer, system flags, options, staff roll). A data word, so it works under JIT, no --debugger.
-- Harmless after boot / on savestates (the literal is read once). Notes: docs/re/debug.md.
L.on_frame(function(n)
  if memory.readdword(0x02022DAC) == 0x1042 then memory.writedword(0x02022DAC, DEV or 0x1000) end
end)
