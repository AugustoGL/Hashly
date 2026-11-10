from io import BytesIO

from pypdf import PdfReader, PdfWriter

from config import MAX_PDF_PAGES


def standardize_pdf(file):

    file.file.seek(0)

    try:
        reader = PdfReader(file.file)

        if len(reader.pages) > MAX_PDF_PAGES:
            raise ValueError(
                f"El PDF {file.filename} tiene demasiadas páginas"
            )

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

    except ValueError:
        raise

    except Exception:
        # PDF corrupto, cifrado o malicioso: es un error del cliente
        raise ValueError(
            f"No se pudo leer el PDF {file.filename}"
        )
