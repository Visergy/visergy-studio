"""Compile a Typst template to PDF.

Typst can only read files under one root folder, and project folders (images) live outside the
repo (templates, brand). So each render copies what it needs into a temporary build folder:

    build/templates/   build/brand/   build/report/<image paths>   (only for reports)

Data reaches the template only as one JSON string in sys.inputs (rule 4).
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import typst

from .errors import RenderError

# The repo root, found from src/visergy/render.py. Works for the editable install uv makes.
REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = REPO_ROOT / "templates"
BRAND_DIR = REPO_ROOT / "brand"


def render_pdf(template: str, data: dict, files: dict[str, Path] | None = None) -> bytes:
    """Render templates/<template> with `data`. `files` maps build-folder paths to source files."""
    with tempfile.TemporaryDirectory(prefix="visergy-build-") as tmp:
        build = Path(tmp)
        shutil.copytree(TEMPLATES_DIR, build / "templates")
        shutil.copytree(BRAND_DIR, build / "brand")
        for rel, src in (files or {}).items():
            dest = build / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
        try:
            return typst.compile(
                str(build / "templates" / template),
                root=str(build),
                font_paths=[str(build / "brand" / "fonts")],
                ignore_system_fonts=True,  # same fonts on every machine
                sys_inputs={"data": json.dumps(data, ensure_ascii=False)},
            )
        except typst.TypstError as e:
            raise RenderError(f"could not render {template}: {e}") from None
