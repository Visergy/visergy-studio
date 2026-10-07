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
    write_control_file(tmp_path, "P2026-001")
    sub = tmp_path / "drawings" / "rev-a"
    sub.mkdir(parents=True)
    assert find_project_dir(sub) == tmp_path.resolve()
    assert locate_project(sub) == (tmp_path.resolve(), "P2026-001")


def test_no_control_file(tmp_path):
    with pytest.raises(ProjectNotFound):
        find_project_dir(tmp_path)


def test_control_file_must_hold_only_a_number(tmp_path):
    (tmp_path / "project.txt").write_text("P2026-001 Thermal review\n", encoding="utf-8")
    with pytest.raises(ProjectNotFound):
        read_project_number(tmp_path)


def test_control_file_whitespace_ignored(tmp_path):
    (tmp_path / "project.txt").write_text("  P2026-012\n\n", encoding="utf-8")
    assert read_project_number(tmp_path) == "P2026-012"


def test_write_control_file_rejects_bad_number(tmp_path):
    with pytest.raises(ValueError):
        write_control_file(tmp_path, "2026-001")


def test_pdf_filenames():
    assert pdf_filename("quote", "Q-0001", 2) == "Q-0001-v2.pdf"
    assert pdf_filename("invoice", "INV-0003") == "INV-0003.pdf"
    with pytest.raises(ValueError):
        pdf_filename("quote", "Q-0001")
    with pytest.raises(ValueError):
        pdf_filename("receipt", "R-1")


def test_relative_pdf_path(tmp_path):
    pdf = tmp_path / "issued" / "Q-0001-v1.pdf"
    assert relative_pdf_path(tmp_path, pdf) == "issued/Q-0001-v1.pdf"
    with pytest.raises(ValueError):
        relative_pdf_path(tmp_path / "issued", tmp_path / "other.pdf")


def test_folder_name():
    name = folder_name("P2026-001", "Thermal review: stage 2/3")
    assert name == "P2026-001 Thermal review stage 23"
    assert folder_name("P2026-001", "  lots   of   space ") == "P2026-001 lots of space"
    assert folder_name("P2026-001", "x" * 100, max_len=10) == "P2026-001 " + "x" * 10
