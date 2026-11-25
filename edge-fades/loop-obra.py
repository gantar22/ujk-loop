"""Obra Dinn-style 1-bit dither fade for the tall loop.

Each line leaving the picture fades out as square 1-bit pixels: a brightness ramp per line is
compared against a threshold pattern, like ditherpunk / Return of the Obra Dinn:
  - "bluenoise": a 64x64 blue-noise threshold map made with the void-and-cluster algorithm
                 (even but random-looking spacing, no grid, no clumps)
  - "bayer":     the classic 8x8 ordered (Bayer) threshold map (crosshatch-looking patterns)

Writes loop-tall-obra-bluenoise.svg and loop-tall-obra-bayer.svg next to this script.
Run:  python3 loop-obra.py
"""
import math
import random
from pathlib import Path

W, H = 240, 364
PX = 1            # dither pixel size, in SVG units (1 unit = 8 px in the 1920-wide PNG)
SEED = 2027
PATCHY = 0.25     # how much the fade density wanders (0 = perfectly even ramp)

# Each fade: (edge, across_from, across_to, solid_until, gone_by)
#   solid_until: where the ramp starts (fully solid on the far side)
#   gone_by:     where the ramp reaches zero; nothing past this toward the edge
BUNDLES = {
    "mBP":   [("top", 16, 32, 18, 2)],                                  # brown + purple
    "mRed":  [("top", 140, 148, 16, 1),                                 # red, top
              ("bottom", 140, 148, 306, 364)],                          # red, bottom: longest tail
    "mGP":   [("left", 40, 56, 17, 0)],                                 # green + pink
    "mBlue": [("left", 66, 74, 14, 3),                                  # blue, left
              ("bottom", 106, 114, 340, 360)],                          # blue, bottom
    "mGO":   [("bottom", 192, 208, 334, 356)],                          # green + orange
}


# ---------- threshold maps ----------

