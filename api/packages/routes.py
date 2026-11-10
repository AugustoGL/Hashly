
import re
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
    HTTPException
)

from pydantic import BaseModel

from sqlalchemy.orm import Session

from database.database import get_db
from database.models import User, Package as PackageModel

from auth.dependencies import get_current_user
from package import Package
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
# CREATE PACKAGE
# ============================================================

@router.post("/")
async def create_package(
    name: str = Form(...),
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

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
        merkle_root=package.hash
    )

    db.add(package_db)
    db.commit()
    db.refresh(package_db)

    return {
        "id": package_db.id,
        "name": package_db.name,
        "created_at": package_db.created_at,
        "manifest": package_db.manifest,
        "merkle_root": package_db.merkle_root
    }


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
            "created_at": package.created_at
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
            {
                "id": package.id,
                "name": package.name,
                "created_at": package.created_at,
                "owner": {
                    "id": package.user.id,
                    "email": package.user.email
                }
            }
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
            {
                "id": package.id,
                "name": package.name,
                "created_at": package.created_at,
                "owner": {
                    "id": package.user.id,
                    "email": package.user.email
                }
            }
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

    package = (
        db.query(PackageModel)
        .filter(
            PackageModel.id == package_id,
            PackageModel.user_id == current_user.id
        )
        .first()
    )

    if not package:
        raise HTTPException(
            status_code=404,
            detail="Package no encontrado"
        )

    return {
        "id": package.id,
        "name": package.name,
        "created_at": package.created_at,
        "manifest": package.manifest,
        "merkle_root": package.merkle_root
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

    package = (
        db.query(PackageModel)
        .filter(
            PackageModel.id == package_id,
            PackageModel.user_id == current_user.id
        )
        .first()
    )

    if not package:
        raise HTTPException(
            status_code=404,
            detail="Package no encontrado"
        )

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
