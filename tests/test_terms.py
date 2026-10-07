from pathlib import Path

import pytest

from visergy.errors import ConfigError
from visergy.terms import load_terms

REPO_TERMS = Path(__file__).parent.parent / "terms"


def _write(tmp_path, version, body):
    (tmp_path / f"terms-{version}.toml").write_text(body, encoding="utf-8")


def test_loads_repo_terms():
    t = load_terms("v1", REPO_TERMS)
    assert t.version == "v1"
    assert t.sections[0]["heading"] == "Scope and changes"
    assert len(t.sha256) == 64


def test_hash_ignores_comments_and_formatting(tmp_path):
    _write(tmp_path, "v1", 'version = "v1"\n[[sections]]\nheading = "A"\nbody = "B"\n')
    first = load_terms("v1", tmp_path).sha256
    _write(tmp_path, "v1", '# note\nversion="v1"\n\n[[sections]]\nbody="B"\nheading="A"\n')
    assert load_terms("v1", tmp_path).sha256 == first


def test_hash_changes_with_content(tmp_path):
    _write(tmp_path, "v1", 'version = "v1"\n[[sections]]\nheading = "A"\nbody = "B"\n')
    first = load_terms("v1", tmp_path).sha256
    _write(tmp_path, "v1", 'version = "v1"\n[[sections]]\nheading = "A"\nbody = "C"\n')
    assert load_terms("v1", tmp_path).sha256 != first


@pytest.mark.parametrize("version", ["1", "v1.1", "V1", "../v1"])
def test_bad_version_name(tmp_path, version):
    with pytest.raises(ConfigError):
        load_terms(version, tmp_path)


def test_missing_file(tmp_path):
    with pytest.raises(ConfigError):
        load_terms("v9", tmp_path)


def test_version_must_match_filename(tmp_path):
    _write(tmp_path, "v2", 'version = "v1"\n')
    with pytest.raises(ConfigError):
        load_terms("v2", tmp_path)


@pytest.mark.parametrize(
    "section",
    ['heading = "A"', 'heading = "A"\nbody = 3', 'heading = "A"\nbody = "B"\nextra = "C"'],
)
def test_bad_sections_rejected(tmp_path, section):
    _write(tmp_path, "v1", f'version = "v1"\n[[sections]]\n{section}\n')
    with pytest.raises(ConfigError):
        load_terms("v1", tmp_path)