def bayer(n=8):
    m = [[0]]
    while len(m) < n:
        k = len(m)
        m = [[4 * m[y % k][x % k] + [[0, 2], [3, 1]][y // k][x // k] for x in range(2 * k)]
             for y in range(2 * k)]
    N = n * n
    return [[(v + 0.5) / N for v in row] for row in m]


def void_and_cluster(n=64, sigma=1.5, seed=1):
    """Blue-noise threshold map (Ulichney's void-and-cluster), pure Python."""
    rnd = random.Random(seed)
    R = 6
    kern = [(dx, dy, math.exp(-(dx * dx + dy * dy) / (2 * sigma * sigma)))
            for dy in range(-R, R + 1) for dx in range(-R, R + 1)]
    N = n * n
    energy = [0.0] * N
    on = [False] * N

    def put(i, sign):
        x, y = i % n, i // n
        for dx, dy, w in kern:
            energy[((y + dy) % n) * n + (x + dx) % n] += sign * w

    def tightest_cluster():
        return max((i for i in range(N) if on[i]), key=energy.__getitem__)

    def largest_void():
        return min((i for i in range(N) if not on[i]), key=energy.__getitem__)

    # initial pattern: ~10% random pixels, then relax it into an even "prototype"
    for i in rnd.sample(range(N), N // 10):
        on[i] = True
        put(i, 1)
    while True:
        c = tightest_cluster()
        on[c] = False
        put(c, -1)
        v = largest_void()
        on[v] = True
        put(v, 1)
        if v == c:
            break

    proto = on[:]
    proto_energy = energy[:]
    ones = sum(on)
    rank = [0] * N

    # phase 1: rank the prototype's pixels by removing tightest clusters
    for r in range(ones - 1, -1, -1):
        c = tightest_cluster()
        on[c] = False
        put(c, -1)
        rank[c] = r
    # phase 2+3: from the prototype, fill the largest voids until full
    on[:] = proto
    energy[:] = proto_energy
    for r in range(ones, N):
        v = largest_void()
        on[v] = True
        put(v, 1)
        rank[v] = r
    return [[(rank[y * n + x] + 0.5) / N for x in range(n)] for y in range(n)]


# ---------- noise for patchy density ----------

rng = random.Random(SEED)
_grid = {}


def _g(ix, iy):
    if (ix, iy) not in _grid:
        _grid[(ix, iy)] = rng.random()
    return _grid[(ix, iy)]


def smooth(x, y, sc=5.0):
    x /= sc
    y /= sc
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    a = _g(ix, iy) + (_g(ix + 1, iy) - _g(ix, iy)) * fx
    b = _g(ix, iy + 1) + (_g(ix + 1, iy + 1) - _g(ix, iy + 1)) * fx
    return a + (b - a) * fy


# ---------- building the masks ----------

def frange(a, b, step):
    k = 0
    while a + k * step < b - 1e-9:
        yield round(a + k * step, 4)
        k += 1


def band(edge, a0, a1, s, e, tmap, spill=0, px=None):
    PX = px or globals()['PX']
    """spill: extra pixels computed past the line's sides and into its solid part, so the
    rounding filter doesn't nibble the edges of the line."""
    n = len(tmap)
    pad = 3
    if edge in ("top", "left"):
        lo, hi = 0, s + pad
    else:
        lo, hi = s - pad, H
    rect = (lo, a0, hi - lo, a1 - a0) if edge == "left" else (a0, lo, a1 - a0, hi - lo)
    if edge in ("top", "left"):
        hi += spill
    else:
        lo -= spill
    pixels = []
    for u in frange(a0 - spill, a1 + spill, PX):
        for v in frange(lo, hi, PX):
            cu, cv = u + PX / 2, v + PX / 2
            t = (cv - e) / (s - e)                     # 1 = solid ... 0 = gone
            x, y = (cv, cu) if edge == "left" else (cu, cv)
            t += PATCHY * (smooth(x, y) - 0.5) * min(1.0, 2 * min(t, 1 - t) + 0.3)
            gx, gy = int(x // PX), int(y // PX)
            if t > tmap[gy % n][gx % n]:
                pixels.append((x - PX / 2, y - PX / 2))
    # merge horizontal runs of pixels into single rectangles
    pixels.sort(key=lambda p: (p[1], p[0]))
    d, i = [], 0
    while i < len(pixels):
        x, y = pixels[i]
        j = i
        while j + 1 < len(pixels) and abs(pixels[j + 1][1] - y) < 1e-6 \
                and abs(pixels[j + 1][0] - pixels[j][0] - PX) < 1e-6:
            j += 1
        d.append(f"M{x:g} {y:g}h{(j - i + 1) * PX:g}v{PX:g}h{-(j - i + 1) * PX:g}z")
        i = j + 1
    return "".join(d), rect


def build(tmap, label, round_px=0.0, px=None):
    """round_px > 0 rounds the pixels off: blur the 1-bit mask slightly, then snap it back to
    hard edges (a 'gooey' filter). Lone pixels become dots, clusters become soft blobs."""
    defs = []
    if round_px:
        defs.append(
            f'    <filter id="round" filterUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"\n'
            f'            color-interpolation-filters="sRGB">\n'
            f'      <feGaussianBlur stdDeviation="{round_px * (px or PX)}"/>\n'
            f'      <feComponentTransfer><feFuncA type="linear" slope="12" intercept="-5.5"/></feComponentTransfer>\n'
            f'    </filter>\n')
    pix_attr = 'filter="url(#round)"' if round_px else 'shape-rendering="crispEdges"'
    for mid, bands in BUNDLES.items():
        parts, holes = [], []
        for b in bands:
            d, (x, y, w, h) = band(*b, tmap, spill=3 if round_px else 0, px=px)
            parts.append(d)
            holes.append(f"M{x} {y}h{w}v{h}h{-w}z")
        defs.append(
            f'    <mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">\n'
            f'      <rect width="{W}" height="{H}" fill="#fff"/>\n'
            f'      <path fill="#000" d="{"".join(holes)}"/>\n'
            f'      <path fill="#fff" {pix_attr} d="{"".join(parts)}"/>\n'
            f'    </mask>\n')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="480" height="728">
  <!-- Transparent background. Lines leaving the picture fade out as 1-bit square pixels,
       {label}, in the style of Return of the Obra Dinn. Side-by-side pairs fade as one block;
       each bundle has its own fade length, red has the longest tail. Generated by loop-obra.py. -->
  <defs>
{"".join(defs)}  </defs>
  <g fill="none" stroke-width="8">
    <rect x="20" y="20" width="200" height="324" rx="40" stroke="#7c4527"/>
    <rect x="28" y="28" width="184" height="308" rx="32" stroke="#9e6ce4"/>
    <rect x="36" y="36" width="168" height="292" rx="24" stroke="#f55f24"/>
    <rect x="44" y="44" width="152" height="276" rx="16" stroke="#59a848"/>
    <rect x="52" y="52" width="136" height="260" rx="8"  stroke="#ff9f9c"/>
    <g mask="url(#mBP)">
      <path d="M 20 0 V 60" stroke="#7c4527"/>
      <path d="M 28 0 V 60" stroke="#9e6ce4"/>
    </g>
    <g mask="url(#mGP)">
      <path d="M 0 44 H 60" stroke="#59a848"/>
      <path d="M 0 52 H 60" stroke="#ff9f9c"/>
    </g>
    <g mask="url(#mGO)">
      <path d="M 204 304 V 364" stroke="#f55f24"/>
      <path d="M 196 304 V 364" stroke="#59a848"/>
    </g>
  </g>
  <line x1="144" y1="0" x2="144" y2="364" stroke="#f00038" stroke-width="8" mask="url(#mRed)"/>
  <path d="M 0 70 H 86 A 24 24 0 0 1 110 94 V 364" fill="none" stroke="#427eff" stroke-width="8" mask="url(#mBlue)"/>
  <g font-family="Ubuntu, Helvetica, Arial, sans-serif" font-weight="bold"
     font-size="22" text-anchor="middle">
    <text x="81" y="98"  fill="#f55f24">U</text>
    <text x="81" y="122" fill="#9e6ce4">J</text>
    <text x="81" y="146" fill="#59a848">K</text>
    <text x="166" y="228" fill="#427eff">2</text>
    <text x="166" y="252" fill="#ff9f9c">0</text>
    <text x="166" y="276" fill="#7c4527">2</text>
    <text x="166" y="300" fill="#f00038">7</text>
  </g>
</svg>
'''


here = Path(__file__).parent
blue = void_and_cluster()
(here / "loop-tall-obra-bluenoise.svg").write_text(
    build(blue, "thresholded against a void-and-cluster blue-noise map"))
(here / "loop-tall-obra-round-first.svg").write_text(
    build(blue, "thresholded against a void-and-cluster blue-noise map, with the pixels rounded off",
          round_px=0.38))
(here / "loop-tall-obra-fine.svg").write_text(
    build(blue, "thresholded against a void-and-cluster blue-noise map, with finer, rounded pixels",
          round_px=0.38, px=0.5))
(here / "loop-tall-obra-bayer.svg").write_text(
    build(bayer(8), "thresholded against an 8x8 Bayer ordered-dither map"))
