import pytest

from visergy.errors import ProjectNotFound
from visergy.paths import (
    find_project_dir,
    folder_name,
    locate_project,
    pdf_filename,
    read_project_number,
    relative_pdf_path,
    write_control_file,
)


def test_finds_control_file_from_subfolder(tmp_path):
    write_control_file(tmp_path, "0059")
    sub = tmp_path / "drawings" / "rev-a"
    sub.mkdir(parents=True)
    assert find_project_dir(sub) == tmp_path.resolve()
    assert locate_project(sub) == (tmp_path.resolve(), "0059")


def test_no_control_file(tmp_path):
    with pytest.raises(ProjectNotFound):
        find_project_dir(tmp_path)


def test_control_file_must_hold_only_a_number(tmp_path):
    (tmp_path / "project.txt").write_text("0059 Thermal review\n", encoding="utf-8")
    with pytest.raises(ProjectNotFound):
        read_project_number(tmp_path)


def test_control_file_whitespace_ignored(tmp_path):
    (tmp_path / "project.txt").write_text("  0012\n\n", encoding="utf-8")
    assert read_project_number(tmp_path) == "0012"


@pytest.mark.parametrize("number", ["P2026-001", "59", "00059", "abcd"])
def test_write_control_file_rejects_bad_number(tmp_path, number):
    with pytest.raises(ValueError):
        write_control_file(tmp_path, number)


def test_pdf_filenames():
    assert pdf_filename("quote", "26001", 2) == "Proposal_26001-v2.pdf"
    assert pdf_filename("invoice", "26003") == "Invoice_26003.pdf"
    assert pdf_filename("report", "0059-R01", "B") == "Report_0059-R01-B.pdf"
    with pytest.raises(ValueError):
        pdf_filename("quote", "26001")
    with pytest.raises(ValueError):
        pdf_filename("report", "0059-R01")
    with pytest.raises(ValueError):
        pdf_filename("receipt", "R-1")


def test_relative_pdf_path(tmp_path):
    pdf = tmp_path / "issued" / "Proposal_26001-v1.pdf"
    assert relative_pdf_path(tmp_path, pdf) == "issued/Proposal_26001-v1.pdf"
    with pytest.raises(ValueError):
        relative_pdf_path(tmp_path / "issued", tmp_path / "other.pdf")


@pytest.mark.parametrize(
    "title, name",
    [
        ("Philip Street", "0059-PhilipStreet"),
        ("200 Sydney Road", "0059-200SydneyRoad"),
        ("Thermal review: stage 2/3", "0059-ThermalReviewStage23"),
        ("  lots   of   space ", "0059-LotsOfSpace"),
        ("Miles_Street", "0059-MilesStreet"),
        ("iPad dock", "0059-IPadDock"),
        ("!!!", "0059"),
    ],
)
def test_folder_name(title, name):
    assert folder_name("0059", title) == name


def test_folder_name_is_truncated():
    assert folder_name("0059", "x" * 100, max_len=10) == "0059-" + "X" + "x" * 9
