import io

import pytest

from fastapi import UploadFile

import validators.files as validator


def make_file(
    filename,
    content=b"contenido"
):

    return UploadFile(
        file=io.BytesIO(content),
        filename=filename
    )


def test_empty_files_rejected():

    with pytest.raises(ValueError):

        validator.validate_files([])


def test_duplicate_files_rejected():

    files = [
        make_file(
            "archivo.txt"
        ),
        make_file(
            "archivo.txt"
        )
    ]

    with pytest.raises(ValueError):

        validator.validate_files(files)


def test_duplicate_files_case_insensitive():

    files = [
        make_file(
            "Archivo.txt"
        ),
        make_file(
            "archivo.TXT"
        )
    ]

    with pytest.raises(ValueError):

        validator.validate_files(files)


def test_unsupported_extension_rejected():

    files = [
        make_file(
            "archivo.exe"
        )
    ]

    with pytest.raises(ValueError) as error:

        validator.validate_files(files)

    assert "Formato no soportado" in str(
        error.value
    )


def test_allowed_extensions():

    extensions = [
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".bmp",
        ".tiff",
        ".pdf",
        ".txt",
        ".md",
        ".py",
        ".js",
        ".ts",
        ".html",
        ".css",
        ".sql",
        ".json",
        ".xml"
    ]

    for extension in extensions:

        files = [
            make_file(
                f"archivo{extension}"
            )
        ]

        validator.validate_files(files)


def test_max_files():

    original = validator.MAX_FILES

    validator.MAX_FILES = 2

    try:

        files = [
            make_file("a.txt"),
            make_file("b.txt"),
            make_file("c.txt")
        ]

        with pytest.raises(ValueError):

            validator.validate_files(files)

    finally:

        validator.MAX_FILES = original


def test_max_file_size():

    original = validator.MAX_FILE_SIZE

    validator.MAX_FILE_SIZE = 10

    try:

        files = [
            make_file(
                "archivo.txt",
                b"12345678901"
            )
        ]

        with pytest.raises(ValueError):

            validator.validate_files(files)

    finally:

        validator.MAX_FILE_SIZE = original


def test_max_total_size():

    original = validator.MAX_TOTAL_SIZE

    validator.MAX_TOTAL_SIZE = 15

    try:

        files = [
            make_file(
                "a.txt",
                b"1234567890"
            ),
            make_file(
                "b.txt",
                b"123456"
            )
        ]

        with pytest.raises(ValueError):

            validator.validate_files(files)

    finally:

        validator.MAX_TOTAL_SIZE = original


def test_file_exactly_at_max_size():

    original = validator.MAX_FILE_SIZE

    validator.MAX_FILE_SIZE = 10

    try:

        files = [
            make_file(
                "archivo.txt",
                b"1234567890"
            )
        ]

        validator.validate_files(files)

    finally:

        validator.MAX_FILE_SIZE = original


def test_total_exactly_at_max_size():

    original = validator.MAX_TOTAL_SIZE

    validator.MAX_TOTAL_SIZE = 20

    try:

        files = [
            make_file(
                "a.txt",
                b"1234567890"
            ),
            make_file(
                "b.txt",
                b"1234567890"
            )
        ]

        validator.validate_files(files)

    finally:

        validator.MAX_TOTAL_SIZE = original