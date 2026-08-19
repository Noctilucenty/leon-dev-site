#!/usr/bin/env python3
"""Renders assets/favicon.svg to the raster icons browsers ask for by name:
/apple-touch-icon.png (iOS home screen, 180x180) and /favicon.ico (16/32/48).

There is no SVG rasteriser on this machine, so the mark is redrawn in Pillow
from the same geometry as the SVG — keep the two in step by hand if the SVG
ever changes. Drawn at 8x and downsampled, which is where the antialiasing
comes from.

Run:  python3 tools/make_icons.py
"""
import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BG      = (8, 8, 10, 255)          # #08080a
ACCENT  = (158, 147, 228, 255)     # #9E93E4
INK     = (239, 237, 230, 255)     # #EFEDE6
RING    = (158, 147, 228, 89)      # #9E93E4 at .35 opacity

S = 8                              # supersampling factor; viewBox is 64 units


def render(px):
    """Draw the mark at `px` square, matching the 64-unit viewBox."""
    n = 64 * S
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    d.rounded_rectangle([0, 0, n - 1, n - 1], radius=14 * S, fill=BG)
    d.rounded_rectangle([1 * S, 1 * S, 63 * S, 63 * S], radius=int(13.2 * S),
                        outline=RING, width=2 * S)

    # path M20 15 v26 h17 — one stroke, round cap and join
    w = int(6.5 * S)
    d.line([(20 * S, 15 * S), (20 * S, 41 * S)], fill=INK, width=w)
    d.line([(20 * S, 41 * S), (37 * S, 41 * S)], fill=INK, width=w)
    for cx, cy in ((20, 15), (20, 41), (37, 41)):           # round the ends
        d.ellipse([cx * S - w // 2, cy * S - w // 2, cx * S + w // 2, cy * S + w // 2], fill=INK)

    d.ellipse([(45 - 5) * S, (41 - 5) * S, (45 + 5) * S, (41 + 5) * S], fill=ACCENT)

    return img.resize((px, px), Image.LANCZOS)


def main():
    apple = render(180)
    apple_path = os.path.join(ROOT, "apple-touch-icon.png")
    apple.convert("RGB").save(apple_path, "PNG", optimize=True)
    print("wrote", apple_path, apple.size)

    ico_path = os.path.join(ROOT, "favicon.ico")
    render(64).save(ico_path, "ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    print("wrote", ico_path)


if __name__ == "__main__":
    main()
