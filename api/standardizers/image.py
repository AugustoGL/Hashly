from io import BytesIO

from PIL import Image, ImageSequence

from config import MAX_IMAGE_PIXELS


# Pillow rechaza por su cuenta las imágenes absurdamente grandes;
# el tope fino (sumando frames) se aplica abajo.
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


def standardize_image(file):
    file.file.seek(0)

    try:
        image = Image.open(file.file)

        frames = getattr(image, "n_frames", 1)
        width, height = image.size

        # Se valida ANTES de decodificar: una imagen pequeña en disco
        # puede ocupar gigas en memoria (bomba de descompresión).
        if width * height * frames > MAX_IMAGE_PIXELS:
            raise ValueError(
                f"La imagen {file.filename} es demasiado grande"
            )

        output = BytesIO()

        filename = file.filename.encode("utf-8")

        output.write(len(filename).to_bytes(4, "big"))
        output.write(filename)

        for index, frame in enumerate(ImageSequence.Iterator(image)):
            rgba = frame.convert("RGBA")

            # Los frames adicionales (TIFF multipágina, WebP animado)
            # también forman parte de la huella: si no, se podrían
            # alterar sin que cambie el hash.
            if index > 0:
                output.write(b"\x00frame")

            output.write(rgba.width.to_bytes(4, "big"))
            output.write(rgba.height.to_bytes(4, "big"))
            output.write(rgba.tobytes())

        return output.getvalue()

    except ValueError:
        raise

    except Exception:
        # Incluye DecompressionBombError y archivos corruptos
        raise ValueError(
            f"No se pudo leer la imagen {file.filename}"
        )
