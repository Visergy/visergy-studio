import pytest

from visergy.errors import ReportSourceError
from visergy.reports import find_images, load_report_source


def _write(tmp_path, text, name="report.md"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_loads_front_matter_and_body(tmp_path):
    path = _write(
        tmp_path, '+++\ntitle = "Review"\nsubtitle = "Stage 2"\n+++\n\n# Summary\nText.\n'
    )
    src = load_report_source(path)
    assert (src.title, src.subtitle, src.toc) == ("Review", "Stage 2", True)
    assert src.body.strip() == "# Summary\nText."
    assert src.images == {}


def test_toc_can_be_turned_off(tmp_path):
    path = _write(tmp_path, '+++\ntitle = "Review"\ntoc = false\n+++\nBody\n')
    assert load_report_source(path).toc is False


def test_windows_line_endings(tmp_path):
    path = tmp_path / "report.md"
    path.write_bytes(b'+++\r\ntitle = "Review"\r\n+++\r\nBody\r\n')
    assert load_report_source(path).title == "Review"


@pytest.mark.parametrize(
    "text",
    [
        "# No front matter\n",
        '+++\ntitle = "Unclosed"\n',
        '+++\nsubtitle = "no title"\n+++\n',
        '+++\ntitle = ""\n+++\n',
        '+++\ntitle = "x"\nauthor = "typo key"\n+++\n',
        '+++\ntitle = "x"\ntoc = "yes"\n+++\n',
        "+++\ntitle = not toml\n+++\n",
    ],
)
def test_bad_front_matter(tmp_path, text):
    with pytest.raises(ReportSourceError):
        load_report_source(_write(tmp_path, text))


def test_missing_file(tmp_path):
    with pytest.raises(ReportSourceError):
        load_report_source(tmp_path / "nope.md")


def test_finds_images(tmp_path):
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "a.png").write_bytes(b"png")
    (tmp_path / "b.svg").write_text("<svg/>")
    body = '![Caption](figures/a.png)\n\ntext ![](b.svg "title")\n'
    images = find_images(body, tmp_path)
    assert images == {
        "figures/a.png": (tmp_path / "figures" / "a.png").resolve(),
        "b.svg": (tmp_path / "b.svg").resolve(),
    }


@pytest.mark.parametrize(
    "ref",
    ["missing.png", "../outside.png", "/etc/passwd", "https://example.com/x.png", "figures"],
)
def test_rejects_bad_image_refs(tmp_path, ref):
    (tmp_path / "figures").mkdir()
    (tmp_path.parent / "outside.png").write_bytes(b"png")
    with pytest.raises(ReportSourceError):
        find_images(f"![x]({ref})", tmp_path)


def test_rejects_symlink_escaping_folder(tmp_path):
    outside = tmp_path.parent / "secret.png"
    outside.write_bytes(b"png")
    report_dir = tmp_path / "report"
    report_dir.mkdir()
    (report_dir / "link.png").symlink_to(outside)
    with pytest.raises(ReportSourceError):
        find_images("![x](link.png)", report_dir)
