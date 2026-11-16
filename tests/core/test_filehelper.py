from pathlib import Path

from PySide6.QtCore import QCoreApplication

from kondor.core.filehelper import FileHelper


def test_keeps_hash_and_percent() -> None:
    url = FileHelper.instance().suggestedFileUrl("/tmp/downloads", "C# 100% Guide", ".pdf")
    assert url.isLocalFile()
    assert not url.hasFragment()
    assert url.toLocalFile() == "/tmp/downloads/C# 100% Guide.pdf"


def test_keeps_spaces() -> None:
    url = FileHelper.instance().suggestedFileUrl("/tmp/my downloads", "a/b", ".html")
    assert url.toLocalFile() == "/tmp/my downloads/a_b.html"


def test_cuts_long_titles_at_100_code_units() -> None:
    assert FileHelper.instance().sanitizeFileName("a" * 99 + "😀") == "a" * 99


def test_reader_resource_reads_allowed_names_only(staged_resources: None) -> None:
    helper = FileHelper.instance()
    assert helper.readerResource("Readability.js") != ""
    assert helper.readerResource("../LICENSE") == ""


def test_removes_temp_folder_with_printed_pdf_when_quitting(qapp: QCoreApplication) -> None:
    helper = FileHelper()
    pdf = Path(helper.tempPdfPath())
    pdf.write_bytes(b"%PDF")
    qapp.aboutToQuit.emit()
    assert not pdf.parent.exists()
