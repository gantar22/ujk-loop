# UJK 2027 loop — design history

A T-shirt design for **Usona Junulara Kongreso 2027** (the US Esperanto youth congress, held in
Chicago). It's an abstract take on the Chicago "L" Loop map: five transit-colored lines form a
rounded loop, with lines coming in from the top and left and leaving at the bottom.

This folder holds everything made while designing it (Nov 23–25, 2026), from the first circle
sketch to the current version.

## Current version

**`final/loop-square-obra.png`** (2304 × 3040, transparent background) and the matching `.svg`.

- A square rounded loop of five rings, outside in: brown, purple, orange, green, pink.
- Brown + purple come in from the top; green + pink come in from the left; orange + green leave
  at the bottom right. A red line runs straight through, right of center. A blue line comes in
  from the left, turns down and leaves at the bottom.
- Each line leaving the picture fades out in a dither inspired by *Return of the Obra Dinn*:
  1-bit blue-noise dithering with the pixels rounded into dots and soft squiggles.
  Side-by-side pairs fade as one block, every fade has its own length, and red has the
  longest tail, ending just above the text.
- "Usona Junulara Kongreso" (brown) with "2027" (red) underneath, in bold **Ubuntu**, the font
  used on the [UJK page](https://esperanto-usa.org/eo/junularo/ujk/).

`final/loop-square-obra.py` regenerates the SVG. The fade start/end points per line are in
`BUNDLES` at the top. Export the PNG with:

```
inkscape loop-square-obra.svg --export-type=png --export-width=2304 --export-filename=loop-square-obra.png
```

### Before sending it to print

- **Font:** the SVG needs the Ubuntu font installed to look right. Use the PNG, or convert the
  text to outlines/paths first.
- **Resolution:** print shops usually want 300 dpi. For a 12-inch-wide print that's about
  3600 px wide; re-export at that width.
- **Text color:** brown text suits a light shirt but would vanish on a dark one.
- **Exporting:** use Inkscape, not ImageMagick. ImageMagick picked a thin italic Ubuntu instead
  of bold.

## Palette

| Line | Hex |
|---|---|
| Brown | `#7c4527` |
| Purple | `#9e6ce4` |
| Orange | `#f55f24` |
| Green | `#59a848` |
| Pink | `#ff9f9c` |
| Red | `#f00038` |
| Blue | `#427eff` |

We went through several palettes on coolors.co; this one ended up with salmon pink
`#ff9f9c`, taken from a `loop(1).svg` you made.

## How it got here

1. **Circle sketch** (`early/`). It started as an SVG of concentric rainbow rings (brown,
   purple, orange, green, pink) with a red vertical line and a blue reverse C, based on a
   photo of the Chicago Loop map. The rings became **rounded rectangles** with only 90° straight
   segments, then lines were added coming in and out the way they do on the real map. The colors
   went through several coolors palettes, then the background changed to light grey and then a
   dark off-white (`#e3dfd6`). "UJK" and "2027" were added inside the loop, stacked vertically,
   first in green and then one line color per letter. `early/loop.svg` is that version.
   `early/loop-hybrid.svg` is the same design in the brighter palette from the "friendly"
   experiment.

2. **Tall version** (`tall-backgrounds/`). The loop was stretched to the **golden ratio**
   (200 × 324), the text made bigger, UJK placed at the top of its space and 2027 at the bottom,
   and the font switched to Ubuntu. Then the same design was tried on different backgrounds:
   - `loop-tall` off-white, `loop-tall-transparent` no background
   - `loop-tall-navy` / `loop-tall-navy-light` navy, then a lighter blue
   - `loop-tall-yellow` pale yellow, from `loop(1).svg`
   - `loop-tall-sky` the Chicago flag blue, `#41B6E6` (Pantone 298), from the city's brand
     guide. Too dark.
   - `loop-tall-bluegrey` too grey; `loop-tall-steel` light steel blue `#bcd0e8`
   - `loop-tall-steel-textured` a heather-jersey fabric texture made with SVG noise filters

3. **Fading the lines out at the edges** (`edge-fades/`), roughly in order:
   - `loop-tall-fade` a smooth gradient fade
   - `loop-tall-dither` random square pixels with patchy density
   - `loop-tall-dots` the same with round dots
   - `loop-tall-halftone` dots that shrink toward the edge, random sizes, no overlaps
   - `loop-tall-dissolve` (`loop-dissolve.py`) each line fades over its own length, red
     longest, with a smooth wavy edge where the solid line breaks up
   - Then, after reading about *Return of the Obra Dinn* and Surma's
     [Ditherpunk](https://surma.dev/things/ditherpunk/) article, real threshold dithering
     (`loop-obra.py`):
     - `loop-tall-obra-bayer` 8×8 ordered (Bayer) dither: crosshatch patterns
     - `loop-tall-obra-bluenoise` 64×64 blue noise from the void-and-cluster algorithm:
       even but random, with squiggly clusters. **This was the favorite.**
     - `loop-tall-obra-fine` finer, rounded pixels. Looks fuzzier, but the dots may be too
       small to print on fabric.
     - `loop-tall-obra-round` (`loop-obra-round.py`) blue noise with rounded pixels: blur the
       1-bit mask, then snap it back to hard edges. More room around the loop, longer and more
       varied tails, red starting late and running furthest, blue going further than green/pink
       on the left.

4. **Final** (`final/`). Back to a square loop with the middle cleared and the congress name
   set underneath.

## Side experiments (`side-experiments/`)

These came from a separate forked session that explored other styles. Each has its own
generator script; `.bak` files are earlier copies:

- `loop-friendly*.svg` a chunky, rounded, playful style with darker "lips" under each shape
- `loop-vortex.svg` the rings as a spiraling vortex with brush-stroke lines
- `loop-liquid.svg` liquid-looking rings
- `loop-rope.svg` the rings drawn as twisted rope
- `loop-particles.html` an animated particle version, opened in a browser

## Tools (`tools/`)

- `loop-editor.html` open it in a browser to recolor any of these SVGs. There's a color
  picker per line, preset palettes, click-to-find-a-color, live SVG source editing and a
  download button.

## Scripts

All scripts are plain Python 3 (no extra packages) and write their SVG next to themselves:

| Script | Makes |
|---|---|
| `final/loop-square-obra.py` | the current version |
| `edge-fades/loop-obra-round.py` | the tall rounded blue-noise version |
| `edge-fades/loop-obra.py` | blue-noise, Bayer, fine and an earlier rounded version (`loop-tall-obra-round-first.svg`) |
| `edge-fades/loop-dissolve.py` | the wavy-edged round-dot dissolve |

## References

- Lucas Pope's dithering devlog post:
  https://forums.tigsource.com/index.php?topic=40832.msg1363742#msg1363742
- Set Side B, "A forum post about the dithering in Return of the Obra Dinn":
  https://setsideb.com/a-forum-post-about-the-dithering-in-return-of-the-obra-dinn/
- Surma, "Ditherpunk": https://surma.dev/things/ditherpunk/
- City of Chicago design system (flag blue): https://design.chicago.gov/flag
