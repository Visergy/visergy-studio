"""Report sources: a Markdown file with TOML front matter and local images.

    +++
    title = "Thermal performance review"
    subtitle = "Stage 2 findings"     # optional
    toc = true                        # optional, default true
    +++

    # Summary
    ![Caption for the figure](figures/option-b.png)

Only inline image tags are supported. Image paths are relative to the Markdown file and must stay
inside its folder.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .errors import ReportSourceError
from .render import render_pdf

_FRONT_MATTER_RE = re.compile(r"\A\+\+\+[ \t]*\r?\n(.*?)\r?\n\+\+\+[ \t]*(?:\r?\n|\Z)", re.S)
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
_FRONT_MATTER_KEYS = {"title", "subtitle", "toc"}


@dataclass(frozen=True)
class ReportSource:
    path: Path
    title: str
    subtitle: str
    toc: bool
    body: str
    images: dict[str, Path]  # path as written in the Markdown -> file on disk


def load_report_source(path: Path) -> ReportSource:
    if not path.is_file():
        raise ReportSourceError(f"report file not found: {path}")
    text = path.read_text(encoding="utf-8")
    match = _FRONT_MATTER_RE.match(text)
    if not match:
        raise ReportSourceError(f"{path} must start with a +++ front matter block")
    try:
        meta = tomllib.loads(match.group(1))
    except tomllib.TOMLDecodeError as e:
        raise ReportSourceError(f"{path}: front matter is not valid TOML: {e}") from None

    unknown = set(meta) - _FRONT_MATTER_KEYS
    if unknown:
        raise ReportSourceError(f"{path}: unknown front matter keys: {', '.join(sorted(unknown))}")
    title = meta.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ReportSourceError(f"{path}: front matter needs a title")
    subtitle = meta.get("subtitle", "")
    toc = meta.get("toc", True)
    if not isinstance(subtitle, str) or not isinstance(toc, bool):
        raise ReportSourceError(f"{path}: subtitle must be text and toc must be true or false")

    body = text[match.end() :]
    return ReportSource(path, title, subtitle, toc, body, find_images(body, path.parent))


def find_images(body: str, base_dir: Path) -> dict[str, Path]:
    """Every inline image reference, checked to exist and to stay inside base_dir."""
    images = {}
    root = base_dir.resolve()
    for ref in _IMAGE_RE.findall(body):
        rel = PurePosixPath(ref)
        if "://" in ref or rel.is_absolute() or ".." in rel.parts:
            raise ReportSourceError(
                f"image {ref!r} must be a relative path inside the report folder"
            )
        file = (root / rel).resolve()
        if not file.is_relative_to(root) or not file.is_file():
            raise ReportSourceError(f"image not found: {ref} (looked in {root})")
        images[ref] = file
    return images


def render_report(source: ReportSource, data: dict) -> bytes:
    """Add the report itself to `data` (doc, business, client, project, history) and render."""
    report = {
        **data["report"],
        "title": source.title,
        "subtitle": source.subtitle,
        "toc": source.toc,
        "body": source.body,
    }
    files = {f"report/{ref}": file for ref, file in source.images.items()}
    return render_pdf("report.typ", {**data, "report": report}, files)
