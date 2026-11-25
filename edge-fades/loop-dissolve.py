"""Generates loop-tall-dissolve.svg: the tall loop with each exiting line dissolving into dots.

Tweak BUNDLES below and re-run:  python3 loop-dissolve.py
Then export:  inkscape loop-tall-dissolve.svg --export-type=png --export-width=1920 \
                --export-filename=loop-tall-dissolve.png
"""
import math
import random
from pathlib import Path

W, H, C = 240, 364, 1          # canvas size, dot cell size
RMAX = 0.47 * C                # biggest dot radius; < half a cell so dots never overlap
SEED = 2027

# Each dissolve: (edge, across_from, across_to, solid_ends_at, last_dots_at)
#   edge: which canvas edge the line exits through
#   across_*: the bundle's extent across its width (side-by-side pairs as one block)
#   solid_ends_at: roughly where the solid line starts breaking up (the edge of it is ragged)
#   last_dots_at: where the dots run out; everything past this toward the edge is gone
BUNDLES = {
    "mBP":   [("top", 16, 32, 16, 3)],                                  # brown + purple
    "mRed":  [("top", 140, 148, 14, 2),                                 # red, top
              ("bottom", 140, 148, 314, 364)],                          # red, bottom: longest tail
    "mGP":   [("left", 40, 56, 15, 1)],                                 # green + pink
    "mBlue": [("left", 66, 74, 12, 4),                                  # blue, left
              ("bottom", 106, 114, 344, 358)],                          # blue, bottom
    "mGO":   [("bottom", 192, 208, 338, 354)],                          # green + orange
}

rng = random.Random(SEED)
_grid = {}


def _g(ix, iy):
    if (ix, iy) not in _grid:
        _grid[(ix, iy)] = rng.random()
    return _grid[(ix, iy)]


def smooth(x, y, sc=3.0):
    """Smooth value noise in 0..1, used to make the edge wobble and the density patchy."""
    x /= sc
    y /= sc
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    a = _g(ix, iy) + (_g(ix + 1, iy) - _g(ix, iy)) * fx
    b = _g(ix, iy + 1) + (_g(ix + 1, iy + 1) - _g(ix, iy + 1)) * fx
    return a + (b - a) * fy


def wobble(u, key):
    """Smooth 1-D noise in -1..1 along a bundle's width (two octaves)."""
    return (smooth(u, key, 4.0) - 0.5) * 1.4 + (smooth(u, key + 50, 1.5) - 0.5) * 0.6


