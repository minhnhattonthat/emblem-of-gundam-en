-- Log the script VM's string-temp allocation (0x0204640C: push a frame entry of size r3, copy r3 bytes from r1).
-- Per call: frame, size (r3), source (r1), the VM code pointer (ctx+0x0C) and the code words just before it.
--   emu.py ROM ... --debugger --script tools/lua/vmalloc.lua [--var FROM=N]
local from, n = FROM or 0, 0
local function hex_words(at, count)
  local t = {}
  for i = 0, count - 1 do t[#t + 1] = string.format("%x", memory.readdword(at + 4 * i)) end
  return table.concat(t, " ")
end
memory.registerexec(0x0204640C, 4, L.safe(function()
  if L.frame < from or n > 300 then return end
  local ctx = memory.getregister("arm9.r0")
  local src, size = memory.getregister("arm9.r1"), memory.getregister("arm9.r3")
  if size <= 4 then return end  -- ints; strings are what overflow
  n = n + 1
  local pc = memory.readdword(ctx + 0x0C) + memory.readdword(ctx + 0x08)
  local s = ""
  if src ~= 0 then
    for i = 0, math.min(size, 40) - 1 do
      local b = memory.readbyte(src + i)
      if b == 0 then break end
      s = s .. (b >= 32 and b < 127 and string.char(b) or ".")
    end
  end
  L.log(string.format("f%d size=%d src=%08X vmpc=%08X code[-6..+2]=%s %q", L.frame, size, src, pc,
    hex_words(pc - 24, 8), s))
end))
