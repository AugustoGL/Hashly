from pathlib import Path

from .image import standardize_image
from .pdf import standardize_pdf
from .text import standardize_text


def standardize_file(file):

    extension = Path(file.filename).suffix.lower()

    if extension in {
        ".jpg", ".jpeg", ".png",
        ".webp", ".bmp", ".tiff"
    }:
        return standardize_image(file)

    if extension == ".pdf":
        return standardize_pdf(file)

    if extension in {
        ".txt", ".md", ".py", ".js",
        ".ts", ".html", ".css",
        ".sql", ".json", ".xml"
    }:
        return standardize_text(file)

    raise ValueError(
        f"Formato no soportado: {extension}"
    )