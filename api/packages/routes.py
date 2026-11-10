
import re
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    Response,
    UploadFile,
    HTTPException
)

from pydantic import BaseModel

from sqlalchemy.orm import Session

from config import MAX_PACKAGES_PER_USER
from database import database
from database.database import get_db
from database.models import (
    User,
    Package as PackageModel,
    PackageTimestamp
)
from ots import service as ots_service

from auth.dependencies import get_current_user
from package import Package, proof_from_manifest
from validators.files import validate_files


router = APIRouter(
    prefix="/packages",
    tags=["packages"]
)


# ============================================================
# SCHEMAS
# ============================================================

class MerkleRootSearch(BaseModel):
    merkle_root: str


# ============================================================
# HELPERS
# ============================================================

def _seal(package: PackageModel) -> dict | None:
    """Estado público del sellado: no revela nada sensible."""

    ts = package.timestamp

    if ts is None:
        return None

    return {
        "status": ts.status,
        "bitcoin_block_height": ts.bitcoin_block_height,
        "confirmed_at": ts.confirmed_at
    }


def _public_package(package: PackageModel) -> dict:
    """
    Lo público confirma, no revela: ni nombre, ni manifest,
    ni dueño.
    """

    return {
        "id": package.id,
        "created_at": package.created_at,
        "verification_method": package.verification_method,
        "seal": _seal(package)
    }


def _private_package(package: PackageModel) -> dict:
    return {
        "id": package.id,
        "name": package.name,
        "created_at": package.created_at,
        "manifest": package.manifest,
        "merkle_root": package.merkle_root,
        "verification_method": package.verification_method,
        "seal": _seal(package)
    }


def _submit_in_background(timestamp_id: int) -> None:
    db = database.SessionLocal()

    try:
        ots_service.submit(db, timestamp_id)
    finally:
        db.close()


def _own_package(
    db: Session,
    user: User,
    package_id: int
) -> PackageModel:

    package = (
        db.query(PackageModel)
        .filter(
            PackageModel.id == package_id,
            PackageModel.user_id == user.id
        )
        .first()
    )

    if not package:
        raise HTTPException(
            status_code=404,
            detail="Package no encontrado"
        )

    return package


# ============================================================
# CREATE PACKAGE
# ============================================================

