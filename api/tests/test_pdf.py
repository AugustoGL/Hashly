
from io import BytesIO

from fastapi import UploadFile
from pypdf import PdfReader, PdfWriter

from standardizers.pdf import standardize_pdf
from standardizers import standardize_file


def make_pdf():

    writer = PdfWriter()

    writer.add_blank_page(
        width=200,
        height=200
    )

    output = BytesIO()

    writer.write(output)

    return output.getvalue()


def make_upload_file(
    filename: str,
    content: bytes
):
    return UploadFile(
        filename=filename,
        file=BytesIO(content)
    )


def test_pdf_is_standardized():

    pdf = make_pdf()

    file = make_upload_file(
        "documento.pdf",
        pdf
    )

    result = standardize_pdf(file)

    assert isinstance(
        result,
        bytes
    )

    assert len(result) > 0


def test_same_pdf_same_filename_same_result():

    pdf = make_pdf()

    file_a = make_upload_file(
        "documento.pdf",
        pdf
    )

    file_b = make_upload_file(
        "documento.pdf",
        pdf
    )

    assert standardize_pdf(file_a) == standardize_pdf(
        file_b
    )


def test_same_pdf_different_filename_different_result():

    pdf = make_pdf()

    file_a = make_upload_file(
        "a.pdf",
        pdf
    )

    file_b = make_upload_file(
        "b.pdf",
        pdf
    )

    assert standardize_pdf(file_a) != standardize_pdf(
        file_b
    )


def test_standardize_file_selects_pdf():

    pdf = make_pdf()

    file_a = make_upload_file(
        "documento.pdf",
        pdf
    )

    file_b = make_upload_file(
        "documento.pdf",
        pdf
    )

    assert standardize_file(file_a) == standardize_pdf(
        file_b
    )


def test_pdf_can_be_read_after_standardization():

    pdf = make_pdf()

    file = make_upload_file(
        "documento.pdf",
        pdf
    )

    result = standardize_pdf(file)

    filename_length = int.from_bytes(
        result[:4],
        "big"
    )

    offset = 4 + filename_length

    pdf_bytes = result[offset:]

    reader = PdfReader(
        BytesIO(pdf_bytes)
    )

    assert len(reader.pages) == 1
