"""Project folder discovery and file naming.

A project folder contains a visible control file, `project.txt`, holding only the project number.
The CLI walks up from the current folder until it finds one.
"""

from __future__ import annotations

import re
from pathlib import Path

from .errors import ProjectNotFound

CONTROL_FILE = "project.txt"
PROJECT_NUMBER_RE = re.compile(r"^\d{4}$")


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
            f"{project_dir / CONTROL_FILE} must contain only a four-digit project number "
            f"like 0059, found {text[:40]!r}"
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


def pdf_filename(kind: str, number: str, version: int | str | None = None) -> str:
    """Proposal_26001-v2.pdf, Invoice_26002.pdf, Report_0059-R01-B.pdf, like the old files.

    `version` is the quote version (an int) or the report revision letter.
    """
    if kind == "invoice":
        return f"Invoice_{number}.pdf"
    if kind not in ("quote", "report"):
        raise ValueError(f"unknown document kind: {kind!r}")
    if version is None:
        raise ValueError(f"a {kind} needs a version")
    if kind == "quote":
        return f"Proposal_{number}-v{version}.pdf"
    return f"Report_{number}-{version}.pdf"


def relative_pdf_path(project_dir: Path, pdf_path: Path) -> str:
    """The value stored in the database: relative to the project folder, with / separators."""
    return pdf_path.resolve().relative_to(project_dir.resolve()).as_posix()


def folder_name(number: str, title: str, max_len: int = 40) -> str:
    """'0059-PhilipStreet': the project number and the title in CamelCase, like the old folders."""
    words = re.findall(r"[A-Za-z0-9]+", title)
    slug = "".join(w[0].upper() + w[1:] for w in words)[:max_len]
    return f"{number}-{slug}" if slug else number
