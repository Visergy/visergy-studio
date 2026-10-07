"""config.toml loading. Every value here is made up; no real details belong in tests."""

from pathlib import Path

import pytest

from visergy.config import (
    CONFIG_ENV,
    DATABASE_ENV,
    abn_is_valid,
    config_path,
    format_abn,
    load_config,
)
from visergy.errors import ConfigError

REPO = Path(__file__).parent.parent
EXAMPLE = REPO / "config.example.toml"

# 51 824 753 556 is the ATO's published example ABN; the bank values are invented.
FILLED = {
    'name = "Your Legal Name"': 'name = "Alex Example"',
    'abn = "00 000 000 000"': 'abn = "51824753556"',
    'email = "you@example.com"': 'email = "alex@visergy.example"',
    'account_name = "Your Legal Name"': 'account_name = "Alex Example"',
    'bsb = "000-000"': 'bsb = "123456"',
    'account_number = "00000000"': 'account_number = "98765432"',
}


@pytest.fixture(autouse=True)
def no_env(monkeypatch):
    monkeypatch.delenv(CONFIG_ENV, raising=False)
    monkeypatch.delenv(DATABASE_ENV, raising=False)


def write(tmp_path, text: str) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(text, encoding="utf-8")
    return path


def filled_text() -> str:
    text = EXAMPLE.read_text(encoding="utf-8")
    for old, new in FILLED.items():
        assert old in text, old
        text = text.replace(old, new, 1)
    return text


def test_example_file_loads_with_every_placeholder_reported(tmp_path):
    cfg = load_config(EXAMPLE)
    assert cfg.business.display_name == "Visergy"
    assert cfg.last_project == 58
    assert cfg.placeholders() == [
        "business.name",
        "business.abn",
        "business.email",
        "bank.account_name",
        "bank.bsb",
        "bank.account_number",
    ]


def test_filled_file_loads_and_normalises(tmp_path):
    cfg = load_config(write(tmp_path, filled_text()))
    assert cfg.placeholders() == []
    assert cfg.business.abn == "51 824 753 556"
    assert cfg.business.address == ("1 Example Street", "Melbourne VIC 3000")
    assert cfg.business.gst_registered is True
    assert cfg.bank.bsb == "123-456"
    assert cfg.paths.database == Path.home() / ".local/share/visergy/visergy.sqlite3"
    assert cfg.paths.projects_root == Path.home() / "Nextcloud/Visergy/projects"
    assert (cfg.quote_validity_days, cfg.terms_version) == (30, "v1")
    assert (cfg.backup_keep_last, cfg.backup_keep_daily_days) == (20, 365)


def test_display_name_falls_back_to_legal_name(tmp_path):
    text = filled_text().replace('trading_as = "Visergy"', 'trading_as = ""')
    assert load_config(write(tmp_path, text)).business.display_name == "Alex Example"


def test_bank_details_never_appear_in_repr(tmp_path):
    cfg = load_config(write(tmp_path, filled_text()))
    shown = repr(cfg)
    for secret in ("123-456", "98765432"):
        assert secret not in shown


def test_errors_name_the_field_not_the_value(tmp_path):
    text = filled_text().replace('bsb = "123456"', 'bsb = "12345x"')
    with pytest.raises(ConfigError) as e:
        load_config(write(tmp_path, text))
    assert "[bank].bsb must be six digits" in str(e.value)
    assert "12345x" not in str(e.value)


def test_missing_file_says_what_to_do(tmp_path):
    with pytest.raises(ConfigError, match="copy config.example.toml"):
        load_config(tmp_path / "config.toml")


def test_invalid_toml(tmp_path):
    with pytest.raises(ConfigError, match="not valid TOML"):
        load_config(write(tmp_path, "[business\n"))


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ('abn = "51824753556"', 'abn = "51824753557"', r"\[business\].abn is not a valid ABN"),
        ('email = "alex@visergy.example"', "", r"\[business\].email is missing"),
        ("gst_registered = true", 'gst_registered = "yes"', r"gst_registered must be bool"),
        ("last_project = 58", "last_project = -1", r"last_project must be at least 0"),
        ("keep_last = 20", "keep_last = true", r"keep_last must be int"),
        ('address = ["1 Example Street", "Melbourne VIC 3000"]', "address = []", "list of lines"),
        ('account_number = "98765432"', 'account_number = "9876-5432"', "must be digits"),
    ],
)
def test_bad_values(tmp_path, old, new, message):
    text = filled_text()
    assert old in text
    with pytest.raises(ConfigError, match=message):
        load_config(write(tmp_path, text.replace(old, new)))


def test_environment_overrides(tmp_path, monkeypatch):
    path = write(tmp_path, filled_text())
    monkeypatch.setenv(CONFIG_ENV, str(path))
    monkeypatch.setenv(DATABASE_ENV, str(tmp_path / "live.sqlite3"))
    assert config_path() == path
    assert load_config().paths.database == tmp_path / "live.sqlite3"


def test_default_location_is_repo_root():
    assert config_path() == REPO / "config.toml"


@pytest.mark.parametrize(
    ("abn", "valid"),
    [
        ("51 824 753 556", True),
        ("51824753556", True),
        ("51 824 753 557", False),
        ("5182475355", False),
        ("51-824-753-556", False),
    ],
)
def test_abn_checksum(abn, valid):
    assert abn_is_valid(abn) is valid


def test_format_abn():
    assert format_abn("51824753556") == "51 824 753 556"
