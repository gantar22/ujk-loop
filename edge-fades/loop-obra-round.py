"""The favourite: tall loop with Obra Dinn-style blue-noise dither fades and rounded pixels.

Each line leaving the picture fades out as 1-bit pixels: a brightness ramp per line is compared
against a 64x64 blue-noise threshold map (void-and-cluster), then the pixels are rounded off with
a blur-and-snap ("gooey") filter, so lone pixels become dots and touching ones join into soft
squiggles. The canvas has extra room around the loop so the tails can run out further.

Writes loop-tall-obra-round.svg next to this script.
Run:     python3 loop-obra-round.py
Export:  inkscape loop-tall-obra-round.svg --export-type=png --export-width=1920 \
           --export-filename=loop-tall-obra-round.png
"""
import math
import random
from pathlib import Path

# The loop is drawn in its original 240 x 364 space; these margins add room around it.
LW, LH = 240, 364
PAD_L, PAD_R, PAD_T, PAD_B = 24, 24, 28, 52
W, H = LW + PAD_L + PAD_R, LH + PAD_T + PAD_B
TOP, LEFT, BOTTOM = -PAD_T, -PAD_L, LH + PAD_B      # canvas edges, in loop coordinates

PX = 1            # dither pixel size (1 unit = 1/280 of the width)
ROUND = 0.38      # how much the pixels get rounded (0 = square)
SEED = 2027
PATCHY = 0.25     # how much the fade density wanders (0 = perfectly even ramp)

# Each fade: (edge, across_from, across_to, solid_until, gone_by), in loop coordinates.
#   solid_until: where the ramp starts (fully solid on the far side)
#   gone_by:     where the last pixels run out; nothing past this toward the canvas edge
# Canvas edges: top = -28, left = -24, bottom = 416.
BUNDLES = {
    "mBP":   [("top", 16, 32, 14, -13)],                                # brown + purple
    "mRed":  [("top", 140, 148, 8, -24),                                # red, top
              ("bottom", 140, 148, 338, 414)],                          # red, bottom: longest tail
    "mGP":   [("left", 40, 56, 12, -17)],                               # green + pink
    "mBlue": [("left", 66, 74, 10, -23),                                 # blue, left
              ("bottom", 106, 114, 340, 381)],                          # blue, bottom
    "mGO":   [("bottom", 192, 208, 330, 393)],                          # green + orange
}


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
    proto, proto_energy, ones = on[:], energy[:], sum(on)
    rank = [0] * N
    for r in range(ones - 1, -1, -1):
        c = tightest_cluster()
        on[c] = False
        put(c, -1)
        rank[c] = r
    on[:], energy[:] = proto, proto_energy
    for r in range(ones, N):
        v = largest_void()
        on[v] = True
        put(v, 1)
        rank[v] = r
    return [[(rank[y * n + x] + 0.5) / N for x in range(n)] for y in range(n)]


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