def band(edge, a0, a1, s, e):
    """Mask shapes for one dissolve, and the rectangle they replace."""
    L = abs(s - e)
    amp = max(2.0, 0.22 * L)                # how far the wavy solid edge swings either way
    extra = math.ceil(amp + 2)
    toward = -1 if edge in ("top", "left") else 1   # direction toward the canvas edge
    if edge in ("top", "left"):
        lo, hi = 0, math.ceil(s + extra)    # band runs all the way out to the canvas edge
    else:
        lo, hi = math.floor(s - extra), H
    key = rng.uniform(1000, 9000)           # each band gets its own wave

    def boundary(u):                        # where the solid part ends, at position u across
        return s + toward * amp * wobble(u, key)

    # Solid part: a smooth, wavy-edged shape from the band's solid side out to boundary(u)
    inner = hi if toward < 0 else lo
    us = [a0 + i * 0.25 for i in range(int((a1 - a0) / 0.25) + 1)]
    pts = [(u, boundary(u)) for u in us] + [(a1, inner), (a0, inner)]
    if edge == "left":
        pts = [(v, u) for u, v in pts]
    shapes = ["M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + "z"]

    for u in range(a0, a1, C):              # across the width
        for v in range(lo, hi, C):          # along the direction of travel
            cu, cv = u + C / 2, v + C / 2
            b = boundary(cu)
            past = (cv - b) * toward        # how far past the solid edge this cell is
            if past <= 0:
                continue
            t = 1 - past / max(abs(b - e), 1)   # 1 at the solid edge, 0 at the last dots
            x, y = (cv, cu) if edge == "left" else (cu, cv)
            t += 0.3 * (smooth(x, y) - 0.5)
            if t <= 0:
                continue
            r = 0.5 * C * math.sqrt(t) * rng.uniform(0.45, 1.25)   # size carries the fade
            if rng.random() > 0.2 + 0.8 * t:                       # some gaps, more near the end
                continue
            r = min(r, RMAX)
            if r < 0.06 * C:
                continue
            sl = RMAX - r                                          # nudge small dots off-grid
            x += rng.uniform(-sl, sl)
            y += rng.uniform(-sl, sl)
            du, dv = (y, x) if edge == "left" else (x, y)
            if (dv - boundary(du)) * toward < r + 0.08:            # would touch the solid edge
                continue
            shapes.append(f"M{x - r:.3f} {y:.3f}a{r:.3f} {r:.3f} 0 1 0 {2 * r:.3f} 0"
                          f"a{r:.3f} {r:.3f} 0 1 0 {-2 * r:.3f} 0z")
    rect = (lo, a0, hi - lo, a1 - a0) if edge == "left" else (a0, lo, a1 - a0, hi - lo)
    return "".join(shapes), rect


def mask(mid, bands):
    parts, holes = [], []
    for b in bands:
        shapes, (x, y, w, h) = band(*b)
        parts.append(shapes)
        holes.append(f"M{x} {y}h{w}v{h}h{-w}z")
    return (f'    <mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">\n'
            f'      <rect width="{W}" height="{H}" fill="#fff"/>\n'
            f'      <path fill="#000" d="{"".join(holes)}"/>\n'
            f'      <path fill="#fff" d="{"".join(parts)}"/>\n'
            f'    </mask>\n')


defs = "".join(mask(mid, b) for mid, b in BUNDLES.items())

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="480" height="728">
  <!-- Transparent background. Each line leaving the picture dissolves into round dots of random
       size (no overlaps). Side-by-side pairs dissolve together as one block. Every bundle starts
       and finishes its dissolve at a different point, the solid part ends on a ragged edge, and
       the red line has the longest tail at the bottom. Generated by loop-dissolve.py. -->
  <defs>
{defs}  </defs>
  <g fill="none" stroke-width="8">
    <!-- Rounded-rectangle loop rings, outside in: brown, purple, orange, green, pink -->
    <rect x="20" y="20" width="200" height="324" rx="40" stroke="#7c4527"/>
    <rect x="28" y="28" width="184" height="308" rx="32" stroke="#9e6ce4"/>
    <rect x="36" y="36" width="168" height="292" rx="24" stroke="#f55f24"/>
    <rect x="44" y="44" width="152" height="276" rx="16" stroke="#59a848"/>
    <rect x="52" y="52" width="136" height="260" rx="8"  stroke="#ff9f9c"/>

    <!-- Brown and purple come in from the top -->
    <g mask="url(#mBP)">
      <path d="M 20 0 V 60" stroke="#7c4527"/>
      <path d="M 28 0 V 60" stroke="#9e6ce4"/>
    </g>
    <!-- Green and pink come in from the left -->
    <g mask="url(#mGP)">
      <path d="M 0 44 H 60" stroke="#59a848"/>
      <path d="M 0 52 H 60" stroke="#ff9f9c"/>
    </g>
    <!-- Orange and green leave out the bottom -->
    <g mask="url(#mGO)">
      <path d="M 204 304 V 364" stroke="#f55f24"/>
      <path d="M 196 304 V 364" stroke="#59a848"/>
    </g>
  </g>
  <!-- Red vertical line -->
  <line x1="144" y1="0" x2="144" y2="364" stroke="#f00038" stroke-width="8" mask="url(#mRed)"/>
  <!-- Blue: in from the left, rounded turn, down out the bottom -->
  <path d="M 0 70 H 86 A 24 24 0 0 1 110 94 V 364" fill="none" stroke="#427eff" stroke-width="8" mask="url(#mBlue)"/>

  <!-- Vertical text inside the loop, each letter a different line color -->
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

Path(__file__).with_name("loop-tall-dissolve.svg").write_text(svg)
