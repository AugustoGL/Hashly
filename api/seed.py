import hashlib
from datetime import datetime, timezone

from database.database import SessionLocal
from database.models import User, Package


def calculate_merkle_root(hashes):
    level = hashes.copy()

    if not level:
        return None

    while len(level) > 1:
        next_level = []

        for i in range(0, len(level), 2):
            left = level[i]

            if i + 1 < len(level):
                right = level[i + 1]
            else:
                right = left

            parent = hashlib.sha256(
                bytes.fromhex(left) +
                bytes.fromhex(right)
            ).hexdigest()

            next_level.append(parent)

        level = next_level

    return level[0]


def create_file_hash(content):
    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


db = SessionLocal()

user = db.query(User).first()

if not user:
    print("No hay usuarios registrados.")
    db.close()
    exit()


packages_data = [
    {
        "name": "Documentos de prueba",
        "files": [
            ("documento.txt", "Contenido del documento de prueba"),
            ("foto.png", "Imagen de prueba"),
        ]
    },
    {
        "name": "Contrato de alquiler",
        "files": [
            ("contrato.pdf", "Contrato de prueba"),
            ("datos.json", '{"nombre": "Augusto", "tipo": "demo"}'),
            ("notas.txt", "Notas del paquete"),
        ]
    },
    {
        "name": "Proyecto Hashly",
        "files": [
            ("archivo.py", "print('Hashly')"),
            ("README.md", "# Hashly\nSistema de prueba"),
        ]
    }
]


for package_data in packages_data:

    name = package_data["name"]
    files = package_data["files"]

    files = sorted(
        files,
        key=lambda file: file[0].lower()
    )

    manifest = []

    for index, (filename, content) in enumerate(files):

        file_hash = create_file_hash(content)

        manifest.append({
            "index": index,
            "filename": filename,
            "hash": file_hash
        })

    hashes = [
        file["hash"]
        for file in manifest
    ]

    merkle_root = calculate_merkle_root(hashes)

    package = Package(
        user_id=user.id,
        name=name,
        created_at=datetime.now(timezone.utc),
        manifest=manifest,
        merkle_root=merkle_root
    )

    db.add(package)


db.commit()

print(f"Packages creados para: {user.email}")

db.close()