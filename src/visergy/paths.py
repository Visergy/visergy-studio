"""Project folder discovery and file naming.

A project folder contains a visible control file, `project.txt`, holding only the project number.
The CLI walks up from the current folder until it finds one.
"""

from __future__ import annotations

import re
from pathlib import Path

from .errors import ProjectNotFound

CONTROL_FILE = "project.txt"
PROJECT_NUMBER_RE = re.compile(r"^P\d{4}-\d{3,}$")


def find_project_dir(start: Path | None = None) -> Path:
    """Walk up from `start` (default: cwd) to the nearest folder containing the control file."""
    here = (start or Path.cwd()).resolve()
    for folder in (here, *here.parents):
        if (folder / CONTROL_FILE).is_file():
            return folder
    raise ProjectNotFound(
        f"no {CONTROL_FILE} found in {here} or any parent folder. "
        "Run this from inside a project folder."
    )


def read_project_number(project_dir: Path) -> str:
    text = (project_dir / CONTROL_FILE).read_text(encoding="utf-8").strip()
    if not PROJECT_NUMBER_RE.match(text):
        raise ProjectNotFound(
            f"{project_dir / CONTROL_FILE} must contain only a project number like P2026-001, "
            f"found {text[:40]!r}"
        )
    return text


def locate_project(start: Path | None = None) -> tuple[Path, str]:
    folder = find_project_dir(start)
    return folder, read_project_number(folder)


def write_control_file(project_dir: Path, number: str) -> Path:
    if not PROJECT_NUMBER_RE.match(number):
        raise ValueError(f"invalid project number: {number!r}")
    path = project_dir / CONTROL_FILE
    path.write_text(number + "\n", encoding="utf-8")
    return path


def pdf_filename(kind: str, number: str, version: int | None = None) -> str:
    """Q-0001-v2.pdf for quotes, INV-0003.pdf for invoices."""
    if kind == "quote":
        if version is None:
            raise ValueError("quotes need a version")
        return f"{number}-v{version}.pdf"
    if kind == "invoice":
        return f"{number}.pdf"
    raise ValueError(f"unknown document kind: {kind!r}")


def relative_pdf_path(project_dir: Path, pdf_path: Path) -> str:
    """The value stored in the database: relative to the project folder, with / separators."""
    return pdf_path.resolve().relative_to(project_dir.resolve()).as_posix()


def folder_name(number: str, title: str, max_len: int = 60) -> str:
    """'P2026-001 Thermal review' with filesystem-hostile characters removed."""
    slug = re.sub(r"[^A-Za-z0-9 _-]+", "", title).strip()
    slug = re.sub(r"\s+", " ", slug)[:max_len].strip()
    return f"{number} {slug}".strip()
