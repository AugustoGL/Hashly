import hashlib
from datetime import datetime, timezone

from standardizers import standardize_file

LEAF_PREFIX = b"\x00"
NODE_PREFIX = b"\x01"


def _leaf_hash(data: bytes) -> str:
    return hashlib.sha256(LEAF_PREFIX + data).hexdigest()


def _node_hash(left_hex: str, right_hex: str) -> str:
    return hashlib.sha256(
        NODE_PREFIX + bytes.fromhex(left_hex) + bytes.fromhex(right_hex)
    ).hexdigest()


def _largest_power_of_two_less_than(n: int) -> int:
    # RFC 6962: el subárbol izquierdo siempre tiene tamaño
    # k = la potencia de 2 más grande estrictamente menor que n
    k = 1
    while 2 * k < n:
        k *= 2
    return k


def _merkle_root(hashes: list[str]) -> str:
    n = len(hashes)

    if n == 1:
        return hashes[0]

    k = _largest_power_of_two_less_than(n)

    left = _merkle_root(hashes[:k])
    right = _merkle_root(hashes[k:])

    return _node_hash(left, right)


def _merkle_proof(hashes: list[str], index: int) -> list[dict]:
    n = len(hashes)

    if n == 1:
        return []

    k = _largest_power_of_two_less_than(n)

    if index < k:
        path = _merkle_proof(hashes[:k], index)
        sibling = _merkle_root(hashes[k:])
        path.append({"hash": sibling, "position": "right"})
    else:
        path = _merkle_proof(hashes[k:], index - k)
        sibling = _merkle_root(hashes[:k])
        path.append({"hash": sibling, "position": "left"})

    return path


def verify_merkle_proof(leaf_hash: str, proof: list[dict], expected_root: str) -> bool:
    current = leaf_hash

    for step in proof:
        if step["position"] == "right":
            current = _node_hash(current, step["hash"])
        else:
            current = _node_hash(step["hash"], current)

    return current == expected_root


def proof_from_manifest(manifest: list[dict], filename: str) -> list[dict]:
    """Prueba de Merkle de un archivo a partir de un manifest guardado."""

    entry = next(
        (
            e for e in manifest
            if e["filename"].lower() == filename.lower()
        ),
        None
    )

    if entry is None:
        raise ValueError(
            f"'{filename}' no pertenece a este paquete"
        )

    return _merkle_proof(
        [e["hash"] for e in manifest],
        entry["index"]
    )


class Package:

    def __init__(self, files):

        if not files:
            raise ValueError(
                "El Package debe contener al menos un archivo"
            )

        filenames = [
            file.filename
            for file in files
        ]

        if any(not filename for filename in filenames):
            raise ValueError(
                "Todos los archivos deben tener un nombre"
            )

        normalized_names = [
            filename.lower()
            for filename in filenames
        ]

        if len(normalized_names) != len(set(normalized_names)):
            raise ValueError(
                "No puede haber archivos con el mismo nombre"
            )

        self.files = sorted(
            files,
            key=lambda file: file.filename.lower()
        )

        self.created_at = datetime.now(timezone.utc)

        self.manifest = []

        self.generate_manifest()

        self.hash = self.generate_hash()

    def generate_manifest(self):

        for index, file in enumerate(self.files):

            standardized = standardize_file(file)

            file_hash = _leaf_hash(standardized)

            self.manifest.append({
                "index": index,
                "filename": file.filename,
                "hash": file_hash
            })

    def generate_hash(self):

        leaf_hashes = [
            entry["hash"]
            for entry in self.manifest
        ]

        if not leaf_hashes:
            return None

        return _merkle_root(leaf_hashes)

    def get_proof(self, filename: str) -> list[dict]:
        """
        Devuelve la Merkle proof de un archivo puntual del paquete,
        calculada al vuelo a partir del manifest ya guardado
        (no hace falta persistirla aparte).
        """

        normalized = filename.lower()

        entry = next(
            (
                e for e in self.manifest
                if e["filename"].lower() == normalized
            ),
            None
        )

        if entry is None:
            raise ValueError(
                f"'{filename}' no pertenece a este paquete"
            )

        leaf_hashes = [
            e["hash"]
            for e in self.manifest
        ]

        return _merkle_proof(leaf_hashes, entry["index"])