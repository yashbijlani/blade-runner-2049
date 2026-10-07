#!/usr/bin/env python3
"""Fetch and grade the Blade Runner 2049 wallpaper set.

The shipped backgrounds are real 4K (3840x2160) cinematic pieces, not
procedural renders. Each source URL is recorded below so the set stays
reproducible; the grade is a light, in-world pass only -- a touch of
contrast, a cyan-in-shadow / sodium-in-highlight split-tone, a soft
vignette and fine grain. No scanlines, no glitch: the film is fog and
dust, not a CRT.

Provenance note: these are third-party artwork/stills hosted on
wallhaven.cc. They are used here for a personal desktop theme only and
carry whatever licence their original authors set. Do not redistribute
them as part of a shared theme.

Output: 3840x2160 JPEGs into the theme's backgrounds/ directory.
Run:    python3 fetch_wallpapers.py
"""

import os
import urllib.request

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "backgrounds"))

W, H = 3840, 2160

# (filename stem, source URL). Order here is the cycle order (find sorts by
# name; the numeric prefix pins it).
WALLS = [
    ("1-los-angeles-night", "https://w.wallhaven.cc/full/ox/wallhaven-oxwj1l.jpg"),
    ("2-k-ryan-gosling",    "https://w.wallhaven.cc/full/5w/wallhaven-5w6p35.jpg"),
    ("3-joi-neon",         "https://w.wallhaven.cc/full/po/wallhaven-po7l39.jpg"),
    ("4-sapper-farm",       "https://w.wallhaven.cc/full/ym/wallhaven-ym9v87.png"),
    ("5-k-rain",            "https://w.wallhaven.cc/full/q6/wallhaven-q6pg7l.jpg"),
    ("6-wallace-hall",      "https://w.wallhaven.cc/full/lm/wallhaven-lm5e2y.png"),
    ("7-joi-ana-de-armas",  "https://w.wallhaven.cc/full/kx/wallhaven-kxlgw1.png"),
]

# Palette anchors pulled from colors.toml, used only for the split-tone.
SHADOW = np.array([0x0B, 0x11, 0x18], np.float32) / 255.0  # dark-bg blue
HIGHLIGHT = np.array([0xE0, 0x6B, 0x32], np.float32) / 255.0  # sodium amber


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def load(data):
    im = Image.open(__import__("io").BytesIO(data)).convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    return im


def grade(im):
    """A restrained cinematic pass. Everything is deliberately gentle; the
    pictures are already graded, we only nudge them toward the theme."""
    a = np.asarray(im, np.float32) / 255.0

    # Contrast: a shallow S-curve about mid-grey.
    a = np.clip((a - 0.5) * 1.06 + 0.5, 0.0, 1.0)

    # Split-tone: cool blue in the shadows, sodium amber in the highlights.
    lum = a.mean(axis=2, keepdims=True)
    tint = SHADOW * (1.0 - lum) + HIGHLIGHT * lum
    a = a * 0.95 + tint * 0.05

    # Vignette: pulled back at the corners so the desktop furniture reads.
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2.0, H / 2.0
    r = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2)
    a *= np.clip(1.0 - 0.16 * r**2, 0.0, 1.0)[..., None]

    # Fine grain.
    rng = np.random.default_rng(2049)
    a += rng.normal(0.0, 0.008, a.shape).astype(np.float32)

    a = np.clip(a, 0.0, 1.0)
    return Image.fromarray((a * 255.0 + 0.5).astype(np.uint8), "RGB")


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, url in WALLS:
        print(f"fetch {name} <- {url}")
        im = grade(load(fetch(url)))
        path = os.path.join(OUT, name + ".jpg")
        im.save(path, "JPEG", quality=92, optimize=True, progressive=True)
        print(f"  wrote {path} ({im.size[0]}x{im.size[1]})")


if __name__ == "__main__":
    main()
