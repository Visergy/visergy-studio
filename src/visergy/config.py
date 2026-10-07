"""Load and check config.toml: business identity, bank details, paths, numbering, defaults.

The file is gitignored and holds bank details, so nothing here may print them: the bank fields are
left out of reprs, and error messages name the field, never its value (rule 6).

Location: the VISERGY_CONFIG environment variable, else config.toml in the repo root. The
VISERGY_DB environment variable overrides [paths].database.

Fields still holding the values from config.example.toml are allowed when loading, so the tool
works while details are being filled in. `Config.placeholders()` lists them; issuing a document
must refuse while any it needs are still placeholders.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .errors import ConfigError
from .paths import REPO_ROOT

CONFIG_ENV = "VISERGY_CONFIG"
DATABASE_ENV = "VISERGY_DB"
DEFAULT_CONFIG = REPO_ROOT / "config.toml"

# The values config.example.toml ships with. trading_as is left out: its example ("Visergy")
# is the real value.
PLACEHOLDERS = {
    "business.name": "Your Legal Name",
    "business.abn": "00 000 000 000",
    "business.email": "you@example.com",
    "bank.account_name": "Your Legal Name",
    "bank.bsb": "000-000",
    "bank.account_number": "00000000",
}

ABN_WEIGHTS = (10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19)


@dataclass(frozen=True)
class Business:
    name: str
    trading_as: str
    abn: str
    address: tuple[str, ...]
    email: str
    phone: str
    gst_registered: bool

    @property
    def display_name(self) -> str:
        return self.trading_as or self.name


@dataclass(frozen=True)
class Bank:
    account_name: str = field(repr=False)
    bsb: str = field(repr=False)
    account_number: str = field(repr=False)


@dataclass(frozen=True)
class Paths:
    database: Path
    backup_dir: Path
    projects_root: Path | None


@dataclass(frozen=True)
class Config:
    source: Path
    business: Business
    bank: Bank
    paths: Paths
    last_project: int
    quote_validity_days: int
    terms_version: str
    backup_keep_last: int
    backup_keep_daily_days: int

    def placeholders(self) -> list[str]:
        """Fields still holding the example values, as "section.key" names."""
        current = {
            "business.name": self.business.name,
            "business.abn": self.business.abn,
            "business.email": self.business.email,
            "bank.account_name": self.bank.account_name,
            "bank.bsb": self.bank.bsb,
            "bank.account_number": self.bank.account_number,
        }
        return [key for key, value in current.items() if value == PLACEHOLDERS[key]]


def config_path() -> Path:
    env = os.environ.get(CONFIG_ENV)
    return Path(env).expanduser() if env else DEFAULT_CONFIG


def abn_is_valid(abn: str) -> bool:
    """The ATO check: subtract 1 from the first digit, weight the digits, total divisible by 89."""
    digits = [int(c) for c in abn if c.isdigit()]
    if len(digits) != 11 or len(abn.replace(" ", "")) != 11:
        return False
    digits[0] -= 1
    return sum(w * d for w, d in zip(ABN_WEIGHTS, digits, strict=True)) % 89 == 0


def format_abn(abn: str) -> str:
    d = abn.replace(" ", "")
    return f"{d[:2]} {d[2:5]} {d[5:8]} {d[8:]}"


class _Reader:
    """Typed access to one parsed file, with errors that name the field but never its value."""

    def __init__(self, data: dict, source: Path):
        self.data = data
        self.source = source

    def error(self, key: str, problem: str) -> ConfigError:
        return ConfigError(f"{self.source.name}: [{key.replace('.', '].', 1)} {problem}")

    def get(self, key: str, kind: type, default=...):
        section, name = key.split(".")
        table = self.data.get(section, {})
        if not isinstance(table, dict):
            raise ConfigError(f"{self.source.name}: [{section}] must be a table")
        if name not in table:
            if default is ...:
                raise self.error(key, "is missing")
            return default
        value = table[name]
        # bool is a subclass of int, so check it explicitly.
        if not isinstance(value, kind) or (kind is int and isinstance(value, bool)):
            raise self.error(key, f"must be {kind.__name__}")
        return value

    def text(self, key: str, default=...) -> str:
        return self.get(key, str, default).strip()

    def lines(self, key: str) -> tuple[str, ...]:
        value = self.get(key, list)
        if not value or not all(isinstance(v, str) for v in value):
            raise self.error(key, "must be a list of lines of text")
        return tuple(v.strip() for v in value)

    def positive(self, key: str, minimum: int = 1) -> int:
        value = self.get(key, int)
        if value < minimum:
            raise self.error(key, f"must be at least {minimum}")
        return value

    def path(self, key: str) -> Path:
        return Path(self.text(key)).expanduser()


def load_config(path: Path | None = None) -> Config:
    source = path or config_path()
    if not source.is_file():
        raise ConfigError(
            f"no config file at {source}: copy config.example.toml to config.toml and fill it in"
            f" (or set {CONFIG_ENV})"
        )
    try:
        data = tomllib.loads(source.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        # The message gives the line and column, not the line's content.
        raise ConfigError(f"{source.name} is not valid TOML: {e}") from None

    r = _Reader(data, source)

    abn = r.text("business.abn")
    if abn != PLACEHOLDERS["business.abn"]:
        if not abn_is_valid(abn):
            raise r.error("business.abn", "is not a valid ABN (check the digits)")
        abn = format_abn(abn)

    bsb = r.text("bank.bsb")
    if bsb != PLACEHOLDERS["bank.bsb"]:
        digits = bsb.replace("-", "").replace(" ", "")
        if len(digits) != 6 or not digits.isdigit():
            raise r.error("bank.bsb", "must be six digits")
        bsb = f"{digits[:3]}-{digits[3:]}"

    account_number = r.text("bank.account_number")
    if not account_number.replace(" ", "").isdigit():
        raise r.error("bank.account_number", "must be digits")

    projects_root = r.text("paths.projects_root", "")
    database = os.environ.get(DATABASE_ENV)

    return Config(
        source=source,
        business=Business(
            name=r.text("business.name"),
            trading_as=r.text("business.trading_as", ""),
            abn=abn,
            address=r.lines("business.address"),
            email=r.text("business.email"),
            phone=r.text("business.phone"),
            gst_registered=r.get("business.gst_registered", bool),
        ),
        bank=Bank(
            account_name=r.text("bank.account_name"),
            bsb=bsb,
            account_number=account_number,
        ),
        paths=Paths(
            database=Path(database).expanduser() if database else r.path("paths.database"),
            backup_dir=r.path("paths.backup_dir"),
            projects_root=Path(projects_root).expanduser() if projects_root else None,
        ),
        last_project=r.positive("numbering.last_project", minimum=0),
        quote_validity_days=r.positive("defaults.quote_validity_days"),
        terms_version=r.text("defaults.terms_version"),
        backup_keep_last=r.positive("backup.keep_last"),
        backup_keep_daily_days=r.positive("backup.keep_daily_days"),
    )
