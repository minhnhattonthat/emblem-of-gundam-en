-- Probe: log every EZ archive lookup (0x0203BC00, r0 = file id group<<12|index) with the caller (lr).
-- Run with --debugger: JIT exec hooks can miss function entries (emulator-qa.md §DeSmuME).
local last = nil
L.on_exec(0x0203BC00, function()
  local id = memory.getregister("arm9.r0")
  local lr = memory.getregister("arm9.r14")
  local k = string.format("%04X %08X", id, lr)
  if k ~= last then L.log(string.format("f%d ez %s", L.frame, k)); last = k end
end)
-- 0x0203BDAC = load-group wrapper (r0 id): graphics sets
L.on_exec(0x0203BDAC, function()
  L.log(string.format("f%d gload %04X lr %08X", L.frame, memory.getregister("arm9.r0"), memory.getregister("arm9.r14")))
end)
-- 0x0203BD34 = load-whole-file wrapper (r0 id, r1 dest); its lr is the real caller.
L.on_exec(0x0203BD34, function()
  L.log(string.format("f%d load %04X lr %08X", L.frame, memory.getregister("arm9.r0"), memory.getregister("arm9.r14")))
end)
