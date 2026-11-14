"""Streamlit interface for the local LaTeX-to-Word converter."""

from __future__ import annotations

import streamlit as st

from converter import (
    DOCX_MIME_TYPE,
    ConversionError,
    PandocNotFoundError,
    convert_latex_to_docx,
    decode_uploaded_latex,
    docx_filename,
    find_pandoc,
)


st.set_page_config(page_title="LaTeX to Word Converter", page_icon="📝", layout="centered")
st.title("LaTeX to Word Converter")
st.write("Convert LaTeX source into an editable Microsoft Word document on this computer.")

if find_pandoc() is None:
    st.warning(
        "Pandoc is required to convert files. Install it using the "
        "[official Pandoc installation guide](https://pandoc.org/installing.html), "
        "then restart this app."
    )


def show_result(state_key: str) -> None:
    """Show the most recent result for one input tab, if there is one."""
    result = st.session_state.get(state_key)
    if result:
        data, filename = result
        st.success("Your Word document is ready.")
        st.download_button(
            "Download Word Document",
            data=data,
            file_name=filename,
            mime=DOCX_MIME_TYPE,
            key=f"download_{state_key}",
        )


paste_tab, upload_tab = st.tabs(["Paste LaTeX", "Upload File"])

with paste_tab:
    pasted_source = st.text_area(
        "LaTeX source",
        height=360,
        placeholder=(
            r"\documentclass{article}" "\n"
            r"\begin{document}" "\n"
            r"\section{A heading}" "\n"
            r"Your content goes here." "\n"
            r"\end{document}"
        ),
        help="Paste a complete LaTeX document or a LaTeX fragment.",
    )
    if st.button("Convert to Word", key="convert_paste", type="primary"):
        st.session_state.pop("paste_result", None)
        try:
            converted = convert_latex_to_docx(pasted_source)
            st.session_state["paste_result"] = (converted, docx_filename())
        except PandocNotFoundError as exc:
            st.error(str(exc))
        except ConversionError as exc:
            st.error(str(exc))
    show_result("paste_result")

with upload_tab:
    uploaded_file = st.file_uploader(
        "Choose a LaTeX source file",
        type=["txt", "tex"],
        accept_multiple_files=False,
        help="Supported file types: .txt and .tex (UTF-8 text).",
    )
    if st.button("Convert to Word", key="convert_upload", type="primary"):
        st.session_state.pop("upload_result", None)
        if uploaded_file is None:
            st.error("Choose a .txt or .tex file first.")
        else:
            try:
                source = decode_uploaded_latex(uploaded_file.name, uploaded_file.getvalue())
                converted = convert_latex_to_docx(source)
                st.session_state["upload_result"] = (
                    converted,
                    docx_filename(uploaded_file.name),
                )
            except PandocNotFoundError as exc:
                st.error(str(exc))
            except ConversionError as exc:
                st.error(str(exc))
    show_result("upload_result")

st.caption(
    "Files are converted locally with Pandoc. Uploaded content is held only in "
    "this app session and conversion temporary files are cleaned up automatically."
)
