import math, random

# Same layout as loop-liquid-gen.py, drawn as twisted rope instead of liquid.
random.seed(3)
CX, CY = 100, 100
COLORS = ["#62361b", "#522398", "#f9461c", "#009b3a", "#e27ea6"]  # outside -> in
R0, STEP, W = 80, 6, 6.4     # outer radius, ring spacing, rope thickness
H = 0.25                     # resampling step
LAY = 1.1                    # distance between strand lines, as a fraction of rope width
TWIST = 1.6                  # how far one strand line runs along the rope, fraction of width
INK = "#3a374a"              # outline colour (flat, illustrated look)
OW = 0.13                    # outline thickness, fraction of rope width

# per-corner inset of the rounding centre (0 = full quarter circle, larger = squarer)
CORNER = {(-1, -1): 32, (1, 1): 32, (1, -1): 0, (-1, 1): 0}


def ring_point(R, a):
    dx, dy = math.cos(a), math.sin(a)
    sx, sy = (1 if dx >= 0 else -1), (1 if dy >= 0 else -1)
    c = CORNER[(sx, sy)]
    t = R / max(abs(dx), abs(dy))
    x, y = t * dx, t * dy
    if abs(x) > c and abs(y) > c:
        cx, cy, r = sx * c, sy * c, R - c
        b = dx * cx + dy * cy
        t = b + math.sqrt(b * b - (cx * cx + cy * cy - r * r))
        x, y = t * dx, t * dy
    return CX + x, CY + y


