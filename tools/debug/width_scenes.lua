-- Targeted native-UI width routes. Load after scenes.lua and before warp.lua.
-- Keep these probes separate from the complete normal-build tour's stable scene list.
local function follow(base, extra)
  local route = { boot = SCENES[base].boot, god = SCENES[base].god }
  for _, step in ipairs(SCENES[base]) do route[#route + 1] = step end
  for _, step in ipairs(extra) do route[#route + 1] = step end
  return route
end
SCENES.width_assign_error = follow("prep_assign", {{"press", "a"}, {"wait", 180}})
SCENES.width_buy = follow("prep_upgrade", {{"press", "down"}, {"press", "a"}, {"wait", 180}})
SCENES.width_buy_error = follow("width_buy", {{"press", "a"}, {"wait", 180}})
SCENES.width_sell = follow("prep_upgrade", {{"press", "down", 2}, {"press", "a"}, {"wait", 180}})
SCENES.width_save_slots = follow("save", {{"press", "left"}, {"press", "a"}, {"wait", 180}})
SCENES.width_turn = follow("mapmenu", {{"press", "down", 4}, {"press", "a"}, {"wait", 180}})
SCENES.width_team_actions = follow("map", {{"press", "a"}, {"wait", 180}})
