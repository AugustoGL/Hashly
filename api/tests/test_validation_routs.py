import io

import validators.files as validator


def make_upload(
    filename,
    content
):

    return (
        "files",
        (
            filename,
            io.BytesIO(content),
            "text/plain"
        )
    )


def test_route_respects_max_files(
    client,
    auth_headers,
    monkeypatch
):

    monkeypatch.setattr(
        validator,
        "MAX_FILES",
        2
    )

    files = [
        make_upload(
            "a.txt",
            b"a"
        ),
        make_upload(
            "b.txt",
            b"b"
        ),
        make_upload(
            "c.txt",
            b"c"
        )
    ]

    response = client.post(
        "/packages/",
        headers=auth_headers,
        data={
            "name": "Demasiados archivos"
        },
        files=files
    )

    assert response.status_code == 400


def test_route_respects_max_file_size(
    client,
    auth_headers,
    monkeypatch
):

    monkeypatch.setattr(
        validator,
        "MAX_FILE_SIZE",
        10
    )

    response = client.post(
        "/packages/",
        headers=auth_headers,
        data={
            "name": "Archivo grande"
        },
        files=[
            make_upload(
                "archivo.txt",
                b"12345678901"
            )
        ]
    )

    assert response.status_code == 400


def test_route_respects_max_total_size(
    client,
    auth_headers,
    monkeypatch
):

    monkeypatch.setattr(
        validator,
        "MAX_TOTAL_SIZE",
        15
    )

    response = client.post(
        "/packages/",
        headers=auth_headers,
        data={
            "name": "Total grande"
        },
        files=[
            make_upload(
                "a.txt",
                b"1234567890"
            ),
            make_upload(
                "b.txt",
                b"123456"
            )
        ]
    )

    assert response.status_code == 400