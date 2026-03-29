#!/usr/bin/env python3
"""
export_pdf.py — Exports DOCX, PPTX, or XLSX files to PDF.

Uses LibreOffice headless mode (cross-platform, free).
Falls back gracefully if LibreOffice is not installed.

Usage:
    from export_pdf import export_to_pdf
    pdf_path = export_to_pdf(Path("document.docx"))
"""

import subprocess
import sys
from pathlib import Path


def export_to_pdf(source_path: Path) -> Path | None:
    """
    Convert source_path to PDF using LibreOffice headless.
    Returns the PDF path on success, None on failure.
    """
    source_path = Path(source_path).resolve()
    if not source_path.exists():
        print(f"export_pdf: source file not found: {source_path}", file=sys.stderr)
        return None

    output_dir = source_path.parent
    pdf_path = output_dir / source_path.with_suffix(".pdf").name

    # LibreOffice command — works on macOS, Linux, and Windows
    libreoffice_cmds = [
        "libreoffice",        # Linux / Windows PATH
        "soffice",            # Alternative Linux name
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",  # macOS
        r"C:\Program Files\LibreOffice\program\soffice.exe",      # Windows
    ]

    for cmd in libreoffice_cmds:
        try:
            result = subprocess.run(
                [cmd, "--headless", "--convert-to", "pdf", "--outdir",
                 str(output_dir), str(source_path)],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0 and pdf_path.exists():
                return pdf_path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    print(
        "export_pdf: LibreOffice not found. "
        "Install LibreOffice to enable PDF export: https://www.libreoffice.org/download/",
        file=sys.stderr,
    )
    return None