def mix(hexc, other, f):
    a = [int(hexc[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(other[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * f):02x}" for x, y in zip(a, b))


def dark(c, f=0.45): return mix(c, "#000000", f)
def light(c, f=0.35): return mix(c, "#ffffff", f)


# ---- paths --------------------------------------------------------------------
def seg(x0, y0, x1, y1): return [(x0, y0), (x1, y1)]


def arc(R, a0, a1):
    n = int(abs(a1 - a0) * 2)
    return [ring_point(R, math.radians(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def bezier(p0, p1, p2, p3, n=300):
    out = []
    for k in range(n + 1):
        t = k / n; u = 1 - t
        out.append(tuple(u**3 * p0[i] + 3*u*u*t * p1[i] + 3*u*t*t * p2[i] + t**3 * p3[i] for i in (0, 1)))
    return out


class Rope:
    def __init__(self, pts, closed=False):
        xs, ys = [pts[0][0]], [pts[0][1]]
        carry = 0.0
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            L = math.hypot(bx - ax, by - ay)
            if L == 0: continue
            d = H - carry
            while d <= L:
                xs.append(ax + (bx - ax) * d / L); ys.append(ay + (by - ay) * d / L); d += H
            carry = L - (d - H)
        self.xs, self.ys, self.closed = xs, ys, closed
        self.n = len(xs)
        self.len = (self.n - 1) * H
        self.t = []
        for i in range(self.n):
            a, b = self._idx(i - 2), self._idx(i + 2)
            dx, dy = xs[b] - xs[a], ys[b] - ys[a]
            l = math.hypot(dx, dy) or 1
            self.t.append((dx / l, dy / l))

    def _idx(self, i):
        if self.closed: return i % (self.n - 1)
        return max(0, min(self.n - 1, i))

    def at(self, s, o=0.0):
        """Point s along the rope, pushed o sideways (straight-line extension past the ends)."""
        if self.closed: s %= self.len
        i = int(round(s / H)); j = self._idx(i)
        x, y = self.xs[j], self.ys[j]
        tx, ty = self.t[j]
        extra = s - j * H if not self.closed else 0.0
        x += tx * extra; y += ty * extra
        return x - ty * o, y + tx * o

    def tangent(self, s):
        if self.closed: s %= self.len
        return self.t[self._idx(int(round(s / H)))]


def pl(points):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in points)


def draw_rope(rope, color, width=W):
    """Flat illustrated rope: ink outline, solid fill, S-shaped lines between strands."""
    hw, ow = width / 2, width * OW
    line = pl(zip(rope.xs, rope.ys))
    join = 'stroke-linejoin="round"'
    tag = "polygon" if rope.closed else "polyline"
    out = [f'<{tag} points="{line}" fill="none" stroke="{INK}" stroke-width="{width:.2f}" {join}/>',
           f'<{tag} points="{line}" fill="none" stroke="{color}" stroke-width="{width - 2 * ow:.2f}" {join}/>']
    lay, tw = LAY * width, TWIST * width
    if rope.closed:                     # whole number of strands so the loop has no seam
        lay = rope.len / round(rope.len / lay)
    inner = hw - ow / 2                 # strand lines meet the outline, tangent to it
    d = []
    s = 0.0 if rope.closed else -tw
    while s < rope.len:
        pts = []
        for k in range(17):
            u = k / 16
            su = s + tw * u
            if not rope.closed and not (0 <= su <= rope.len):
                continue
            pts.append(rope.at(su, -inner * math.cos(math.pi * u)))
        if len(pts) > 1:
            d.append("M" + pl(pts).replace(" ", " L"))
        s += lay
    out.append(f'<path d="{" ".join(d)}" fill="none" stroke="{INK}" stroke-width="{ow:.2f}" '
               f'stroke-linecap="round" stroke-linejoin="round"/>')
    return out


def fray(rope, s, direction, color, width=W):
    """A cut end with ragged, splayed fibres (drawn under the rope body).
    direction = +1 for the far end, -1 for the start."""
    tx, ty = rope.tangent(s)
    tx, ty = tx * direction, ty * direction
    nx, ny = -ty, tx
    hw, ow = width / 2, width * OW
    x0, y0 = rope.at(s)
    P = lambda a, o: (x0 + tx * a + nx * o, y0 + ty * a + ny * o)
    pts = [P(-1.5, -hw), P(0, -hw * 1.02)]
    teeth = 5
    for k in range(teeth + 1):          # zig-zag across the end: long tips, short notches
        o = -hw + 2 * hw * k / teeth
        pts.append(P(2.6 + random.random() * 3.2, o * 1.3))
        if k < teeth:
            pts.append(P(0.4 + random.random() * 1.4, o + hw / teeth))
    pts += [P(0, hw * 1.02), P(-1.5, hw)]
    return [f'<polygon points="{pl(pts)}" fill="{color}" stroke="{INK}" stroke-width="{ow:.2f}" '
            f'stroke-linejoin="round"/>']


def group(parts):
    return '<g>\n    ' + "\n    ".join(parts) + "\n  </g>"


# ---- the picture ----------------------------------------------------------------
layers = []
for i, color in enumerate(COLORS):
    R = R0 - STEP * i
    parts = []
    # branches tuck in underneath their own ring, like a splice
    stubs = {
        0: [seg(CX - R, -12, CX - R, CY)],
        1: [seg(CX - R, -12, CX - R, CY)],
        2: [seg(CX + R, CY, CX + R, 212)],
        3: [seg(-12, CY - R, CX, CY - R), seg(CX + R, CY, CX + R, 212)],
        4: [seg(-12, CY - R, CX, CY - R)],
    }
    for st in stubs[i]:
        parts += draw_rope(Rope(st), color)
    parts += draw_rope(Rope(arc(R, 0, 360), closed=True), color)
    layers.append(group(parts))

# the two loose strings, bound and frayed where they end in the picture
blue = Rope(bezier((-6, 68.5), (78, 60), (112, 120), (100, 184)))
red = Rope(seg(122, 6, 122, 184))
SW = 5
for rope, color, top_end in ((blue, "#00a1de", False), (red, "#c60c30", True)):
    parts = fray(rope, rope.len, 1, color, SW)
    if top_end:
        parts += fray(rope, 0, -1, color, SW)
    parts += draw_rope(rope, color, SW)
    layers.append(group(parts))

body = "\n  ".join(layers)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="600" height="600">
  <rect width="200" height="200" fill="#fbf8f2"/>
  {body}
</svg>
'''
open("/home/kartero/Documents/loop-rope.svg", "w").write(svg)
