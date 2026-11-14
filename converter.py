"""Local LaTeX-to-DOCX conversion using the Pandoc command-line tool."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path


PANDOC_INSTALL_URL = "https://pandoc.org/installing.html"
DOCX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class ConversionError(Exception):
    """Raised when Pandoc cannot convert the supplied LaTeX source."""


class PandocNotFoundError(ConversionError):
    """Raised when the Pandoc executable is not available on PATH."""


def find_pandoc() -> str | None:
    """Return the Pandoc executable path, or None when Pandoc is not installed."""
    executable = shutil.which("pandoc")
    if executable:
        return executable

    # The official Windows installer commonly places Pandoc here even when the
    # app's current process has not picked up an updated PATH yet.
    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        possible_paths = []
        if local_app_data:
            possible_paths.append(Path(local_app_data) / "Pandoc" / "pandoc.exe")
        possible_paths.append(Path.home() / "AppData" / "Local" / "Pandoc" / "pandoc.exe")
        for installed_executable in possible_paths:
            if installed_executable.is_file():
                return str(installed_executable)

    return None


def decode_uploaded_latex(file_name: str, file_content: bytes) -> str:
    """Decode an uploaded .txt or .tex file as UTF-8 (accepting a UTF-8 BOM)."""
    suffix = Path(file_name.replace("\\", "/")).suffix.lower()
    if suffix not in {".txt", ".tex"}:
        raise ConversionError("Please upload a .txt or .tex file.")

    try:
        return file_content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ConversionError(
            "This file is not valid UTF-8 text. Save it as UTF-8 and upload it again."
        ) from exc


def docx_filename(source_name: str | None = None) -> str:
    """Create a safe, meaningful DOCX filename from an uploaded file name."""
    if not source_name:
        return "latex_document.docx"

    # Treat either slash style as a path separator so names are safe on all OSes.
    base_name = source_name.replace("\\", "/").rsplit("/", maxsplit=1)[-1]
    stem = Path(base_name).stem
    safe_stem = "".join(
        character
        for character in stem
        if character.isalnum() or character in {"-", "_", " "}
    ).strip()
    safe_stem = "_".join(safe_stem.split())
    return f"{safe_stem or 'latex_document'}.docx"


def _validate_docx(path: Path) -> bytes:
    """Read and minimally validate a generated Office Open XML document."""
    if not path.is_file() or path.stat().st_size == 0:
        raise ConversionError("Pandoc did not create a Word document.")

    try:
        with zipfile.ZipFile(path) as archive:
            required_parts = {"[Content_Types].xml", "word/document.xml"}
            if not required_parts.issubset(archive.namelist()):
                raise ConversionError(
                    "Pandoc created a file that is not a valid DOCX document."
                )
    except zipfile.BadZipFile as exc:
        raise ConversionError(
            "Pandoc created a file that is not a valid DOCX document."
        ) from exc

    return path.read_bytes()


def convert_latex_to_docx(latex_source: str) -> bytes:
    """Convert LaTeX source to DOCX bytes with Pandoc, using only temporary files.

    Pandoc parses LaTeX and writes Word's DOCX format. Pandoc converts supported
    math to native Office Math Markup Language (OMML). The temporary directory
    is removed automatically on success and on failure.
    """
    if not latex_source or not latex_source.strip():
        raise ConversionError("The LaTeX input is empty. Add some content and try again.")

    pandoc = find_pandoc()
    if pandoc is None:
        raise PandocNotFoundError(
            "Pandoc was not found. Install it from the official guide at "
            f"{PANDOC_INSTALL_URL}, then restart this app."
        )

    with tempfile.TemporaryDirectory(prefix="latex-to-word-") as temporary_folder:
        temporary_path = Path(temporary_folder)
        input_path = temporary_path / "input.tex"
        output_path = temporary_path / "converted.docx"
        input_path.write_text(latex_source, encoding="utf-8", newline="\n")

        command = [
            pandoc,
            "--from=latex",
            "--to=docx",
            "--output",
            str(output_path),
            str(input_path),
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
            )
        except subprocess.TimeoutExpired as exc:
            raise ConversionError(
                "Pandoc took too long to convert this document. Try a smaller "
                "document or remove unsupported content."
            ) from exc
        except OSError as exc:
            raise ConversionError(f"Could not start Pandoc: {exc}") from exc

        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            if not detail:
                detail = "Pandoc did not provide additional details."
            raise ConversionError(f"Pandoc could not convert this LaTeX source:\n{detail}")

        return _validate_docx(output_path)
