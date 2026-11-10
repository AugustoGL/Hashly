"""Regresiones de la revisión de seguridad."""

import io

import pytest
from PIL import Image

from package import Package


class Upload:
    def __init__(self, filename, data):
        self.filename = filename
        self.file = io.BytesIO(data)


def png(width, height, color=(1, 2, 3)):
    out = io.BytesIO()
    Image.new("RGB", (width, height), color).save(out, "PNG")
    return out.getvalue()


def tiff(*colors):
    frames = [Image.new("RGB", (4, 4), color) for color in colors]
    out = io.BytesIO()
    frames[0].save(out, "TIFF", save_all=True, append_images=frames[1:])
    return out.getvalue()


def send(client, path, files, **kwargs):
    return client.post(
        path,
        files=[("files", (name, io.BytesIO(data), "application/octet-stream"))
               for name, data in files],
        **kwargs,
    )


# ---------------- Archivos maliciosos ----------------

def test_decompression_bomb_is_rejected(client, monkeypatch):
    import standardizers.image as image

    monkeypatch.setattr(image, "MAX_IMAGE_PIXELS", 1000)

    # Pocos bytes en disco, muchos píxeles en memoria
    r = send(client, "/v1/packages/search/package", [("bomba.png", png(200, 200))])

    assert r.status_code == 400
    assert "demasiado grande" in r.json()["detail"]


@pytest.mark.parametrize("name,data", [
    ("roto.pdf", b"%PDF-1.4 esto no es un pdf"),
    ("roto.png", b"\x89PNG esto no es una imagen"),
    ("roto.txt", b"\xff\xfe\xfa no es utf-8"),
])
def test_corrupt_files_are_client_errors_not_500(client, name, data):
    r = send(client, "/v1/packages/search/package", [(name, data)])

    assert r.status_code == 400
    assert "Traceback" not in r.text


def test_every_frame_of_an_image_is_part_of_the_hash():
    """Antes solo se hasheaba el primer frame: el resto se podía alterar."""

    original = Package([Upload("acta.tiff", tiff((1, 1, 1), (2, 2, 2)))])
    tampered = Package([Upload("acta.tiff", tiff((1, 1, 1), (9, 9, 9)))])

    assert original.hash != tampered.hash


def test_single_frame_hash_is_unchanged():
    """Los paquetes ya sellados siguen verificando."""

    import hashlib

    from standardizers import standardize_file

    data = standardize_file(Upload("a.png", png(7, 5, (10, 20, 30))))

    assert hashlib.sha256(data).hexdigest() == (
        "d0582ea8621d3553479bb668d0e42dc992464864ff9d6a84656aaa519dc15b20"
    )


@pytest.mark.parametrize("filename", ["a\x07b.txt", "a\nb.txt", "x" * 300 + ".txt"])
def test_hostile_filenames_rejected(filename):
    from validators.files import validate_files

    with pytest.raises(ValueError):
        validate_files([Upload(filename, b"x")])


def test_package_name_length_is_capped(client, auth_headers):
    r = client.post(
        "/v1/packages/",
        data={"name": "x" * 300},
        files=[("files", ("a.txt", io.BytesIO(b"x"), "text/plain"))],
        headers=auth_headers,
    )
    assert r.status_code == 422


# ---------------- Capa HTTP ----------------

def test_oversized_body_is_cut_off(client, monkeypatch):
    import auth.hardening as hardening

    monkeypatch.setattr(hardening, "MULTIPART_LIMIT", 2000)

    r = send(client, "/v1/packages/search/package", [("a.txt", b"x" * 5000)])

    assert r.status_code == 413


def test_oversized_json_body_is_cut_off(client):
    r = client.post(
        "/v1/users/login",
        content=b'{"email":"a@b.co","password":"' + b"x" * 2_000_000 + b'"}',
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 413


def test_security_headers_present(client):
    r = client.get("/health")

    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["cache-control"] == "no-store"
    assert "default-src 'none'" in r.headers["content-security-policy"]


def test_docs_still_render(client):
    r = client.get("/docs")

    assert r.status_code == 200
    assert "content-security-policy" not in r.headers


def test_rate_limit_cannot_be_bypassed_with_fake_tokens(client, monkeypatch):
    """Antes cada Authorization distinto estrenaba un cupo nuevo."""

    import auth.ratelimit as rl

    monkeypatch.setattr(rl, "RATE_LIMIT_PER_MINUTE", 3)

    codes = [
        client.get(
            "/health", headers={"Authorization": f"Bearer inventado-{i}"}
        ).status_code
        for i in range(6)
    ]

    assert codes.count(429) == 3


def test_rate_limiter_memory_is_bounded(monkeypatch):
    import auth.ratelimit as rl

    monkeypatch.setattr(rl, "MAX_KEYS", 100)

    limiter = rl.RateLimitMiddleware(app=None)

    for i in range(1000):
        limiter._allowed(f"ip:{i}", 5)

    assert len(limiter.hits) <= 101


def test_waitlist_and_public_upload_are_rate_limited(client, monkeypatch):
    import auth.ratelimit as rl

    monkeypatch.setattr(rl, "AUTH_RATE_LIMIT_PER_MINUTE", 2)
    monkeypatch.setattr(rl, "PUBLIC_UPLOAD_RATE_LIMIT_PER_MINUTE", 2)

    waitlist = [
        client.post("/v1/waitlist/", json={"email": f"a{i}@b.co"}).status_code
        for i in range(4)
    ]
    uploads = [
        send(client, "/v1/packages/search/package", [("a.txt", b"x")]).status_code
        for _ in range(4)
    ]

    assert waitlist == [201, 201, 429, 429]
    assert uploads == [200, 200, 429, 429]


# ---------------- Cuentas ----------------

def test_email_is_case_insensitive(client):
    body = {"email": "Persona@Ejemplo.com", "password": "password123"}

    assert client.post("/v1/users/register", json=body).status_code == 200

    # No se puede registrar el mismo email con otras mayúsculas
    dup = client.post(
        "/v1/users/register",
        json={"email": "persona@ejemplo.COM", "password": "password123"},
    )
    assert dup.status_code == 400

    login = client.post(
        "/v1/users/login",
        json={"email": "PERSONA@ejemplo.com", "password": "password123"},
    )
    assert login.status_code == 200


def test_login_does_the_same_work_for_unknown_users(client, monkeypatch):
    """Sin esto, el tiempo de respuesta revela qué emails existen."""

    import users.routes as routes

    calls = []
    monkeypatch.setattr(
        routes, "burn_password_check", lambda password: calls.append(password)
    )

    r = client.post(
        "/v1/users/login",
        json={"email": "nadie@ejemplo.com", "password": "password123"},
    )

    assert r.status_code == 401
    assert calls == ["password123"]


def test_corrupt_password_hash_is_401_not_500(client, db, user):
    user.password_hash = "no-es-un-hash-argon2"
    db.commit()

    r = client.post(
        "/v1/users/login",
        json={"email": user.email, "password": "password123"},
    )
    assert r.status_code == 401


def test_private_endpoints_reject_anonymous(client):
    for method, path in [
        ("get", "/v1/packages/"),
        ("get", "/v1/packages/1"),
        ("get", "/v1/packages/1/proof/a.txt"),
        ("get", "/v1/keys/"),
        ("get", "/v1/users/me"),
    ]:
        assert getattr(client, method)(path).status_code in (401, 403), path
