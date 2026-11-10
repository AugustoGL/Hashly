
from io import BytesIO

from pypdf import PdfReader, PdfWriter


def standardize_pdf(file):

    file.file.seek(0)

    reader = PdfReader(file.file)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    output = BytesIO()

    filename = file.filename.encode("utf-8")

    output.write(
        len(filename).to_bytes(4, "big")
    )

    output.write(filename)

    writer.write(output)

    return output.getvalue()
