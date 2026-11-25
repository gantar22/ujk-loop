import math, random

random.seed(7)
CX, CY = 100, 100
COLORS = ["#62361b", "#522398", "#f9461c", "#009b3a", "#e27ea6"]  # outside -> in
R0 = 130          # start radius (clipped to the vortex edge)
TURNS = 4.0
B = math.log(R0 / 2.0) / (TURNS * 2 * math.pi)   # log-spiral tightness
PHI = 2 * math.pi / len(COLORS)


def r(t):
    return R0 * math.exp(-B * t)


def pt(radius, ang):
    return (CX + radius * math.cos(ang), CY + radius * math.sin(ang))


def fmt(points):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in points)


def spiral_arm(i, steps=500):
    """Area between two log spirals offset by one color-width."""
    T0, T = -2 * math.pi, TURNS * 2 * math.pi
    ts = [T0 + (T - T0) * k / steps for k in range(steps + 1)]
    outer = [pt(r(t + i * PHI), -t) for t in ts]
    inner = [pt(r(t + (i + 1) * PHI), -t) for t in reversed(ts)]
    return f'<polygon points="{fmt(outer + inner)}" fill="{COLORS[i]}"/>'


def streak(offset, width, color, opacity, steps=300):
    T = TURNS * 2 * math.pi
    pts = [pt(r(t + offset), -t) for t in (T * k / steps for k in range(steps + 1))]
    return (f'<polyline points="{fmt(pts)}" fill="none" stroke="{color}" '
            f'stroke-width="{width}" stroke-opacity="{opacity}" stroke-linecap="round"/>')


def bezier(p0, p1, p2, p3, n):
    out = []
    for k in range(n + 1):
        s = k / n
        u = 1 - s
        out.append((u**3 * p0[0] + 3 * u * u * s * p1[0] + 3 * u * s * s * p2[0] + s**3 * p3[0],
                    u**3 * p0[1] + 3 * u * u * s * p1[1] + 3 * u * s * s * p2[1] + s**3 * p3[1]))
    return out


def brush(center, width, color, light):
    """Smooth tapered stroke along a centerline."""
    n = len(center)
    normals = []
    for k in range(n):
        a = center[max(k - 1, 0)]
        b = center[min(k + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        normals.append((-dy / L, dx / L))

    def w(s):  # smooth swell: tapered at both ends, a little heavier at the start
        return width * math.sin(math.pi * s) ** 0.5 * (1 - 0.35 * s)

    left, right = [], []
    for k, (c, nm) in enumerate(zip(center, normals)):
        hw = w(k / (n - 1)) / 2
        left.append((c[0] + nm[0] * hw, c[1] + nm[1] * hw))
        right.append((c[0] - nm[0] * hw, c[1] - nm[1] * hw))
    out = [f'<polygon points="{fmt(left + right[::-1])}" fill="{color}"/>']

    return "\n    ".join(out)


rings = "\n    ".join(
    f'<ellipse cx="{CX}" cy="{CY}" rx="{62 - 7 * i}" ry="{84 - 7 * i}" stroke="{c}"/>'
    for i, c in enumerate(COLORS))
streaks = "\n      ".join(
    streak(random.uniform(0, 2 * math.pi), random.uniform(0.3, 1.2),
           random.choice(["#fff", "#000"]), random.uniform(0.12, 0.3))
    for _ in range(26))

red = bezier((124, -4), (121, 60), (125, 140), (121, 204), 160)
blue = bezier((-4, 34), (88, 26), (114, 118), (100, 204), 160)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="600" height="600">
  <defs>
    <filter id="fluid" x="-10%" y="-10%" width="120%" height="120%">
      <feTurbulence type="fractalNoise" baseFrequency="0.018" numOctaves="3" seed="4" result="n"/>
      <feDisplacementMap in="SourceGraphic" in2="n" scale="5" xChannelSelector="R" yChannelSelector="G" result="d"/>
      <feGaussianBlur in="d" stdDeviation="0.35"/>
    </filter>
    <filter id="edge" x="-10%" y="-10%" width="120%" height="120%">
      <feTurbulence type="fractalNoise" baseFrequency="0.05" numOctaves="2" seed="9" result="n"/>
      <feDisplacementMap in="SourceGraphic" in2="n" scale="14" xChannelSelector="R" yChannelSelector="G"/>
    </filter>
    <filter id="brush" x="-20%" y="-5%" width="140%" height="110%">
      <feDropShadow dx="0.5" dy="0.7" stdDeviation="0.7" flood-opacity="0.18"/>
    </filter>
  </defs>
  <rect width="200" height="200" fill="#fbf8f2"/>

  <!-- Ring: tall oval bands, brown/purple/orange/green/pink from the outside in, hollow middle -->
  <g filter="url(#fluid)" fill="none" stroke-width="7.5">
    {rings}
  </g>

  <!-- Brush strokes piercing the vortex -->
  <g filter="url(#brush)">
    {brush(blue, 13, "#00a1de", "#bfefff")}
  </g>
  <g filter="url(#brush)">
    {brush(red, 12, "#c60c30", "#ff9fae")}
  </g>
</svg>
'''
open("/home/kartero/Documents/loop-vortex.svg", "w").write(svg)
