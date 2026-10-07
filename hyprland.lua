-- Blade Runner 2049 — Hyprland window chrome.
-- The active edge runs the film's whole neon vocabulary: sodium orange
-- through Joi's magenta to cold cyan, along the diagonal. Inactive windows
-- settle into a dim wet-steel blue.

local active_border_color = {
  colors = { "rgba(E06B32e6)", "rgba(E34B91cc)", "rgba(5FA7B8cc)" },
  angle = 45,
}
local inactive_border_color = "rgba(101923cc)"

hl.config({
  general = {
    col = {
      active_border = active_border_color,
      inactive_border = inactive_border_color,
    },
  },

  group = {
    col = {
      border_active = active_border_color,
      border_inactive = inactive_border_color,
    },
  },
})
