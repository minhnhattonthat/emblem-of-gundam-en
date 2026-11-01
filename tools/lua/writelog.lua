-- Log every write to WATCH_LO..WATCH_HI (not deduplicated): frame, pc, lr, address, value. NDS (DeSmuME); run with
-- --debugger so pc is exact (the JIT reports block starts).
--   emu.py ROM ... --debugger --script tools/lua/writelog.lua --var WATCH_LO=0x2206ba8 [--var WATCH_HI=..] [--var FROM=N]
local lo = assert(WATCH_LO, "set --var WATCH_LO=0x...")
local hi, from, n = WATCH_HI or lo, FROM or 0, 0
L.on_write(lo, hi, function(addr, size)
  if L.frame < from or n > 400 then return end
  n = n + 1
  L.log(string.format("f%d pc=%08X lr=%08X addr=%08X size=%s r0=%08X r1=%08X r2=%08X", L.frame, L.pc(),
    memory.getregister("arm9.r14"), addr or 0, tostring(size), memory.getregister("arm9.r0"),
    memory.getregister("arm9.r1"), memory.getregister("arm9.r2")))
end)
