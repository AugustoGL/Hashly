from io import BytesIO   
   
def standardize_text(file):
    file.file.seek(0)

    text = file.file.read().decode("utf-8")

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    filename = file.filename.encode("utf-8")

    return (
        len(filename).to_bytes(4, "big")
        + filename
        + text.encode("utf-8")
    )
