
from io import BytesIO

import pytest
from fastapi import UploadFile
from PIL import Image

from standardizers import standardize_file
from standardizers.text import standardize_text
from standardizers.image import standardize_image
from standardizers.pdf import standardize_pdf


def make_upload_file(
    filename: str,
    content: bytes
):
    return UploadFile(
        filename=filename,
        file=BytesIO(content)
    )


def make_image_file(
    filename: str,
    color=(255, 0, 0, 255),
    metadata=None
):
    image = Image.new(
        "RGBA",
        (2, 2),
        color
    )

    output = BytesIO()

    if metadata:
        image.info.update(metadata)

    image.save(
        output,
        format="PNG"
    )

    output.seek(0)

    return UploadFile(
        filename=filename,
        file=output
    )


def test_text_crlf_is_normalized():

    file = make_upload_file(
        "archivo.txt",
        b"linea1\r\nlinea2\r\n"
    )

    result = standardize_text(file)

    filename = b"archivo.txt"

    expected = (
        len(filename).to_bytes(4, "big")
        + filename
        + b"linea1\nlinea2\n"
    )

    assert result == expected


def test_text_cr_is_normalized():

    file = make_upload_file(
        "archivo.txt",
        b"linea1\rlinea2\r"
    )

    result = standardize_text(file)

    filename = b"archivo.txt"

    expected = (
        len(filename).to_bytes(4, "big")
        + filename
        + b"linea1\nlinea2\n"
    )

    assert result == expected


def test_text_same_content_same_filename_same_result():

    file_a = make_upload_file(
        "archivo.txt",
        b"hola\nmundo"
    )

    file_b = make_upload_file(
        "archivo.txt",
        b"hola\nmundo"
    )

    assert standardize_text(file_a) == standardize_text(file_b)


def test_text_different_filename_different_result():

    file_a = make_upload_file(
        "a.txt",
        b"hola"
    )

    file_b = make_upload_file(
        "b.txt",
        b"hola"
    )

    assert standardize_text(file_a) != standardize_text(file_b)


def test_text_different_content_different_result():

    file_a = make_upload_file(
        "archivo.txt",
        b"hola"
    )

    file_b = make_upload_file(
        "archivo.txt",
        b"chau"
    )

    assert standardize_text(file_a) != standardize_text(file_b)


def test_image_same_pixels_same_filename_same_result():

    file_a = make_image_file(
        "imagen.png"
    )

    file_b = make_image_file(
        "imagen.png"
    )

    assert standardize_image(file_a) == standardize_image(file_b)


def test_image_different_filename_different_result():

    file_a = make_image_file(
        "a.png"
    )

    file_b = make_image_file(
        "b.png"
    )

    assert standardize_image(file_a) != standardize_image(file_b)


def test_image_one_pixel_change_changes_result():

    file_a = make_image_file(
        "imagen.png",
        color=(255, 0, 0, 255)
    )

    file_b = make_image_file(
        "imagen.png",
        color=(0, 255, 0, 255)
    )

    assert standardize_image(file_a) != standardize_image(file_b)


def test_image_metadata_does_not_change_result():

    image_a = Image.new(
        "RGBA",
        (2, 2),
        (255, 0, 0, 255)
    )

    image_b = Image.new(
        "RGBA",
        (2, 2),
        (255, 0, 0, 255)
    )

    output_a = BytesIO()
    output_b = BytesIO()

    image_a.save(
        output_a,
        format="PNG"
    )

    image_b.save(
        output_b,
        format="PNG"
    )

    file_a = UploadFile(
        filename="imagen.png",
        file=BytesIO(output_a.getvalue())
    )

    file_b = UploadFile(
        filename="imagen.png",
        file=BytesIO(output_b.getvalue())
    )

    assert standardize_image(file_a) == standardize_image(file_b)


def test_standardize_file_selects_text():

    file = make_upload_file(
        "archivo.txt",
        b"hola"
    )

    assert standardize_file(file) == standardize_text(
        make_upload_file(
            "archivo.txt",
            b"hola"
        )
    )


def test_standardize_file_selects_image():

    file = make_image_file(
        "imagen.png"
    )

    expected_file = make_image_file(
        "imagen.png"
    )

    assert standardize_file(file) == standardize_image(
        expected_file
    )


def test_unsupported_extension():

    file = make_upload_file(
        "archivo.exe",
        b"contenido"
    )

    with pytest.raises(ValueError):

        standardize_file(file)
