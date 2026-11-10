   # package.py

from io import BytesIO
from PIL import Image


   
def standardize_image(file):
    file.file.seek(0)

    image = Image.open(file.file).convert("RGBA")

    output = BytesIO()

    filename = file.filename.encode("utf-8")

    output.write(
        len(filename).to_bytes(4, "big")
    )
    output.write(filename)

    output.write(
        image.width.to_bytes(4, "big")
    )
    output.write(
        image.height.to_bytes(4, "big")
    )

    output.write(image.tobytes())

    return output.getvalue()