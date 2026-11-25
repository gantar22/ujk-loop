"""Fade the line ends of a PNG (the vertical-name design) with the same rounded
blue-noise dither as final/loop-square-obra.py. Works on the PNG directly.
Writes vertical-name-obra.png next to this script.  Run: python3 fade-ends.py path/to/source.png
"""
import math, random, sys
from pathlib import Path
from PIL import Image, ImageFilter

HERE = Path(__file__).parent
CELL = 4          # dither pixel size in image px (lines are ~24 px wide -> 6 cells across)
ROUND = 1.6       # blur sigma used to round the cells
PATCHY = 0.25
SEED = 2027

# (axis, across_from, across_to, solid_until, gone_by) in image px.
# axis "y": fade runs vertically (top/bottom exits); "x": horizontally (left exits).
FADES = [
    ("y", 184, 246, 100, 8),      # brown + purple, top
    ("y", 614, 650, 104, 4),      # red, top
    ("x", 198, 284, 182, 72),     # green + pink + blue, left
    ("y", 614, 650, 1172, 1278),  # red, bottom
    ("y", 792, 856, 1128, 1272),  # green + orange, bottom
    ("x", 1236, 1280, 372, 66),   # blue, bottom left: longest tail
]

# borrow the blue-noise generator from the final script without running it
src = (HERE.parent / "final" / "loop-square-obra.py").read_text()
src = src[:src.index("rng = random.Random")]
ns = {}
exec(src, ns)
tmap = ns["void_and_cluster"]()
n = len(tmap)

rng = random.Random(SEED)
_grid = {}
def g(i, j):
    return _grid.setdefault((i, j), rng.random())
def smooth(x, y, sc=20.0):
    x, y = x / sc, y / sc
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = g(ix, iy) + (g(ix + 1, iy) - g(ix, iy)) * fx
    b = g(ix, iy + 1) + (g(ix + 1, iy + 1) - g(ix, iy + 1)) * fx
    return a + (b - a) * fy

im = Image.open(sys.argv[1]).convert("RGB")
W, H = im.size
bg = Image.new("RGB", im.size, im.getpixel((5, 5)))
mask = Image.new("L", im.size, 255)
mp = mask.load()
for axis, a0, a1, s, e in FADES:
    lo, hi = sorted((s, e))
    lo = max(0, lo - 12) if e < s else lo
    hi = min(W if axis == "x" else H, hi + 12) if e > s else hi
    for u in range(a0 // CELL * CELL, a1, CELL):
        for v in range(lo // CELL * CELL, hi, CELL):
            cu, cv = u + CELL / 2, v + CELL / 2
            t = (cv - e) / (s - e)
            x, y = (cv, cu) if axis == "x" else (cu, cv)
            t += PATCHY * (smooth(x, y) - 0.5) * min(1.0, 2 * min(max(t, 0), max(1 - t, 0)) + 0.3)
            keep = t > tmap[int(y // CELL) % n][int(x // CELL) % n]
            if not keep:
                for yy in range(int(y - CELL / 2), int(y + CELL / 2)):
                    for xx in range(int(x - CELL / 2), int(x + CELL / 2)):
                        if 0 <= xx < W and 0 <= yy < H:
                            mp[xx, yy] = 0
# round the 1-bit cells: blur, then snap back to a crisp (lightly antialiased) edge
mask = mask.filter(ImageFilter.GaussianBlur(ROUND))
mask = mask.point(lambda v: max(0, min(255, int((12 * v / 255 - 5.5) * 255))))
Image.composite(im, bg, mask).save(HERE / "vertical-name-obra.png")
