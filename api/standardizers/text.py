def standardize_text(file):
    file.file.seek(0)

    try:
        text = file.file.read().decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError(
            f"El archivo {file.filename} no es texto UTF-8 válido"
        )

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    filename = file.filename.encode("utf-8")

    return (
        len(filename).to_bytes(4, "big")
        + filename
        + text.encode("utf-8")
    )
