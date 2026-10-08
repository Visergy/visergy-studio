"""Redraw the sunburst artwork as thin lines (white and turquoise), for the "field" cover style.

The original artwork (sunburst-white.svg) is one filled outline. This finds each of its rays and
redraws them as stroked lines along the same angles and lengths, so the hand-drawn irregularity is
kept. Run from the repo root after changing the artwork:

    uv run python brand/make_thin_sunburst.py
"""

import math
import re
from pathlib import Path

BRAND = Path(__file__).parent
SOURCE = BRAND / "sunburst-white.svg"
# Output file -> line colour. Turquoise is the logo colour (RGB 0, 171, 191).
OUTPUTS = {"sunburst-thin-white.svg": "#ffffff", "sunburst-thin-turquoise.svg": "#00abbf"}
STROKE_WIDTH = 1.6  # the original rays are about 8 units wide in a 633-unit drawing


def find_rays(svg: str) -> tuple[float, list[tuple[float, float, float]]]:
    """(drawing size, [(angle, inner radius, outer radius), ...]) from the filled outline."""
    size = float(re.search(r'viewBox="0 0 ([\d.]+)', svg).group(1))
    outline = re.search(r'<path[^>]*fill="rgb[^"]*"[^>]*d="([^"]+)"', svg).group(1)
    centre = size / 2
    rays = []
    for shape in re.split(r"(?=M)", outline):
        numbers = [float(n) for n in re.findall(r"-?[\d.]+", shape)]
        points = list(zip(numbers[0::2], numbers[1::2], strict=False))
        if len(points) < 4:
            continue
        mid_x = sum(p[0] for p in points) / len(points)
        mid_y = sum(p[1] for p in points) / len(points)
        angle = math.atan2(mid_y - centre, mid_x - centre)
        along = [(x - centre) * math.cos(angle) + (y - centre) * math.sin(angle) for x, y in points]
        rays.append((angle, min(along), max(along)))
    return size, sorted(rays)


def main() -> None:
    size, rays = find_rays(SOURCE.read_text(encoding="utf-8"))
    c = size / 2
    lines = "\n".join(
        f'  <line x1="{c + r0 * math.cos(a):.2f}" y1="{c + r0 * math.sin(a):.2f}" '
        f'x2="{c + r1 * math.cos(a):.2f}" y2="{c + r1 * math.sin(a):.2f}"/>'
        for a, r0, r1 in rays
    )
    for name, colour in OUTPUTS.items():
        (BRAND / name).write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size:.0f}" height="{size:.0f}" '
            f'viewBox="0 0 {size:.0f} {size:.0f}">\n'
            f'<g stroke="{colour}" stroke-width="{STROKE_WIDTH}" '
            f'stroke-linecap="round" fill="none">\n'
            f"{lines}\n</g>\n</svg>\n",
            encoding="utf-8",
        )
        print(f"wrote {BRAND / name} ({len(rays)} rays)")


if __name__ == "__main__":
    main()
