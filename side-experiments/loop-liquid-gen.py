import math, random

random.seed(3)
CX, CY = 100, 100
COLORS = ["#62361b", "#522398", "#f9461c", "#009b3a", "#e27ea6"]  # outside -> in
R0, STEP, W = 80, 6, 6.4     # outer radius, ring spacing, ring thickness


# per-corner inset of the rounding centre (0 = full quarter circle, larger = tighter
# corner). Corners share centres across rings, so the rings stay evenly spaced.
#        (sx, sy): inset   -- y points down, so sy=-1 is the top
CORNER = {(-1, -1): 32,   # top left: tighter
          (1, 1): 32,     # bottom right: tighter
          (1, -1): 0,     # top right: fully round
          (-1, 1): 0}     # bottom left: fully round


def ring_point(rx, ry, a):
    """Point where the ray from the centre at angle a meets a rounded square of
    half-size rx whose corners follow CORNER."""
    R = rx
    dx, dy = math.cos(a), math.sin(a)
    sx, sy = (1 if dx >= 0 else -1), (1 if dy >= 0 else -1)
    c = CORNER[(sx, sy)]
    t = R / max(abs(dx), abs(dy))           # hit on the square
    x, y = t * dx, t * dy
    if abs(x) > c and abs(y) > c:            # in the rounded corner: hit the arc instead
        cx, cy, r = sx * c, sy * c, R - c
        b = dx * cx + dy * cy
        t = b + math.sqrt(b * b - (cx * cx + cy * cy - r * r))
        x, y = t * dx, t * dy
    return CX + x, CY + y


def ring(i, color):
    rx = ry = R0 - STEP * i
    R = rx
    parts = [f'<ellipse cx="{CX}" cy="{CY}" rx="{rx}" ry="{ry}" fill="none" stroke="{color}" stroke-width="{W}"/>']
    # entrances / exits, like loop.svg: each leaves the ring along a tangent
    stubs = {
        0: [f"M {CX - R} {CY} V -10"],                      # brown: in from the top, joins left side
        1: [f"M {CX - R} {CY} V -10"],                      # purple: same
        2: [f"M {CX + R} {CY} V 210"],                      # orange: out the bottom
        3: [f"M {CX} {CY - R} H -10", f"M {CX + R} {CY} V 210"],  # green: in from left, out the bottom
        4: [f"M {CX} {CY - R} H -10"],                      # pink: in from the left
    }
    parts += [f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{W}"/>' for d in stubs.get(i, [])]
    # the band itself: one pass of a wide rainbow brush, starting and lifting at the
    # lower left, each "bristle" color starting/ending a little out of step
    seam = math.radians(135)
    start = seam + math.radians([2, 6, 1, 8, 4][i])
    taper = math.radians(22)
    # overlap the two ends by more than both tapers combined, so each thin tapered
    # end sits on top of full-width band and no background shows through
    end = start + 2 * math.pi + 2 * taper + math.radians([6, 4, 8, 2, 5][i])
    n = 360
    outer, inner = [], []
    for k in range(n + 1):
        t = start + (end - start) * k / n
        f = max(0.0, min(1, (t - start) / taper, (end - t) / taper)) ** 0.6
        hw = W / 2 * f
        outer.append(ring_point(R + hw, R + hw, t))
        inner.append(ring_point(R - hw, R - hw, t))
    # draw in quarter-circle chunks so the overlapping seam can't confuse the fill
    polys = []
    for a0 in range(0, n, 90):
        a1 = min(a0 + 91, n + 1)
        pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in outer[a0:a1] + inner[a0:a1][::-1])
        polys.append(f'<polygon points="{pts}" fill="{color}"/>')
    parts[0] = "\n    ".join(polys)
    return f'<g filter="url(#goo)">\n    ' + "\n    ".join(parts) + "\n  </g>"


def stream(d, color, blobs, drops):
    parts = [f'<path d="{d}" fill="none" stroke="{color}" stroke-width="5" stroke-linecap="round"/>']
    parts += [f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>' for x, y, r in blobs + drops]
    return f'<g filter="url(#goo)">\n    ' + "\n    ".join(parts) + "\n  </g>"


rings = "\n  ".join(ring(i, c) for i, c in enumerate(COLORS))

red = stream("M 122 6 V 184", "#c60c30",
             blobs=[(122, 186, 3.6)],          # liquid pooling at the end...
             drops=[(122, 194, 2.6)])          # ...and a drip pulling off
blue = stream("M -4 68 C 78 60, 112 120, 100 184", "#00a1de",
              blobs=[(100, 186, 3.6)],
              drops=[(100, 194, 2.6)])

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="600" height="600">
  <defs>
    <!-- "goo": blur shapes together, then sharpen the alpha so they merge like liquid -->
    <!-- one shared wobble so all five colors move together like a single brush -->
    <filter id="wobble" x="-10%" y="-10%" width="120%" height="120%">
      <feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="5" result="n"/>
      <feDisplacementMap in="SourceGraphic" in2="n" scale="3" xChannelSelector="R" yChannelSelector="G"/>
    </filter>
    <filter id="goo" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="2.2" result="b"/>
      <feColorMatrix in="b" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 22 -9"/>
    </filter>
  </defs>
  <rect width="200" height="200" fill="#fbf8f2"/>
  <g filter="url(#wobble)">
  {rings}
  </g>
  {blue}
  {red}
</svg>
'''
open("/home/kartero/Documents/loop-liquid.svg", "w").write(svg)