@router.post("/")
async def create_package(
    background_tasks: BackgroundTasks,
    name: str = Form(..., min_length=1, max_length=255),
    files: list[UploadFile] = File(...),
    method: str = Form(
        "ots",
        description=(
            "Vía de sellado: `ots` (gratis, Bitcoin). "
            "`smart_contract` (NFT) llega próximamente."
        )
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crea un paquete: hashea los archivos (que no se guardan),
    arma el árbol de Merkle y sella el `merkle_root`.
    """

    if method == "smart_contract":
        raise HTTPException(
            status_code=501,
            detail="La vía por contrato (NFT) llega próximamente"
        )

    if method != "ots":
        raise HTTPException(
            status_code=400,
            detail="method debe ser 'ots'"
        )

    if MAX_PACKAGES_PER_USER:
        owned = (
            db.query(PackageModel)
            .filter(PackageModel.user_id == current_user.id)
            .count()
        )

        if owned >= MAX_PACKAGES_PER_USER:
            raise HTTPException(
                status_code=403,
                detail="Alcanzaste el límite de paquetes del plan"
            )

    try:
        validate_files(files)

        package = Package(files)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    package_db = PackageModel(
        user_id=current_user.id,
        name=name,
        created_at=package.created_at,
        manifest=package.manifest,
        merkle_root=package.hash,
        verification_method="ots"
    )

    package_db.timestamp = PackageTimestamp(status="creating")

    db.add(package_db)
    db.commit()
    db.refresh(package_db)

    background_tasks.add_task(
        _submit_in_background,
        package_db.timestamp.id
    )

    return _private_package(package_db)


# ============================================================
# GET MY PACKAGES
# ============================================================

@router.get("/")
def get_my_packages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    packages = (
        db.query(PackageModel)
        .filter(
            PackageModel.user_id == current_user.id
        )
        .all()
    )

    return [
        {
            "id": package.id,
            "name": package.name,
            "created_at": package.created_at,
            "merkle_root": package.merkle_root,
            "verification_method": package.verification_method,
            "seal": _seal(package)
        }
        for package in packages
    ]


# ============================================================
# SEARCH BY MERKLE ROOT
# ============================================================

@router.post("/search/merkle-root")
def search_by_merkle_root(
    data: MerkleRootSearch,
    db: Session = Depends(get_db)
):

    if not re.fullmatch(
        r"[a-fA-F0-9]{64}",
        data.merkle_root
    ):
        raise HTTPException(
            status_code=400,
            detail="Merkle Root inválido"
        )

    packages = (
        db.query(PackageModel)
        .filter(
            PackageModel.merkle_root == data.merkle_root
        )
        .all()
    )

    if not packages:
        return {
            "found": False,
            "merkle_root": data.merkle_root,
            "packages": []
        }

    return {
        "found": True,
        "merkle_root": data.merkle_root,
        "packages": [
            _public_package(package)
            for package in packages
        ]
    }


# ============================================================
# SEARCH BY FILE SET
# ============================================================

@router.post("/search/package")
async def search_by_package(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
):

    try:
        validate_files(files)

        uploaded_package = Package(files)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    packages = (
        db.query(PackageModel)
        .filter(
            PackageModel.merkle_root == uploaded_package.hash
        )
        .all()
    )

    if not packages:
        return {
            "found": False,
            "merkle_root": uploaded_package.hash,
            "packages": []
        }

    return {
        "found": True,
        "merkle_root": uploaded_package.hash,
        "packages": [
            _public_package(package)
            for package in packages
        ]
    }


# ============================================================
# GET ONE PACKAGE
# ============================================================

@router.get("/{package_id}")
def get_my_package(
    package_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    package = _own_package(db, current_user, package_id)

    return _private_package(package)


# ============================================================
# OTS PROOF (público)
# ============================================================

@router.get("/{package_id}/ots-proof")
def get_ots_proof(
    package_id: int,
    db: Session = Depends(get_db)
):
    """
    Descarga el `.ots`. Es público a propósito: se puede auditar
    con cualquier cliente OpenTimestamps (`ots verify`).
    """

    package = db.get(PackageModel, package_id)

    ts = package.timestamp if package else None

    if ts is None or not ts.ots_proof:
        raise HTTPException(
            status_code=404,
            detail="Todavía no hay prueba disponible"
        )

    return Response(
        content=ts.ots_proof,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition":
                f'attachment; filename="hashly-{package_id}.ots"'
        }
    )


# ============================================================
# MERKLE PROOF DE UN ARCHIVO
# ============================================================

@router.get("/{package_id}/proof/{filename:path}")
def get_file_proof(
    package_id: int,
    filename: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Prueba de Merkle de un archivo, calculada desde el manifest."""

    package = _own_package(db, current_user, package_id)

    try:
        proof = proof_from_manifest(package.manifest, filename)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))

    entry = next(
        e for e in package.manifest
        if e["filename"].lower() == filename.lower()
    )

    return {
        "filename": entry["filename"],
        "leaf_hash": entry["hash"],
        "merkle_root": package.merkle_root,
        "proof": proof
    }


# ============================================================
# VERIFY PACKAGE
# ============================================================

@router.post("/{package_id}/verify")
async def verify_package(
    package_id: int,
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    package = _own_package(db, current_user, package_id)

    try:
        validate_files(files)

        uploaded_package = Package(files)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    expected_manifest = package.manifest
    uploaded_manifest = uploaded_package.manifest

    expected = {
        file["filename"]: file["hash"]
        for file in expected_manifest
    }

    uploaded = {
        file["filename"]: file["hash"]
        for file in uploaded_manifest
    }

    results = []

    for filename, expected_hash in expected.items():

        if filename not in uploaded:

            results.append({
                "filename": filename,
                "expected_hash": expected_hash,
                "uploaded_hash": None,
                "match": False,
                "status": "missing"
            })

            continue

        uploaded_hash = uploaded[filename]

        results.append({
            "filename": filename,
            "expected_hash": expected_hash,
            "uploaded_hash": uploaded_hash,
            "match": expected_hash == uploaded_hash,
            "status": (
                "match"
                if expected_hash == uploaded_hash
                else "modified"
            )
        })

    extra_files = [
        filename
        for filename in uploaded
        if filename not in expected
    ]

    valid = (
        uploaded_package.manifest == expected_manifest
        and uploaded_package.hash == package.merkle_root
    )

    return {
        "valid": valid,
        "expected_merkle_root": package.merkle_root,
        "uploaded_merkle_root": uploaded_package.hash,
        "files": results,
        "extra_files": extra_files
    }
