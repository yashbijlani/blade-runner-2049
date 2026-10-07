#!/usr/bin/env python3
"""Render the Blade Runner 2049 wallpaper set.

Original, procedurally generated pieces -- no film stills, no scraped
assets, nothing AI-generated. Every frame is built from gradients, value
noise, silhouette layers, and film grain, tuned to the theme palette so
the desktop furniture stays legible on top.

Output: 3840x2160 JPEGs into the theme's backgrounds/ directory.
Run:    python3 render_wallpapers.py
"""

import os
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "backgrounds"))

W, H = 3840, 2160


# ---------------------------------------------------------------- utilities

def value_noise(shape, cells, seed):
    """Smooth value noise: a small random grid upsampled bicubically."""
    rng = np.random.default_rng(seed)
    grid = rng.random((cells, cells)).astype(np.float32)
    im = Image.fromarray((grid * 255).astype(np.uint8), "L")
    im = im.resize((shape[1], shape[0]), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255.0


def fbm(shape, seed, octaves=6, base=3, gain=0.5, lacunarity=2):
    out = np.zeros(shape, np.float32)
    amp, total = 1.0, 0.0
    for i in range(octaves):
        out += amp * value_noise(shape, base * lacunarity ** i, seed + i * 37)
        total += amp
        amp *= gain
    return out / total


def horizon_fbm(shape, seed, octaves=6, base=3):
    """Fbm stretched wide -- reads as atmospheric banding, not blobs."""
    stretched = fbm((shape[0] // 6, shape[1]), seed, octaves, base)
    im = Image.fromarray((stretched * 255).astype(np.uint8), "L")
    im = im.resize((shape[1], shape[0]), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255.0


def vgrad(shape, stops):
    h, w = shape
    ys = np.linspace(0.0, 1.0, h, np.float32)
    xs = np.array([s[0] for s in stops], np.float32)
    col = np.zeros((h, 3), np.float32)
    for c in range(3):
        vals = np.array([s[1][c] for s in stops], np.float32)
        col[:, c] = np.interp(ys, xs, vals)
    return np.repeat(col[:, None, :], w, axis=1)


def hexc(s):
    s = s.lstrip("#")
    return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def vignette(shape, strength=0.55, power=2.1):
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2.0, h / 2.0
    r = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2) / 1.414
    v = 1.0 - strength * np.clip(r, 0, 1) ** power
    return v[..., None]


def glow(shape, points, radius, seed=0):
    """Sum of Gaussian-ish blobs -> soft additive light field."""
    acc = np.zeros(shape, np.float32)
    im = Image.new("L", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(im)
    for (x, y, s) in points:
        d.ellipse([x - s, y - s, x + s, y + s], fill=255)
    im = im.filter(ImageFilter.GaussianBlur(radius))
    return np.asarray(im, np.float32) / 255.0


def skyline_profile(w, rng, lo, hi, block_lo, block_hi, gap=0):
    prof = np.zeros(w, np.float32)
    x = 0
    while x < w:
        bw = int(rng.integers(block_lo, block_hi))
        bh = rng.uniform(lo, hi)
        prof[x:x + bw] = bh
        x += bw + int(rng.integers(0, gap + 1))
    # a few landmarks punching above the roofline
    for _ in range(rng.integers(2, 5)):
        bx = int(rng.integers(0, w))
        bw = int(rng.integers(block_lo, block_hi * 2))
        prof[bx:bx + bw] = max(prof[bx:bx + bw].max(), rng.uniform(hi, hi * 1.6))
    return prof


def mask_from_profile(shape, base_y, prof):
    h, w = shape
    y = np.arange(h, dtype=np.float32)[:, None]
    top = base_y - prof[None, :]
    return (y >= top).astype(np.float32)


def window_lights(shape, base_y, prof, rng, density, color, glow_radius,
                  size=(3, 7)):
    h, w = shape
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    for x in range(0, w, 4):
        if prof[x] <= 1:
            continue
        top = base_y - prof[x]
        n = int(prof[x] * density)
        for _ in range(n):
            yy = rng.uniform(top + 20, base_y - 10)
            xx = x + rng.uniform(-2, 2)
            s = rng.integers(size[0], size[1])
            d.rectangle([xx, yy, xx + s, yy + s * 1.4], fill=255)
    base = np.asarray(im, np.float32) / 255.0
    soft = np.asarray(
        im.filter(ImageFilter.GaussianBlur(glow_radius)), np.float32
    ) / 255.0
    field = np.clip(base + soft * 1.0, 0, 1)
    return field[..., None] * color[None, None, :]


def grain(shape, amount, seed):
    rng = np.random.default_rng(seed)
    g = rng.normal(0.0, 1.0, (shape[0], shape[1])).astype(np.float32)
    g = np.asarray(
        Image.fromarray(np.clip(g * 40 + 128, 0, 255).astype(np.uint8), "L")
        .filter(ImageFilter.GaussianBlur(0.6)),
        np.float32,
    ) / 255.0
    return (g - 0.5)[..., None] * amount


def finish(arr, seed, grain_amt=6.0, vig=0.55, lift=0.0):
    arr = arr + grain(arr.shape, grain_amt, seed)
    arr = arr * vignette(arr.shape[:2], vig)
    arr = np.clip(arr + lift, 0, 255)
    return arr


def save(arr, name):
    im = Image.fromarray(arr.astype(np.uint8), "RGB")
    path = os.path.join(OUT, name + ".jpg")
    im.save(path, quality=93, subsampling=1, optimize=True, progressive=True)
    print("wrote", os.path.relpath(path, HERE), im.size)


# -------------------------------------------------------------------- scenes

def scene_los_angeles():
    rng = np.random.default_rng(1)
    stops = [
        (0.00, hexc("#04060A")),
        (0.34, hexc("#070C14")),
        (0.58, hexc("#111B28")),
        (0.70, hexc("#2A2A32")),
        (0.745, hexc("#4A3320")),   # sodium haze at the horizon
        (0.80, hexc("#161A20")),
        (1.00, hexc("#05070A")),
    ]
    img = vgrad((H, W), stops)

    # drifting smog
    fog = horizon_fbm((H, W), seed=11, octaves=6, base=3)
    band = np.exp(-((np.linspace(0, 1, H) - 0.66) ** 2) / (2 * 0.16 ** 2))
    img += (fog[..., None] - 0.5) * 34 * band[:, None, None]
    img += np.clip(fog - 0.45, 0, 1)[..., None] * band[:, None, None] * 26

    # warm bloom just above the roofline
    bloom = glow((H, W), [
        (W * 0.30, H * 0.72, 240), (W * 0.34, H * 0.73, 150),
        (W * 0.66, H * 0.71, 170),
    ], radius=190)
    img += bloom[..., None] * hexc("#E08A3C")[None, None, :]

    # two ridges of buildings, far hazed, near black
    far = skyline_profile(W, np.random.default_rng(2), 60, 240, 90, 260, gap=6)
    mid = skyline_profile(W, np.random.default_rng(3), 120, 430, 120, 340, gap=8)
    near = skyline_profile(W, np.random.default_rng(4), 200, 620, 150, 420, gap=12)

    haze = hexc("#1A2634")
    for prof, base, tint in [
        (far, H * 0.760, hexc("#16202C")),
        (mid, H * 0.800, hexc("#0C1119")),
        (near, H * 0.870, hexc("#05070B")),
    ]:
        m = mask_from_profile((H, W), base, prof)
        img = img * (1 - m[..., None] * 0.92) + m[..., None] * tint[None, None, :]
    # a faint haze over the far ridge only
    img += horizon_fbm((H, W), 21, 4, 2)[..., None] * 0.06 * hexc("#3A3226")

    # window pinpricks
    for prof, base, col, dens, gr in [
        (far, H * 0.760, hexc("#B98A4E"), 0.010, 5),
        (mid, H * 0.800, hexc("#C79A5A"), 0.012, 4),
        (near, H * 0.870, hexc("#8AA0B0"), 0.006, 4),
    ]:
        f = window_lights((H, W), base, prof, rng, dens, col, gr)
        img = img + f * 0.85

    return finish(img, seed=101, grain_amt=6.0, vig=0.6)


def scene_orange_haze():
    rng = np.random.default_rng(7)
    stops = [
        (0.00, hexc("#2A1608")),
        (0.28, hexc("#5E3212")),
        (0.55, hexc("#9C5518")),
        (0.70, hexc("#C4762A")),   # the bright dust wall
        (0.78, hexc("#7A4415")),
        (0.86, hexc("#2A1608")),
        (1.00, hexc("#120A04")),
    ]
    img = vgrad((H, W), stops)

    dust = horizon_fbm((H, W), seed=31, octaves=7, base=2)
    img += (dust[..., None] - 0.5) * 46
    img += np.clip(dust - 0.55, 0, 1)[..., None] * hexc("#E8A055") * 0.5

    # deep dust plumes
    plum = fbm((H, W), seed=33, octaves=5, base=2)
    img += np.clip(plum - 0.62, 0, 1)[..., None] * hexc("#F0B268") * 0.4

    # silhouetted towers receding into the dust
    for seed, base, tint, k in [
        (41, H * 0.760, hexc("#7A4A1E"), 0.55),
        (42, H * 0.815, hexc("#40260F"), 0.82),
        (43, H * 0.885, hexc("#160C05"), 0.95),
    ]:
        prof = skyline_profile(W, np.random.default_rng(seed), 80, 360, 110, 300, gap=10)
        m = mask_from_profile((H, W), base, prof) * k
        img = img * (1 - m[..., None]) + m[..., None] * tint[None, None, :]

    return finish(img, seed=102, grain_amt=7.5, vig=0.5)


def scene_k_orange():
    rng = np.random.default_rng(9)
    stops = [
        (0.00, hexc("#8A4E1C")),
        (0.30, hexc("#B4661F")),
        (0.52, hexc("#C77A2C")),
        (0.70, hexc("#8E5320")),
        (0.86, hexc("#3A1F0C")),
        (1.00, hexc("#1E1207")),
    ]
    img = vgrad((H, W), stops)
    img += (horizon_fbm((H, W), 51, 6, 2)[..., None] - 0.5) * 34

    # a lone coat-silhouette, back to us, walking away into the light
    dark = hexc("#180D05")
    cx, ground = W * 0.50, H * 0.945
    fh = H * 0.36
    top = ground - fh
    hr = fh * 0.056
    fig = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(fig)
    # head, with a wider fall of hair
    d.ellipse([cx - hr * 1.15, top, cx + hr * 1.15, top + 2.1 * hr], fill=255)
    # neck
    d.rectangle([cx - hr * 0.36, top + 1.9 * hr, cx + hr * 0.36, top + 2.5 * hr], fill=255)
    # coat: shoulders, taper to waist, flare to a split hem
    sh_y, sh_hw = top + 2.4 * hr, fh * 0.150
    wa_y, wa_hw = top + fh * 0.55, fh * 0.112
    hem_hw = fh * 0.186
    d.polygon([
        (cx - sh_hw, sh_y), (cx - wa_hw, wa_y), (cx - hem_hw, ground),
        (cx - hem_hw * 0.26, ground), (cx, ground - fh * 0.055),
        (cx + hem_hw * 0.26, ground), (cx + hem_hw, ground),
        (cx + wa_hw, wa_y), (cx + sh_hw, sh_y),
    ], fill=255)
    fig = fig.filter(ImageFilter.GaussianBlur(2.2))
    m = np.asarray(fig, np.float32)[..., None] / 255.0
    img = img * (1 - m * 0.93) + m * dark[None, None, :] * 0.93

    # the light wraps the shoulders from behind
    img += glow((H, W), [(cx, top + 2.2 * hr, 300)], radius=180)[..., None] * hexc("#E0A050") * 0.20
    # and the figure casts a soft wet shadow toward the viewer
    img += glow((H, W), [(cx, ground + 30, 300)], radius=200)[..., None] * hexc("#0A0502") * 0.5

    return finish(img, seed=103, grain_amt=8.0, vig=0.62)


def scene_rainy_city():
    rng = np.random.default_rng(13)
    stops = [
        (0.00, hexc("#05080E")),
        (0.30, hexc("#0A1420")),
        (0.55, hexc("#122536")),
        (0.68, hexc("#1E3A4E")),
        (0.74, hexc("#244A5E")),
        (0.82, hexc("#0B131B")),
        (1.00, hexc("#04070B")),
    ]
    img = vgrad((H, W), stops)

    fog = horizon_fbm((H, W), 61, 6, 3)
    img += (fog[..., None] - 0.5) * 26 * np.exp(
        -((np.linspace(0, 1, H) - 0.68) ** 2) / (2 * 0.2 ** 2)
    )[:, None, None]

    # cold window field on two ridges
    for seed, base, tint, k in [
        (71, H * 0.700, hexc("#0E1A26"), 0.9),
        (72, H * 0.770, hexc("#081019"), 0.94),
        (73, H * 0.900, hexc("#04070B"), 0.97),
    ]:
        prof = skyline_profile(W, np.random.default_rng(seed), 90, 480, 110, 320, gap=8)
        m = mask_from_profile((H, W), base, prof) * k
        img = img * (1 - m[..., None]) + m[..., None] * tint[None, None, :]
        f = window_lights((H, W), base, prof, rng, 0.0075, hexc("#6FB6C8"), 4)
        img = img + f * 0.5

    # wet reflection band
    refl = np.exp(-((np.linspace(0, 1, H) - 0.86) ** 2) / (2 * 0.05 ** 2))
    img += hexc("#2E5A6E")[None, None, :] * refl[:, None, None] * 0.22

    # rain: thin near-vertical streaks, denser and brighter up top
    rain = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(rain)
    for _ in range(3200):
        x = rng.uniform(0, W)
        y = rng.uniform(0, H)
        ln = rng.uniform(24, 130)
        drift = rng.uniform(-18, 8)
        w_ = rng.choice([1, 1, 1, 2])
        d.line([x, y, x + drift, y + ln], fill=int(rng.uniform(50, 150)), width=int(w_))
    rain = rain.filter(ImageFilter.GaussianBlur(0.9))
    rmask = np.asarray(rain, np.float32)[..., None] / 255.0
    img = img + rmask * hexc("#9FC4D4")[None, None, :] * 0.42

    # a single warm sign, far off, the only heat in the frame
    img += glow((H, W), [(W * 0.22, H * 0.72, 120)], radius=120)[..., None] * hexc("#E06B32") * 0.5

    return finish(img, seed=104, grain_amt=5.5, vig=0.58)


def scene_joi():
    rng = np.random.default_rng(17)
    stops = [
        (0.00, hexc("#080610")),
        (0.22, hexc("#150C1E")),
        (0.40, hexc("#241130")),
        (0.58, hexc("#120A18")),
        (0.80, hexc("#08060C")),
        (1.00, hexc("#040306")),
    ]
    img = vgrad((H, W), stops)

    # the room: a far wall grid, barely lit, keeping the frame mostly black
    wall = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(wall)
    for gx in range(0, W, 260):
        d.line([gx, H * 0.10, gx, H * 0.68], fill=40, width=3)
    for gy in range(int(H * 0.10), int(H * 0.68), 210):
        d.line([0, gy, W, gy], fill=34, width=2)
    wall = wall.filter(ImageFilter.GaussianBlur(5))
    img += (np.asarray(wall, np.float32)[..., None] / 255.0) * hexc("#25313E") * 0.6

    # a drift of pink dust in the air
    veil = fbm((H, W), seed=81, octaves=6, base=2)
    img += np.clip(veil - 0.66, 0, 1)[..., None] * hexc("#E34B91") * 0.35

    # the projection: a standing figure of soft pink light, not a blob
    cx, ground = W * 0.50, H * 0.90
    fh = H * 0.58
    top = ground - fh
    hr = fh * 0.050
    fig = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(fig)
    d.ellipse([cx - hr * 1.55, top - hr * 0.3, cx + hr * 1.55, top + 2.3 * hr], fill=255)  # hair
    d.rectangle([cx - hr * 0.36, top + 1.9 * hr, cx + hr * 0.36, top + 2.6 * hr], fill=255)  # neck
    d.polygon([
        (cx - fh * 0.130, top + 2.5 * hr), (cx - fh * 0.150, top + fh * 0.44),
        (cx - fh * 0.098, ground), (cx + fh * 0.098, ground),
        (cx + fh * 0.150, top + fh * 0.44), (cx + fh * 0.130, top + 2.5 * hr),
    ], fill=255)
    core = np.asarray(fig.filter(ImageFilter.GaussianBlur(3)), np.float32)[..., None] / 255.0
    soft = np.asarray(fig.filter(ImageFilter.GaussianBlur(26)), np.float32)[..., None] / 255.0
    field = np.clip(core * 0.75 + soft * 0.95, 0, 1)
    img += field * hexc("#EE6FA8")[None, None, :] * 0.9

    # a cold cyan edge where the hologram meets the floor
    rim = np.asarray(fig.filter(ImageFilter.GaussianBlur(60)), np.float32)[..., None] / 255.0
    img += rim * hexc("#5FA7B8")[None, None, :] * 0.30

    # scanline sweep across the projection
    ys = np.arange(H, dtype=np.float32)[:, None]
    scan = (np.sin(ys * 0.8) * 0.5 + 0.5) * np.exp(
        -((ys / H - 0.62) ** 2) / (2 * 0.24 ** 2)
    )
    img += (scan * field[..., 0])[..., None] * hexc("#F06AA8") * 0.14

    return finish(img, seed=105, grain_amt=6.0, vig=0.64)


def scene_wallace():
    rng = np.random.default_rng(19)
    stops = [
        (0.00, hexc("#0A0D10")),
        (0.30, hexc("#11161A")),
        (0.52, hexc("#1A2228")),
        (0.68, hexc("#232D34")),
        (0.74, hexc("#2B363D")),   # the waterline of light
        (0.80, hexc("#161D22")),
        (1.00, hexc("#080B0E")),
    ]
    img = vgrad((H, W), stops)

    # vertical light shafts off polished stone -- cold, geometric, silent
    shafts = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(shafts)
    x = 0
    while x < W:
        sw = int(rng.integers(40, 190))
        if rng.random() < 0.5:
            d.rectangle([x, 0, x + sw, H], fill=int(rng.uniform(20, 90)))
        x += sw + int(rng.integers(30, 200))
    shafts = shafts.filter(ImageFilter.GaussianBlur(26))
    sm = np.asarray(shafts, np.float32)[..., None] / 255.0
    img += sm * hexc("#8FA6B2")[None, None, :] * 0.55

    # a still sheet of water reflecting the light
    refl = np.exp(-((np.linspace(0, 1, H) - 0.78) ** 2) / (2 * 0.06 ** 2))
    img += hexc("#AEBec8")[None, None, :] * refl[:, None, None] * 0.18
    rip = fbm((H, W), seed=91, octaves=5, base=2)
    img += (rip[..., None] - 0.5) * refl[:, None, None] * 22

    # one warm accent, the only human thing in the room
    img += glow((H, W), [(W * 0.72, H * 0.70, 90)], radius=110)[..., None] * hexc("#E06B32") * 0.45

    return finish(img, seed=106, grain_amt=5.0, vig=0.6)


def scene_spinner():
    rng = np.random.default_rng(23)
    stops = [
        (0.00, hexc("#03050A")),
        (0.35, hexc("#060B14")),
        (0.60, hexc("#0C1622")),
        (0.72, hexc("#1A2634")),
        (0.78, hexc("#241F1C")),
        (0.86, hexc("#0A0E14")),
        (1.00, hexc("#04060A")),
    ]
    img = vgrad((H, W), stops)
    img += (horizon_fbm((H, W), 111, 6, 3)[..., None] - 0.5) * 22

    # a low roofline under the craft
    prof = skyline_profile(W, np.random.default_rng(113), 60, 300, 100, 280, gap=10)
    m = mask_from_profile((H, W), H * 0.84, prof)
    img = img * (1 - m[..., None] * 0.93) + m[..., None] * hexc("#04070B")[None, None, :]
    img += window_lights((H, W), H * 0.84, prof, rng, 0.006, hexc("#B98A4E"), 5) * 0.6

    cx, cy = W * 0.60, H * 0.28

    # short engine trails trailing off behind the craft only
    trails = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(trails)
    for i, dy in enumerate((-14, 0, 12)):
        d.line([cx - 620, cy + dy, cx - 150, cy + dy * 0.4], fill=120 - i * 20, width=4)
    trails = trails.filter(ImageFilter.GaussianBlur(5))
    img += (np.asarray(trails, np.float32)[..., None] / 255.0) * hexc("#5FA7B8") * 0.5

    # a cold search cone sweeping down from the hull to the street
    cone = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(cone)
    d.polygon([(cx - 40, cy + 40), (cx + 40, cy + 40),
               (cx + 380, H * 0.86), (cx - 340, H * 0.86)], fill=90)
    cone = cone.filter(ImageFilter.GaussianBlur(40))
    img += (np.asarray(cone, np.float32)[..., None] / 255.0) * hexc("#7FB4C6") * 0.35

    # the spinner: a flattened hull, hard-edged, with two sodium lights
    hull = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(hull)
    d.polygon([
        (cx - 300, cy + 30), (cx - 150, cy - 18), (cx + 150, cy - 22),
        (cx + 300, cy + 4), (cx + 130, cy + 48), (cx - 140, cy + 54),
    ], fill=255)
    d.polygon([(cx - 250, cy - 4), (cx + 40, cy - 22), (cx + 60, cy - 6), (cx - 240, cy + 12)], fill=255)  # canopy
    d.rectangle([cx - 240, cy + 48, cx - 170, cy + 82], fill=255)  # rear fin
    hm = np.asarray(hull.filter(ImageFilter.GaussianBlur(1.4)), np.float32)[..., None] / 255.0
    img = img * (1 - hm * 0.95) + hm * hexc("#090C11")[None, None, :] * 0.95
    # tight rim light so the hull reads as metal, not a glow
    rm = np.asarray(hull.filter(ImageFilter.GaussianBlur(6)), np.float32)[..., None] / 255.0
    img += rm * hexc("#5FA7B8")[None, None, :] * 0.16
    # two bright point lights on the belly
    img += glow((H, W), [(cx - 250, cy + 40, 26), (cx - 168, cy + 40, 20)],
                radius=55)[..., None] * hexc("#F09040") * 1.1

    return finish(img, seed=107, grain_amt=6.0, vig=0.62)


def main():
    os.makedirs(OUT, exist_ok=True)
    for fn, name in [
        (scene_los_angeles, "1-los-angeles-night"),
        (scene_orange_haze, "2-orange-haze"),
        (scene_k_orange, "3-k-orange"),
        (scene_rainy_city, "4-rainy-city"),
        (scene_joi, "5-joi"),
        (scene_wallace, "6-wallace"),
        (scene_spinner, "7-spinner"),
    ]:
        save(fn(), name)


if __name__ == "__main__":
    main()
