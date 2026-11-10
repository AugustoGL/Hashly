#!/usr/bin/env python3
"""
Prueba de humo del flujo completo de Hashly contra un API en marcha.

    python scripts/smoke.py                      # http://localhost:8000
    python scripts/smoke.py http://localhost:8100

Solo usa la librería estándar. Crea una cuenta nueva en cada corrida.
"""

import json
import sys
import time
import urllib.error
import urllib.request
import uuid

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")


def call(method, path, *, body=None, headers=None, raw=False):
    data = None
    headers = dict(headers or {})

    if isinstance(body, dict):
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    elif isinstance(body, tuple):  # (bytes, content_type) ya armado
        data, headers["Content-Type"] = body

    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            payload = res.read()
            return res.status, payload if raw else json.loads(payload or "null")
    except urllib.error.HTTPError as error:
        payload = error.read()
        try:
            return error.code, json.loads(payload)
        except ValueError:
            return error.code, payload


def multipart(fields, files):
    boundary = uuid.uuid4().hex
    out = b""

    for name, value in fields.items():
        out += (
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'
        ).encode()

    for filename, content in files:
        out += (
            f'--{boundary}\r\nContent-Disposition: form-data; name="files"; '
            f'filename="{filename}"\r\nContent-Type: text/plain\r\n\r\n'
        ).encode() + content + b"\r\n"

    out += f"--{boundary}--\r\n".encode()
    return out, f"multipart/form-data; boundary={boundary}"


failures = 0


def check(label, ok, extra=""):
    global failures
    print(f"  {'OK ' if ok else 'FAIL'}  {label}" + (f"  ({extra})" if extra and not ok else ""))
    failures += 0 if ok else 1


print(f"Hashly smoke test -> {BASE}")

status, health = call("GET", "/health")
check("API arriba", status == 200 and health.get("status") == "ok")

email = f"smoke-{uuid.uuid4().hex[:8]}@example.com"
status, _ = call("POST", "/v1/users/register", body={"email": email, "password": "smoke-password-123"})
check("registro", status == 200, status)

status, login = call("POST", "/v1/users/login", body={"email": email, "password": "smoke-password-123"})
check("login", status == 200 and "access_token" in login, status)
token = login["access_token"]

status, key = call("POST", "/v1/keys/", body={"name": "smoke"}, headers={"Authorization": f"Bearer {token}"})
check("API key creada", status == 201 and key["key"].startswith("hshl_live_"), status)
auth = {"Authorization": f"Bearer {key['key']}"}

files = [("a.txt", b"uno " + uuid.uuid4().hex.encode()), ("b.txt", b"dos"), ("c.txt", b"tres")]
status, pkg = call("POST", "/v1/packages/", body=multipart({"name": "Paquete secreto"}, files), headers=auth)
check("paquete sellado con API key", status == 200 and len(pkg["merkle_root"]) == 64, status)

status, found = call("POST", "/v1/packages/search/package", body=multipart({}, files))
check("verificación pública por archivos", status == 200 and found["found"] is True)

status, found_root = call("POST", "/v1/packages/search/merkle-root", body={"merkle_root": pkg["merkle_root"]})
check("verificación pública por raíz", found_root["found"] is True)

leak = json.dumps(found) + json.dumps(found_root)
check("lo público no revela email, nombre ni archivos",
      email not in leak and "Paquete secreto" not in leak and "a.txt" not in leak)

status, miss = call("POST", "/v1/packages/search/package", body=multipart({}, [(files[0][0], files[0][1] + b"!"), files[1], files[2]]))
check("un archivo alterado NO coincide", miss["found"] is False)

status, proof = call("GET", f"/v1/packages/{pkg['id']}/proof/b.txt", headers=auth)
check("prueba de Merkle de un archivo", status == 200 and proof["merkle_root"] == pkg["merkle_root"], status)

# El sello se envía en segundo plano a los calendar servers
seal = None
for _ in range(20):
    _, detail = call("GET", f"/v1/packages/{pkg['id']}", headers=auth)
    seal = detail["seal"]["status"]
    if seal != "creating":
        break
    time.sleep(1.5)
check(f"sello fuera de 'creating' (estado: {seal})", seal in ("pending", "confirmed"))

status, ots = call("GET", f"/v1/packages/{pkg['id']}/ots-proof", raw=True)
check("prueba .ots pública", status == 200 and ots[:16].startswith(b"\x00OpenTimestamps"), status)

status, _ = call("GET", "/v1/packages/")
check("listado privado exige credencial", status in (401, 403))

status, _ = call("POST", "/v1/packages/", body=multipart({"name": "x", "method": "smart_contract"}, files), headers=auth)
check("vía NFT responde 'próximamente' (501)", status == 501, status)

status, _ = call("POST", "/v1/waitlist/", body={"email": email, "interest": "contrato"})
check("lista de espera", status == 201, status)

print("\nTodo bien." if not failures else f"\n{failures} chequeo(s) fallaron.")
sys.exit(1 if failures else 0)
