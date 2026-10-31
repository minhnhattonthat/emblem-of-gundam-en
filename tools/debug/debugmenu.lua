-- Re-enable the leftover debug item in the map command menu (QA only, never in the release build).
-- arm9 0x02029678 `cmp r8, #4` limits the menu loop to 5 items (ターン終了..ギブアップ); the 6th, デバッグ
-- (string 37, table 0x02070D44[5]), runs 0x02032890 (docs/re/debug.md). #5 shows it.
L.on_frame(function(n)
  if memory.readdword(0x02029678) == 0xE3580004 then memory.writedword(0x02029678, 0xE3580005) end
end)
