
from pathlib import Path

from fastapi import UploadFile

from config import (
    MAX_FILES,
    MAX_FILE_SIZE,
    MAX_TOTAL_SIZE
)


ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png",
    ".webp", ".bmp", ".tiff",
    ".pdf",
    ".txt", ".md", ".py", ".js",
    ".ts", ".html", ".css",
    ".sql", ".json", ".xml"
}


def validate_files(
    files: list[UploadFile]
) -> None:

    if not files:
        raise ValueError(
            "El Package debe contener al menos un archivo"
        )

    if len(files) > MAX_FILES:
        raise ValueError(
            f"No se pueden subir más de {MAX_FILES} archivos"
        )

    filenames = set()
    total_size = 0

    for file in files:

        if not file.filename:
            raise ValueError(
                "Todos los archivos deben tener un nombre"
            )

        if len(file.filename) > 255:
            raise ValueError(
                "El nombre de un archivo supera los 255 caracteres"
            )

        if any(ord(char) < 32 or ord(char) == 127 for char in file.filename):
            raise ValueError(
                "El nombre de un archivo tiene caracteres no permitidos"
            )

        normalized_name = file.filename.lower()

        if normalized_name in filenames:
            raise ValueError(
                f"Archivo duplicado: {file.filename}"
            )

        filenames.add(normalized_name)

        extension = Path(
            file.filename
        ).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Formato no soportado: {extension}"
            )

        file.file.seek(0)

        content = file.file.read()

        size = len(content)

        file.file.seek(0)

        if size > MAX_FILE_SIZE:
            raise ValueError(
                f"El archivo {file.filename} supera "
                f"el límite permitido"
            )

        total_size += size

    if total_size > MAX_TOTAL_SIZE:
        raise ValueError(
            "El tamaño total de los archivos supera "
            "el límite permitido"
        )
