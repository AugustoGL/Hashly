import io

from auth.api_keys import KEY_PREFIX
from database.models import ApiKey, PackageTimestamp
from ots import client as ots_client, service


def make_package(client_, headers, name="Pack", files=None, **extra):
    files = files or [
        ("files", ("a.txt", io.BytesIO(b"uno"), "text/plain")),
        ("files", ("b.txt", io.BytesIO(b"dos"), "text/plain")),
        ("files", ("c.txt", io.BytesIO(b"tres"), "text/plain")),
    ]

    return client_.post(
        "/v1/packages/",
        data={"name": name, **extra},
        files=files,
        headers=headers,
    )


# ---------------- API keys ----------------

def test_api_key_lifecycle(client, auth_headers, db):
    created = client.post(
        "/v1/keys/", json={"name": "ci"}, headers=auth_headers
    )

    assert created.status_code == 201
    key = created.json()["key"]
    assert key.startswith(KEY_PREFIX)

    # La key completa no se guarda, solo su hash
    row = db.query(ApiKey).one()
    assert row.key_hash != key
    assert key not in (row.prefix, row.key_hash)

    # Sirve para autenticar
    headers = {"Authorization": f"Bearer {key}"}
    assert client.get("/v1/users/me", headers=headers).status_code == 200
    assert make_package(client, headers).status_code == 200

    # El listado no vuelve a mostrar la key
    listed = client.get("/v1/keys/", headers=auth_headers).json()
    assert len(listed) == 1
    assert "key" not in listed[0]
    assert listed[0]["last_used_at"] is not None

    # Revocada deja de funcionar
    key_id = created.json()["id"]
    assert client.delete(
        f"/v1/keys/{key_id}", headers=auth_headers
    ).status_code == 204

    assert client.get("/v1/users/me", headers=headers).status_code == 401


def test_invalid_api_key_rejected(client):
    r = client.get(
        "/v1/users/me",
        headers={"Authorization": f"Bearer {KEY_PREFIX}nope"},
    )
    assert r.status_code == 401


def test_cannot_revoke_someone_elses_key(
    client, auth_headers, second_auth_headers
):
    key_id = client.post(
        "/v1/keys/", json={"name": "mine"}, headers=auth_headers
    ).json()["id"]

    r = client.delete(f"/v1/keys/{key_id}", headers=second_auth_headers)
    assert r.status_code == 404


# ---------------- Privacidad ----------------

def test_public_search_never_leaks_owner_or_names(
    client, auth_headers, user
):
    root = make_package(client, auth_headers, name="Secreto").json()[
        "merkle_root"
    ]

    r = client.post(
        "/v1/packages/search/merkle-root", json={"merkle_root": root}
    )
    body = r.text

    assert user.email not in body
    assert "Secreto" not in body
    assert "a.txt" not in body


# ---------------- Sellado OTS ----------------

def test_create_package_is_stamped_in_background(
    client, auth_headers, db
):
    r = make_package(client, auth_headers)
    assert r.status_code == 200

    db.expire_all()
    ts = db.query(PackageTimestamp).one()

    assert ts.status == "pending"
    assert ts.ots_proof.startswith(b"OTS-PENDING:")


def test_ots_proof_is_public(client, auth_headers):
    pid = make_package(client, auth_headers).json()["id"]

    r = client.get(f"/v1/packages/{pid}/ots-proof")

    assert r.status_code == 200
    assert r.headers["content-type"] == "application/octet-stream"
    assert r.content.startswith(b"OTS-PENDING:")


def test_ots_proof_404_when_missing(client):
    assert client.get("/v1/packages/999/ots-proof").status_code == 404


