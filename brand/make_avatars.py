"""Render square logo images and LinkedIn banners for the Visergy profiles.

Both sites show an organisation logo as a square (GitHub rounds the corners). LinkedIn suggests
400 x 400 px and GitHub at least 500 x 500 px under 1 MB, so these are 800 x 800 px. Every image is
saved as both PNG and JPEG, flattened to plain RGB (no alpha channel) with an sRGB profile and a
72 dpi tag, because LinkedIn's uploader rejected Typst's RGBA PNGs. Run from the repo root after
changing the artwork or colours (Pillow is needed only here, for the conversion):

    uv run --with pillow python brand/make_avatars.py
"""

import io
import re
import tomllib
from pathlib import Path

import typst
from PIL import Image, ImageCms

BRAND = Path(__file__).parent
OUT = BRAND / "avatars"
SIZE_PX = 800
THEME = tomllib.loads((BRAND / "theme.toml").read_text())["colours"]

# The "v" from the wordmark, on its own, for icons too small for the whole word to read.
# It is the fourth path in logo.svg (after two clip rectangles and the sunburst dot).
V_PATH_INDEX = 3
V_VIEWBOX = "-1 31 35 33.2"  # the v's bounds in logo.svg units, rounded outward
V_OUTPUTS = {"logo-v.svg": THEME["accent"], "logo-v-white.svg": "#ffffff"}

# Output name (without extension) -> (background, logo file, logo width as a share of the square).
# The wordmark keeps clear of the corners, so it also survives a circular crop.
AVATARS = {
    "visergy-logo-white": ("#ffffff", "logo.svg", 0.78),
    "visergy-logo-deep": (THEME["deep"], "logo.svg", 0.78),
    "visergy-sunburst-deep": (THEME["deep"], "sunburst.svg", 0.76),
    "visergy-v-deep": (THEME["deep"], "logo-v.svg", 0.6),
    "visergy-v-white": ("#ffffff", "logo-v.svg", 0.6),
    "visergy-v-turquoise": (THEME["accent"], "logo-v-white.svg", 0.6),
}

# LinkedIn company page cover: output name -> (width, height) in px. Deep blue with the fine
# sunburst running off the right edge, as on the "field" cover. No text: LinkedIn puts the logo
# over the lower left, so that corner is left empty. 1128 x 191 is LinkedIn's display size;
# 4200 x 700 is the larger upload size some guides recommend.
BANNERS = {
    "linkedin-banner-company": (1128, 191),
    "linkedin-banner-company-4200": (4200, 700),
}
SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


def write_v_logos() -> None:
    """Cut the "v" out of the wordmark into its own SVGs, one per colour."""
    logo = (BRAND / "logo.svg").read_text()
    d = re.findall(r'<path[^>]*\bd="([^"]+)"', logo)[V_PATH_INDEX]
    for name, colour in V_OUTPUTS.items():
        (BRAND / name).write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{V_VIEWBOX}">\n'
            f'<path fill="{colour}" d="{d}"/>\n'
            "</svg>\n"
        )


def source(background: str, logo: str, share: float) -> bytes:
    return f"""
#set page(width: 800pt, height: 800pt, margin: 0pt, fill: rgb("{background}"))
#place(center + horizon, image("{logo}", width: {share * 100}%))
""".encode()


def banner_svg(width: int, height: int) -> str:
    """The whole banner as one SVG. Typst clips an SVG image placed partly off the page, so the
    sunburst's lines are moved and scaled inside a drawing exactly the banner's size instead."""
    sunburst = (BRAND / "sunburst-thin-turquoise.svg").read_text()
    size = float(re.search(r'viewBox="0 0 ([\d.]+)', sunburst).group(1))
    rays = re.search(r"<g\b.*</g>", sunburst, re.DOTALL).group(0)
    diameter = 2.4 * height
    left, top = width - 0.55 * diameter, (height - diameter) / 2
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" fill="{THEME["deep"]}"/>'
        f'<g transform="translate({left} {top}) scale({diameter / size})">{rays}</g>'
        "</svg>"
    )


def banner_source(width: int, height: int) -> bytes:
    return f"""
#set page(width: {width}pt, height: {height}pt, margin: 0pt)
#image(bytes(sys.inputs.svg), width: 100%)
""".encode()


def save(png: bytes, name: str) -> None:
    """Save Typst's RGBA PNG as plain RGB PNG and JPEG files."""
    image = Image.open(io.BytesIO(png)).convert("RGB")
    for path in (OUT / f"{name}.png", OUT / f"{name}.jpg"):
        image.save(path, dpi=(72, 72), icc_profile=SRGB, quality=95)
        print(path)


def main() -> None:
    write_v_logos()
    OUT.mkdir(exist_ok=True)
    for name, (background, logo, share) in AVATARS.items():
        png = typst.compile(
            source(background, logo, share), format="png", ppi=72 * SIZE_PX / 800, root=BRAND
        )
        save(png, name)
    for name, (width, height) in BANNERS.items():
        png = typst.compile(
            banner_source(width, height),
            format="png",
            ppi=72,
            root=BRAND,
            sys_inputs={"svg": banner_svg(width, height)},
        )
        save(png, name)


if __name__ == "__main__":
    main()
