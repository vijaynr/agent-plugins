from zipfile import ZipFile

from okf_core.adapters.docx import extract_docx
from okf_core.adapters.pdf import extract_pdf


def test_extract_docx_text_without_executing_embedded_content(tmp_path):
    path = tmp_path / "notes.docx"
    xml = """<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'><w:body><w:p><w:r><w:t>Decision text</w:t></w:r></w:p></w:body></w:document>"""
    with ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", xml)

    assert extract_docx(path) == "Decision text"


def test_extract_pdf_parenthesized_text(tmp_path):
    path = tmp_path / "notes.pdf"
    path.write_bytes(b"%PDF-1.4\nBT (Gotcha text) Tj ET\n%%EOF")

    assert extract_pdf(path) == "Gotcha text"
