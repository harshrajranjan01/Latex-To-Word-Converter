"""Tests for conversion, uploads, and the generated DOCX package."""

from __future__ import annotations

import zipfile
from io import BytesIO

import pytest

from converter import (
    ConversionError,
    PandocNotFoundError,
    convert_latex_to_docx,
    decode_uploaded_latex,
    docx_filename,
    find_pandoc,
)


PANDOC_AVAILABLE = find_pandoc() is not None
requires_pandoc = pytest.mark.skipif(
    not PANDOC_AVAILABLE, reason="Pandoc is required for conversion integration tests"
)


def assert_valid_docx(document: bytes) -> zipfile.ZipFile:
    archive = zipfile.ZipFile(BytesIO(document))
    assert "[Content_Types].xml" in archive.namelist()
    assert "word/document.xml" in archive.namelist()
    return archive


def test_empty_input_has_a_useful_error() -> None:
    with pytest.raises(ConversionError, match="empty"):
        convert_latex_to_docx("  \n")


def test_uploaded_txt_and_tex_files_are_decoded() -> None:
    source = "\\documentclass{article}\n\\begin{document}Hello\\end{document}"
    for filename in ("notes.txt", "paper.tex"):
        assert decode_uploaded_latex(filename, source.encode("utf-8")) == source


def test_uploaded_utf8_bom_is_accepted() -> None:
    assert decode_uploaded_latex("paper.tex", b"\xef\xbb\xbfHello") == "Hello"


def test_unsupported_upload_extension_is_rejected() -> None:
    with pytest.raises(ConversionError, match=r"\.txt or \.tex"):
        decode_uploaded_latex("paper.pdf", b"content")


def test_non_utf8_upload_has_a_useful_error() -> None:
    with pytest.raises(ConversionError, match="UTF-8"):
        decode_uploaded_latex("paper.tex", b"\xff\xfe\x00")


def test_docx_filename_is_safe_and_meaningful() -> None:
    assert docx_filename() == "latex_document.docx"
    assert docx_filename(r"C:\\Users\\me\\My Paper.tex") == "My_Paper.docx"


@requires_pandoc
def test_simple_latex_produces_a_valid_docx() -> None:
    document = convert_latex_to_docx(
        r"""\documentclass{article}
\begin{document}
Hello, Word!
\end{document}
"""
    )
    assert_valid_docx(document)


@requires_pandoc
def test_headings_paragraphs_and_lists_are_preserved() -> None:
    document = convert_latex_to_docx(
        r"""\documentclass{article}
\begin{document}
\section{First Section}
This is a paragraph.
\begin{enumerate}
\item First ordered item
\item Second ordered item
\end{enumerate}
\begin{itemize}
\item An unordered item
\end{itemize}
\end{document}
"""
    )
    with assert_valid_docx(document) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
    assert "First Section" in xml
    assert "This is a paragraph." in xml
    assert "First ordered item" in xml
    assert "An unordered item" in xml
    assert "Heading1" in xml
    assert "numPr" in xml


@requires_pandoc
def test_math_is_written_as_native_omml() -> None:
    document = convert_latex_to_docx(
        r"""\documentclass{article}
\begin{document}
Inline math $x^2 + y^2 = z^2$ and display math:
\[
\int_0^1 x^2\,dx = \frac{1}{3}
\]
\end{document}
"""
    )
    with assert_valid_docx(document) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
    assert "<m:oMath" in xml
    assert "<m:oMathPara" in xml


@requires_pandoc
def test_table_is_written_to_docx_table_structure() -> None:
    document = convert_latex_to_docx(
        r"""\documentclass{article}
\begin{document}
\begin{tabular}{ll}
Name & Value \\
Tea & 2 \\
\end{tabular}
\end{document}
"""
    )
    with assert_valid_docx(document) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
    assert "<w:tbl>" in xml
    assert "Tea" in xml and "Value" in xml


@requires_pandoc
@pytest.mark.parametrize("filename", ["notes.txt", "paper.tex"])
def test_uploaded_txt_and_tex_sources_convert(filename: str) -> None:
    source_bytes = (
        b"\\documentclass{article}\n"
        b"\\begin{document}Uploaded source\\end{document}"
    )
    source = decode_uploaded_latex(filename, source_bytes)
    assert_valid_docx(convert_latex_to_docx(source))


@requires_pandoc
def test_malformed_latex_reports_pandoc_details() -> None:
    with pytest.raises(ConversionError, match="Pandoc could not convert"):
        convert_latex_to_docx(r"\documentclass{article}\begin{document}\textbf{unclosed")


def test_missing_pandoc_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("converter.find_pandoc", lambda: None)
    with pytest.raises(PandocNotFoundError, match="pandoc.org/installing.html"):
        convert_latex_to_docx("\\begin{document}Hello\\end{document}")
