import io

from fastapi.testclient import TestClient


def make_upload(
    filename,
    content,
    content_type="text/plain"
):

    return (
        "files",
        (
            filename,
            io.BytesIO(content),
            content_type
        )
    )


def create_package(
    client,
    headers,
    name="Package de prueba",
    files=None
):

    if files is None:

        files = [
            make_upload(
                "archivo.txt",
                b"Contenido original"
            )
        ]

    return client.post(
        "/packages/",
        headers=headers,
        data={
            "name": name
        },
        files=files
    )


# ============================================================
# Create / list / get
# ============================================================

def test_create_package(
    client,
    auth_headers
):

    response = create_package(
        client,
        auth_headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] > 0
    assert data["name"] == "Package de prueba"

    assert data["merkle_root"]
    assert len(data["merkle_root"]) == 64

    assert len(data["manifest"]) == 1

    assert (
        data["manifest"][0]["filename"]
        == "archivo.txt"
    )


def test_create_package_requires_auth(
    client
):

    response = create_package(
        client,
        headers={}
    )

    assert response.status_code == 401


def test_list_my_packages(
    client,
    auth_headers
):

    create_package(
        client,
        auth_headers,
        name="Package 1"
    )

    create_package(
        client,
        auth_headers,
        name="Package 2"
    )

    response = client.get(
        "/packages/",
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    names = {
        package["name"]
        for package in data
    }

    assert names == {
        "Package 1",
        "Package 2"
    }


def test_user_only_sees_own_packages(
    client,
    auth_headers,
    second_auth_headers
):

    create_package(
        client,
        auth_headers,
        name="Package privado"
    )

    response = client.get(
        "/packages/",
        headers=second_auth_headers
    )

    assert response.status_code == 200

    assert response.json() == []


def test_get_own_package(
    client,
    auth_headers
):

    response = create_package(
        client,
        auth_headers
    )

    package_id = response.json()["id"]

    response = client.get(
        f"/packages/{package_id}",
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == package_id
    assert data["name"] == "Package de prueba"
    assert data["manifest"]
    assert data["merkle_root"]


def test_cannot_get_other_users_package(
    client,
    auth_headers,
    second_auth_headers
):

    response = create_package(
        client,
        auth_headers
    )

    package_id = response.json()["id"]

    response = client.get(
        f"/packages/{package_id}",
        headers=second_auth_headers
    )

    assert response.status_code == 404


# ============================================================
# Verification
# ============================================================

def test_verify_identical_package(
    client,
    auth_headers
):

    original_files = [
        make_upload(
            "archivo.txt",
            b"Contenido original"
        ),
        make_upload(
            "datos.json",
            b'{"nombre":"Hashly"}',
            "application/json"
        )
    ]

    response = create_package(
        client,
        auth_headers,
        files=original_files
    )

    assert response.status_code == 200

    package_id = response.json()["id"]
    expected_root = response.json()["merkle_root"]

    verification_files = [
        make_upload(
            "archivo.txt",
            b"Contenido original"
        ),
        make_upload(
            "datos.json",
            b'{"nombre":"Hashly"}',
            "application/json"
        )
    ]

    response = client.post(
        f"/packages/{package_id}/verify",
        headers=auth_headers,
        files=verification_files
    )

    assert response.status_code == 200

    data = response.json()

    assert data["valid"] is True
    assert data["expected_merkle_root"] == expected_root
    assert data["uploaded_merkle_root"] == expected_root

    assert all(
        file["match"]
        for file in data["files"]
    )

    assert data["extra_files"] == []


def test_verify_modified_file(
    client,
    auth_headers
):

    response = create_package(
        client,
        auth_headers,
        files=[
            make_upload(
                "archivo.txt",
                b"Contenido original"
            )
        ]
    )

    package_id = response.json()["id"]

    response = client.post(
        f"/packages/{package_id}/verify",
        headers=auth_headers,
        files=[
            make_upload(
                "archivo.txt",
                b"Contenido modificado"
            )
        ]
    )

    assert response.status_code == 200

    data = response.json()

    assert data["valid"] is False
    assert data["files"][0]["status"] == "modified"
    assert data["files"][0]["match"] is False


def test_verify_missing_file(
    client,
    auth_headers
):

    response = create_package(
        client,
        auth_headers,
        files=[
            make_upload(
                "archivo.txt",
                b"Contenido"
            ),
            make_upload(
                "otro.txt",
                b"Otro"
            )
        ]
    )

    package_id = response.json()["id"]

    response = client.post(
        f"/packages/{package_id}/verify",
        headers=auth_headers,
        files=[
            make_upload(
                "archivo.txt",
                b"Contenido"
            )
        ]
    )

    assert response.status_code == 200

    data = response.json()

    assert data["valid"] is False

    missing = [
        file
        for file in data["files"]
        if file["status"] == "missing"
    ]

    assert len(missing) == 1
    assert missing[0]["filename"] == "otro.txt"


def test_verify_extra_file(
    client,
    auth_headers
):

    response = create_package(
        client,
        auth_headers,
        files=[
            make_upload(
                "archivo.txt",
                b"Contenido"
            )
        ]
    )

    package_id = response.json()["id"]

    response = client.post(
        f"/packages/{package_id}/verify",
        headers=auth_headers,
        files=[
            make_upload(
                "archivo.txt",
                b"Contenido"
            ),
            make_upload(
                "extra.txt",
                b"Extra"
            )
        ]
    )

    assert response.status_code == 200

    data = response.json()

    assert data["valid"] is False
    assert data["extra_files"] == [
        "extra.txt"
    ]


def test_cannot_verify_other_users_package(
    client,
    auth_headers,
    second_auth_headers
):

    response = create_package(
        client,
        auth_headers
    )

    package_id = response.json()["id"]

    response = client.post(
        f"/packages/{package_id}/verify",
        headers=second_auth_headers,
        files=[
            make_upload(
                "archivo.txt",
                b"Contenido original"
            )
        ]
    )

    assert response.status_code == 404


# ============================================================
# Public search by Merkle Root
# ============================================================

def test_search_by_merkle_root(
    client,
    auth_headers,
    user
):

    response = create_package(
        client,
        auth_headers,
        name="Registro público"
    )

    merkle_root = response.json()["merkle_root"]

    response = client.post(
        "/packages/search/merkle-root",
        json={
            "merkle_root": merkle_root
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["found"] is True
    assert data["merkle_root"] == merkle_root
    assert len(data["packages"]) == 1

    package = data["packages"][0]

    assert package["name"] == "Registro público"

    assert package["owner"]["id"] == user.id
    assert package["owner"]["email"] == user.email


def test_search_by_merkle_root_does_not_require_auth(
    client,
    auth_headers
):

    response = create_package(
        client,
        auth_headers
    )

    merkle_root = response.json()["merkle_root"]

    response = client.post(
        "/packages/search/merkle-root",
        json={
            "merkle_root": merkle_root
        }
    )

    assert response.status_code == 200


def test_search_nonexistent_merkle_root(
    client
):

    root = (
        "a" * 64
    )

    response = client.post(
        "/packages/search/merkle-root",
        json={
            "merkle_root": root
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["found"] is False
    assert data["packages"] == []


def test_search_invalid_merkle_root(
    client
):

    response = client.post(
        "/packages/search/merkle-root",
        json={
            "merkle_root": "abc"
        }
    )

    assert response.status_code == 400


# ============================================================
# Public search by files
# ============================================================

def test_search_by_package(
    client,
    auth_headers,
    user
):

    original_files = [
        make_upload(
            "archivo.txt",
            b"Contenido"
        ),
        make_upload(
            "datos.json",
            b'{"test":true}',
            "application/json"
        )
    ]

    create_response = create_package(
        client,
        auth_headers,
        name="Package buscable",
        files=original_files
    )

    merkle_root = (
        create_response
        .json()["merkle_root"]
    )

    search_files = [
        make_upload(
            "archivo.txt",
            b"Contenido"
        ),
        make_upload(
            "datos.json",
            b'{"test":true}',
            "application/json"
        )
    ]

    response = client.post(
        "/packages/search/package",
        files=search_files
    )

    assert response.status_code == 200

    data = response.json()

    assert data["found"] is True
    assert data["merkle_root"] == merkle_root

    package = data["packages"][0]

    assert package["name"] == "Package buscable"
    assert package["owner"]["id"] == user.id
    assert package["owner"]["email"] == user.email


def test_search_by_package_does_not_require_auth(
    client,
    auth_headers
):

    create_package(
        client,
        auth_headers
    )

    response = client.post(
        "/packages/search/package",
        files=[
            make_upload(
                "archivo.txt",
                b"Contenido original"
            )
        ]
    )

    assert response.status_code == 200


def test_search_by_modified_package_not_found(
    client,
    auth_headers
):

    create_package(
        client,
        auth_headers,
        files=[
            make_upload(
                "archivo.txt",
                b"Contenido original"
            )
        ]
    )

    response = client.post(
        "/packages/search/package",
        files=[
            make_upload(
                "archivo.txt",
                b"Contenido modificado"
            )
        ]
    )

    assert response.status_code == 200

    data = response.json()

    assert data["found"] is False
    assert data["packages"] == []


def test_search_by_package_with_extra_file_not_found(
    client,
    auth_headers
):

    create_package(
        client,
        auth_headers,
        files=[
            make_upload(
                "archivo.txt",
                b"Contenido"
            )
        ]
    )

    response = client.post(
        "/packages/search/package",
        files=[
            make_upload(
                "archivo.txt",
                b"Contenido"
            ),
            make_upload(
                "extra.txt",
                b"Extra"
            )
        ]
    )

    assert response.status_code == 200

    data = response.json()

    assert data["found"] is False
    assert data["packages"] == []


# ============================================================
# Route validation
# ============================================================

def test_create_package_duplicate_filename(
    client,
    auth_headers
):

    response = create_package(
        client,
        auth_headers,
        files=[
            make_upload(
                "archivo.txt",
                b"uno"
            ),
            make_upload(
                "archivo.txt",
                b"dos"
            )
        ]
    )

    assert response.status_code == 400


def test_create_package_unsupported_file(
    client,
    auth_headers
):

    response = create_package(
        client,
        auth_headers,
        files=[
            make_upload(
                "virus.exe",
                b"contenido",
                "application/octet-stream"
            )
        ]
    )

    assert response.status_code == 400