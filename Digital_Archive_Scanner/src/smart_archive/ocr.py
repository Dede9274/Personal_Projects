from dataclasses import dataclass
from io import BytesIO
import os
from pathlib import Path


@dataclass(frozen=True)
class ExtractionResult:
    text: str
    used_ocr: bool
    languages: str


def extract_text(pdf_path: Path, languages: str = "deu+eng") -> ExtractionResult:
    try:
        import fitz
        from PIL import Image
        import pytesseract
    except ImportError as error:
        raise RuntimeError(
            'Python dependencies are missing. Run: python -m pip install -e ".[dev]"'
        ) from error

    tesseract_config = _configure_windows_tesseract(pytesseract)
    page_texts: list[str] = []
    used_ocr = False

    try:
        with fitz.open(pdf_path) as document:
            for page in document:
                embedded_text = page.get_text("text").strip()
                if len(embedded_text) >= 30:
                    page_texts.append(embedded_text)
                    continue

                used_ocr = True
                scale = 300 / 72
                pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
                image = Image.open(BytesIO(pixmap.tobytes("png")))
                page_texts.append(
                    pytesseract.image_to_string(
                        image,
                        lang=languages,
                        config=tesseract_config,
                    )
                )
    except pytesseract.TesseractNotFoundError as error:
        raise RuntimeError(
            "Tesseract OCR is not installed or is not available on PATH."
        ) from error
    except pytesseract.TesseractError as error:
        raise RuntimeError(
            f"Tesseract failed. Confirm that these language packs are installed: {languages}"
        ) from error

    return ExtractionResult("\n\n".join(page_texts).strip(), used_ocr, languages)


def _configure_windows_tesseract(pytesseract_module: object) -> str:
    if os.name != "nt":
        return ""

    program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    executable = program_files / "Tesseract-OCR" / "tesseract.exe"
    if executable.is_file():
        pytesseract_module.pytesseract.tesseract_cmd = str(executable)

    local_app_data = Path(
        os.environ.get(
            "LOCALAPPDATA",
            Path.home() / "AppData" / "Local",
        )
    )
    tessdata_directory = local_app_data / "Tesseract-OCR" / "tessdata"
    if tessdata_directory.is_dir():
        os.environ["TESSDATA_PREFIX"] = str(tessdata_directory)

    return ""