def test_failed_stamp_stays_creating_then_worker_retries(
    client, auth_headers, db, monkeypatch
):
    def boom(digest):
        raise ots_client.OtsError("sin red")

    monkeypatch.setattr(ots_client, "stamp", boom)

    make_package(client, auth_headers)

    db.expire_all()
    ts = db.query(PackageTimestamp).one()
    assert ts.status == "creating"
    assert "sin red" in ts.error

    monkeypatch.setattr(
        ots_client, "stamp", lambda d: b"OTS-PENDING:" + d
    )
    service.process_all(db)

    db.expire_all()
    assert db.query(PackageTimestamp).one().status == "pending"


def test_worker_confirms_when_bitcoin_confirms(
    client, auth_headers, db, monkeypatch
):
    make_package(client, auth_headers)

    monkeypatch.setattr(
        ots_client,
        "upgrade",
        lambda proof: ots_client.UpgradeResult(
            proof=b"OTS-CONFIRMED", confirmed=True, block_height=850000
        ),
    )

    service.process_all(db)

    db.expire_all()
    ts = db.query(PackageTimestamp).one()

    assert ts.status == "confirmed"
    assert ts.bitcoin_block_height == 850000
    assert ts.ots_proof == b"OTS-CONFIRMED"
    assert ts.confirmed_at is not None


def test_public_search_exposes_seal_status(client, auth_headers):
    root = make_package(client, auth_headers).json()["merkle_root"]

    pkg = client.post(
        "/v1/packages/search/merkle-root", json={"merkle_root": root}
    ).json()["packages"][0]

    assert pkg["verification_method"] == "ots"
    assert pkg["seal"]["status"] == "pending"


def test_smart_contract_method_is_coming_soon(client, auth_headers):
    r = make_package(client, auth_headers, method="smart_contract")
    assert r.status_code == 501
    assert "próximamente" in r.json()["detail"]


def test_unknown_method_rejected(client, auth_headers):
    assert make_package(
        client, auth_headers, method="otro"
    ).status_code == 400


# ---------------- Merkle proof por archivo ----------------

def test_file_merkle_proof_verifies(client, auth_headers):
    from package import _leaf_hash, verify_merkle_proof  # noqa

    pkg = make_package(client, auth_headers).json()

    r = client.get(
        f"/v1/packages/{pkg['id']}/proof/b.txt", headers=auth_headers
    )

    assert r.status_code == 200
    body = r.json()

    assert verify_merkle_proof(
        body["leaf_hash"], body["proof"], pkg["merkle_root"]
    )


def test_file_proof_unknown_file_404(client, auth_headers):
    pid = make_package(client, auth_headers).json()["id"]
    r = client.get(
        f"/v1/packages/{pid}/proof/nada.txt", headers=auth_headers
    )
    assert r.status_code == 404


def test_file_proof_requires_ownership(
    client, auth_headers, second_auth_headers
):
    pid = make_package(client, auth_headers).json()["id"]
    r = client.get(
        f"/v1/packages/{pid}/proof/a.txt", headers=second_auth_headers
    )
    assert r.status_code == 404


# ---------------- Límites ----------------

def test_package_limit_per_user(client, auth_headers, monkeypatch):
    import packages.routes as routes

    monkeypatch.setattr(routes, "MAX_PACKAGES_PER_USER", 1)

    assert make_package(client, auth_headers).status_code == 200
    assert make_package(client, auth_headers, name="2").status_code == 403


def test_register_validates_email_and_password(client):
    bad_email = client.post(
        "/v1/users/register",
        json={"email": "no-es-email", "password": "password123"},
    )
    short_pw = client.post(
        "/v1/users/register",
        json={"email": "a@b.co", "password": "corta"},
    )

    assert bad_email.status_code == 422
    assert short_pw.status_code == 422


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_rate_limit_returns_429(client, monkeypatch):
    import auth.ratelimit as rl

    monkeypatch.setattr(rl, "RATE_LIMIT_PER_MINUTE", 3)

    codes = [client.get("/health").status_code for _ in range(5)]

    assert codes[:3] == [200, 200, 200]
    assert 429 in codes[3:]
