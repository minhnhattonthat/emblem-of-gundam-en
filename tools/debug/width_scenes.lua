-- Targeted native-UI width routes. Load after scenes.lua and before warp.lua.
-- Keep these probes separate from the complete normal-build tour's stable scene list.
local function follow(base, extra)
  local route = { boot = SCENES[base].boot, god = SCENES[base].god }
  for _, step in ipairs(SCENES[base]) do route[#route + 1] = step end
  for _, step in ipairs(extra) do route[#route + 1] = step end
  return route
end

-- QA-only: hold the basket selector after its normal constructor has drawn it.
if HOLD_BASKET then
  L.on_frame(function()
    if memory.readdword(0x02057424) == 0xe5970084 then
      memory.writedword(0x02057424, 0xe3a00001)
      L.log("WIDTH: basket input held; constructor and drawing unchanged")
    end
  end)
end
SCENES.width_assign_error = follow("prep_assign", {{"press", "a"}, {"wait", 180}})
SCENES.width_buy = follow("prep_upgrade", {{"press", "down"}, {"press", "a"}, {"wait", 180}})
SCENES.width_buy_error = follow("width_buy", {{"press", "a"}, {"wait", 180}})
SCENES.width_sell = follow("prep_upgrade", {{"press", "down", 2}, {"press", "a"}, {"wait", 180}})
SCENES.width_save_warning = follow("save", {{"press", "left"}, {"press", "a"}, {"wait", 180}})
SCENES.width_save_slots = follow("width_save_warning", {{"press", "t128,100"}, {"wait", 180}})
SCENES.width_turn = follow("mapmenu", {{"press", "down", 4}, {"press", "a"}, {"wait", 180}})
SCENES.width_team_actions = follow("map", {{"press", "a"}, {"wait", 180}})

-- QA-only: show the existing save confirmation through the error-dialog descriptor variant.
-- This changes only descriptor 9's layout selector; the route supplies no input after it opens.
if LARGE_DIALOG then
  L.on_frame(function()
    if memory.readdword(0x02073e60) == 1 then
      memory.writedword(0x02073e60, 0)
      L.log("WIDTH: save descriptor 9 uses the large-dialog renderer")
    end
  end)
end
