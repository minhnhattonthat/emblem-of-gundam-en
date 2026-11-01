-- Read-only allocation guard for native text-surface QA (QA fork exec hooks also work with JIT).
-- 02044a60 is the allocator's exhausted/uninitialized-pool return, before r0 is cleared.
L.on_exec(0x02044a60, function()
  L.fail(string.format("native allocation failed: pool=%08X requested=%d tiles pc=%08X",
    memory.getregister("arm9.r6"), memory.getregister("arm9.r5"), L.pc()))
end)
