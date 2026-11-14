# LaTeX to Word Converter

A small local Streamlit app that converts pasted LaTeX or uploaded `.txt` and
`.tex` files into downloadable `.docx` documents. Pandoc performs the parsing
and conversion. Supported math is written as native, editable Word equations
(OMML); support for custom LaTeX commands, packages, and environments varies.
Streamlit usage statistics are disabled by the included local configuration.

## Requirements

- Python 3.10 or later
- Pandoc installed separately and available on `PATH`

## How to install

First install Pandoc separately. Installing the Python requirements does not
install Pandoc. Use the [official Pandoc installation guide](https://pandoc.org/installing.html).

### Windows

1. Open the [official Pandoc installation page](https://pandoc.org/installing.html).
2. Download and run the current Windows installer.
3. Close and reopen PowerShell or Command Prompt so the updated `PATH` is read.
4. Check that `pandoc --version` prints a version.

### Linux

Use the package for your distribution or follow the current Linux instructions
on the [official Pandoc installation page](https://pandoc.org/installing.html).
For Debian or Ubuntu, the system package manager can be used:

```bash
sudo apt update
sudo apt install pandoc
```

### macOS

Follow the [official Pandoc installation page](https://pandoc.org/installing.html)
or install with Homebrew:

```bash
brew install pandoc
```

### Install Python dependencies

Open a terminal in the project folder, then run the commands for your operating
system.

#### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

These commands use the virtual environment directly, so activation scripts and
PowerShell execution-policy changes are not needed.

#### Linux and macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## How to run

Run the app from the project folder. Keep the terminal open while you use it.

### Windows (PowerShell)

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

### Linux and macOS

```bash
source .venv/bin/activate
streamlit run app.py
```

Streamlit prints the local address to open in your browser (usually
`http://localhost:8501`). Keep the terminal running while you use the app.

## Use

- **Paste LaTeX:** paste a complete document or fragment, then select **Convert
  to Word**.
- **Upload File:** choose a UTF-8 `.txt` or `.tex` file, then select **Convert
  to Word**.
- Select **Download Word Document** after conversion.

Both input methods are in the same app. An uploaded `.txt` or `.tex` file must
contain LaTeX source; it is not a plain-text-to-Word formatter. Use relative
figure paths only when the referenced files are accessible to Pandoc on this
computer. Figures and references depend on Pandoc's support and on those local
resources being available. The app does not upload documents to an external
service or keep conversion files permanently.

## Run tests

With Pandoc installed, run the test command from the project folder.

### Windows (PowerShell)

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

### Linux and macOS

```bash
python -m pytest -q
```

The tests check empty and malformed input, uploaded file decoding, DOCX package
validity, document structure, lists, tables, equations, and both upload
extensions. Integration tests that need Pandoc are skipped when the executable
is unavailable.
