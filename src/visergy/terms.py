"""Versioned standard terms.

Files live in terms/terms-<version>.toml and are never edited once used.
"""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from .errors import ConfigError

_VERSION_RE = re.compile(r"^v\d+$")


@dataclass(frozen=True)
class Terms:
    version: str
    sections: list[dict[str, str]]
    sha256: str


def load_terms(version: str, terms_dir: Path) -> Terms:
    if not _VERSION_RE.match(version):
        raise ConfigError(f"terms version must look like 'v1', got {version!r}")
    path = terms_dir / f"terms-{version}.toml"
    if not path.is_file():
        raise ConfigError(f"terms file not found: {path}")
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != version:
        raise ConfigError(f"{path} declares version {data.get('version')!r}, expected {version!r}")
    sections = data.get("sections", [])
    for s in sections:
        if set(s) != {"heading", "body"} or not all(isinstance(v, str) for v in s.values()):
            raise ConfigError(f"{path}: each section needs exactly a string heading and body")
    canonical = json.dumps(
        {"version": version, "sections": sections},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return Terms(version=version, sections=sections, sha256=digest)