def band(edge, a0, a1, s, e, tmap, spill=3):
    """Pixel shapes for one fade, plus the rectangle of line they replace."""
    n = len(tmap)
    pad = 3
    if edge == "top":
        lo, hi = TOP, s + pad
    elif edge == "left":
        lo, hi = LEFT, s + pad
    else:
        lo, hi = s - pad, BOTTOM
    rect = (lo, a0, hi - lo, a1 - a0) if edge == "left" else (a0, lo, a1 - a0, hi - lo)
    # compute a little past the line's sides and into its solid part, so rounding
    # doesn't nibble the line's edges
    if edge in ("top", "left"):
        hi += spill
    else:
        lo -= spill
    pixels = []
    for u in range(a0 - spill, a1 + spill, PX):
        for v in range(lo, hi, PX):
            cu, cv = u + PX / 2, v + PX / 2
            t = (cv - e) / (s - e)                     # 1 = solid ... 0 = gone
            x, y = (cv, cu) if edge == "left" else (cu, cv)
            t += PATCHY * (smooth(x, y) - 0.5) * min(1.0, 2 * min(t, 1 - t) + 0.3)
            if t > tmap[int(y // PX) % n][int(x // PX) % n]:
                pixels.append((x - PX / 2, y - PX / 2))
    pixels.sort(key=lambda p: (p[1], p[0]))            # merge horizontal runs into rectangles
    d, i = [], 0
    while i < len(pixels):
        x, y = pixels[i]
        j = i
        while j + 1 < len(pixels) and pixels[j + 1] == (pixels[j][0] + PX, y):
            j += 1
        d.append(f"M{x:g} {y:g}h{(j - i + 1) * PX:g}v{PX:g}h{-(j - i + 1) * PX:g}z")
        i = j + 1
    return "".join(d), rect


def build(tmap):
    area = f'x="{LEFT}" y="{TOP}" width="{W}" height="{H}"'
    defs = [f'    <filter id="round" filterUnits="userSpaceOnUse" {area}\n'
            f'            color-interpolation-filters="sRGB">\n'
            f'      <feGaussianBlur stdDeviation="{ROUND * PX}"/>\n'
            f'      <feComponentTransfer><feFuncA type="linear" slope="12" intercept="-5.5"/></feComponentTransfer>\n'
            f'    </filter>\n']
    for mid, bands in BUNDLES.items():
        parts, holes = [], []
        for b in bands:
            d, (x, y, w, h) = band(*b, tmap)
            parts.append(d)
            holes.append(f"M{x} {y}h{w}v{h}h{-w}z")
        defs.append(
            f'    <mask id="{mid}" maskUnits="userSpaceOnUse" {area}>\n'
            f'      <rect {area} fill="#fff"/>\n'
            f'      <path fill="#000" d="{"".join(holes)}"/>\n'
            f'      <path fill="#fff" filter="url(#round)" d="{"".join(parts)}"/>\n'
            f'    </mask>\n')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{2 * W}" height="{2 * H}">
  <!-- Transparent background. Lines leaving the picture fade out as rounded 1-bit pixels
       (blue-noise dither, in the style of Return of the Obra Dinn). Side-by-side pairs fade as
       one block; every fade has its own length, and red has the longest tail.
       Generated by loop-obra-round.py. -->
  <defs>
{"".join(defs)}  </defs>
  <g transform="translate({PAD_L} {PAD_T})">
    <g fill="none" stroke-width="8">
      <rect x="20" y="20" width="200" height="324" rx="40" stroke="#7c4527"/>
      <rect x="28" y="28" width="184" height="308" rx="32" stroke="#9e6ce4"/>
      <rect x="36" y="36" width="168" height="292" rx="24" stroke="#f55f24"/>
      <rect x="44" y="44" width="152" height="276" rx="16" stroke="#59a848"/>
      <rect x="52" y="52" width="136" height="260" rx="8"  stroke="#ff9f9c"/>
      <g mask="url(#mBP)">
        <path d="M 20 {TOP} V 60" stroke="#7c4527"/>
        <path d="M 28 {TOP} V 60" stroke="#9e6ce4"/>
      </g>
      <g mask="url(#mGP)">
        <path d="M {LEFT} 44 H 60" stroke="#59a848"/>
        <path d="M {LEFT} 52 H 60" stroke="#ff9f9c"/>
      </g>
      <g mask="url(#mGO)">
        <path d="M 204 304 V {BOTTOM}" stroke="#f55f24"/>
        <path d="M 196 304 V {BOTTOM}" stroke="#59a848"/>
      </g>
    </g>
    <line x1="144" y1="{TOP}" x2="144" y2="{BOTTOM}" stroke="#f00038" stroke-width="8" mask="url(#mRed)"/>
    <path d="M {LEFT} 70 H 86 A 24 24 0 0 1 110 94 V {BOTTOM}" fill="none" stroke="#427eff" stroke-width="8" mask="url(#mBlue)"/>
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
  </g>
</svg>
'''


Path(__file__).with_name("loop-tall-obra-round.svg").write_text(build(void_and_cluster()))
