# Blade Runner 2049

An Omarchy theme built from the film's vocabulary of dust: a near-black
blue city, weathered steel, sodium-amber haze, and the cold teal spill of a
hologram. Roughly **70% dark blue/black, 15% grey/steel, 8% orange/amber,
4% cyan/blue, 3% pink/red** — the amber only ever touches the edges, and
nothing glows for its own sake.

Targets **Omarchy 4** (the Quickshell shell). No Waybar, no Mako, no GTK
override — everything goes through Omarchy's native theme mechanism, so it
installs, switches, and removes like any other theme.

---

## Install

A theme is just a directory under `~/.config/omarchy/themes/`. This one is
already there; to rebuild it elsewhere, copy the directory:

```sh
cp -r ~/.config/omarchy/themes/blade-runner-2049 ~/.config/omarchy/themes/
```

The theme is kept under version control, but its git metadata lives
**outside** the theme directory — a `.git` *file* at the theme root points to
`~/Projects/blade-runner-2049.git`. This matters because Omarchy treats a
theme directory containing a `.git` **directory** as "installed from a repo"
and stages it through a much stricter path that strips `.lua` files and
terminal configs. Keeping the metadata out of the tree keeps a local checkout
staging in full.

A plain `git clone` puts a `.git` directory back in the tree (which is why
`omarchy theme install` will drop `hyprland.lua` and the terminal configs —
the security policy for themes from a stranger's repo). After cloning, remove
the `.git` directory, or move it aside with `--separate-git-dir`, to keep the
full theme.

To install straight from the repository:

```sh
omarchy theme install https://github.com/yashbijlani/blade-runner-2049
```

The theme is registered under the name `blade-runner-2049`, so it is then set
with `omarchy theme set blade-runner-2049` as below.

## Activate

```sh
omarchy theme set blade-runner-2049
```

Or open the picker (`Super + Shift + T` / `omarchy theme switcher`) and
choose **Blade Runner 2049**. Every apply cycles the wallpaper to the next
image in `backgrounds/`.

Re-apply to step to the next wallpaper at any time:

```sh
omarchy theme set blade-runner-2049
```

## Remove

```sh
omarchy theme remove blade-runner-2049
```

Then switch to another theme (`omarchy theme set <name>`) to clear the
staged copy at `~/.local/state/omarchy/current/theme`. Remove that directory
too if you want the state fully gone.

---

## What's in here

| File | Purpose |
| --- | --- |
| `colors.toml` | The palette. Drives terminals (kitty/foot/ghostty/alacritty), btop, neovim, helix, tmux, VS Code, Obsidian, browser, and the Hyprland borders. |
| `hyprland.lua` | Window chrome: a sodium→magenta→cyan gradient on the active border, dim wet steel when inactive. |
| `shell.bar.toml` | The bar: near-black, quiet, no glow. |
| `shell.controls.toml` | Buttons/tabs: steel idle, sodium focus, cyan hover. |
| `shell.launcher.toml` / `shell.menu.toml` | Launcher and menu cards over a darkened street, edged in sodium→magenta neon. |
| `shell.notifications.toml` | Toasts on a cold cyan→magenta edge. |
| `shell.popups.toml` | Bar flyouts with a cool steel/cyan edge. |
| `shell.tooltip.toml` | Hover tooltips on the lifted panel blue. |
| `shell.lock.toml` | Lock input: steel idle → sodium while typing → red on a wrong pass. |
| `shell.spacing.toml` | Slightly tighter than stock (`scale = 0.96`). |
| `shell.font.toml` | Type scale root (`base-size = 12`). |
| `icons.theme` | `Yaru-olive-dark` — muted, monochrome, in-world. |
| `keyboard.rgb` | `E06B32` — sodium amber, for RGB-capable keyboards. |
| `backgrounds/` | Nine cinematic wallpapers: two shipped 4K frames plus seven user-added frames (see below). |
| `preview.png` | Selector thumbnail, cut from the wallpaper set. |
| `extras/starship.toml` | **Opt-in** prompt retint (see below). |
| `scripts/fetch_wallpapers.py` | Re-fetches and re-grades the wallpaper set from its recorded sources. |
| `scripts/render_wallpapers.py` | **Superseded.** The earlier fully-procedural wallpaper set, kept for reference. |

## Wallpapers

The set is two of the 4K frames the theme shipped with (Wallace Hall, the
protein farm) plus seven cinematic frames the user added. Files are
numbered `01`–`09` so the cycle order is stable.

1. `01-wallace-hall` — the silent hall of light and reflection
2. `02-joi-hologram` — Joi's hologram in pink and blue
3. `03-joi-table` — Joi at the table in daylight
4. `04-amber-corridor` — a corridor of sodium light
5. `05-solar-field` — the solar array seen from above
6. `06-la-skyline` — the city skyline under dust and spinners
7. `07-desert-spinner` — K and the spinner in the orange waste
8. `08-hall-staircase` — the golden stair of Wallace's hall
9. `09-sapper-farm` — the lone tree on the protein farm

The seven user-added frames are plain images the theme does not track or
re-download. The Wallace Hall and sapper-farm frames come from the original
fetched set; the script below regenerates that full seven-frame set (Python
3 + Pillow + NumPy, network required), which will also restore the frames no
longer used here:

```sh
python3 ~/.config/omarchy/themes/blade-runner-2049/scripts/fetch_wallpapers.py
```

### Provenance & licensing

These are **third-party artwork and film-derived stills hosted on
wallhaven.cc**, not original work by this theme. Each source URL is recorded
in `scripts/fetch_wallpapers.py` so the set stays reproducible and
traceable. They carry whatever licence their original authors set and are
**not** covered by the theme's MIT licence. They are shipped in this repo for
personal desktop use; a rights holder who wants one removed can open an issue
and it will be replaced. For a build with no third-party media at all, the
fully-original procedural set (`render_wallpapers.py`) is still in the repo
and needs no attribution.

### Using your own images

Drop any `.jpg`/`.png` into the theme's `backgrounds/` and Omarchy will cycle
to it. Two ways to keep a personal set separate from the theme:

```sh
# A: into the theme itself
~/.config/omarchy/themes/blade-runner-2049/backgrounds/

# B: a user-level set that overlays the theme (survives theme updates)
~/.config/omarchy/backgrounds/blade-runner-2049/
```

Either directory, same slug, same rules — `find` picks them up sorted, any of
`jpg jpeg png gif bmp webp`, and each re-apply advances to the next.

## Fonts & cursor

- **Fonts:** the theme does not ship or fetch fonts. The shell and terminals
  fall back to **JetBrainsMono Nerd Font** (mono) and **Adwaita Sans** (UI),
  which are already present. For a closer match to the film's condensed
  display type, install a face like *IBM Plex Sans Condensed* or *Inter* and
  point `[font]`/terminal configs at it yourself — the theme makes no
  network calls.
- **Cursor:** Omarchy has no per-theme cursor mechanism. Size lives in
  `/usr/share/omarchy/default/hypr/envs.lua`
  (`XCURSOR_SIZE`/`HYPRCURSOR_SIZE`); set the theme through your
  `~/.config/hypr` config if you want one. Nothing here changes it.

## Optional: Starship prompt

Starship colors are **not** generated from `colors.toml`, so the stock prompt
stays cyan in every theme. `extras/starship.toml` is the retint — a sodium
`❯`, teal paths, red errors. It is not installed automatically; copy it
yourself once you've reviewed it:

```sh
cp ~/.config/omarchy/themes/blade-runner-2049/extras/starship.toml ~/.config/starship.toml
```

## Extras

```sh
omarchy theme extras blade-runner-2049
```

## License

The theme's own work — the palette, the shell surface tuning, the Hyprland
chrome, the scripts — is MIT (see `LICENSE`).

The shipped wallpapers are **not** original to the theme and are **not**
covered by that licence: they are third-party artwork/film-derived stills
from wallhaven.cc, used for personal desktop use only (see
[Provenance & licensing](#provenance--licensing)). Do not redistribute them
in a shared copy of this theme; use the procedural set from
`scripts/render_wallpapers.py` instead if you need a licence-clean build.
