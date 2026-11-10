
from io import BytesIO

import pytest
from fastapi import UploadFile

from package import (
    Package,
    _leaf_hash,
    _merkle_root,
)


def make_upload_file(
    filename: str,
    content: bytes
):
    return UploadFile(
        filename=filename,
        file=BytesIO(content)
    )


def test_empty_package():

    with pytest.raises(ValueError):
        Package([])


def test_missing_filename():

    file = make_upload_file(
        "",
        b"hola"
    )

    with pytest.raises(ValueError):
        Package([file])


def test_duplicate_filename():

    file_a = make_upload_file(
        "archivo.txt",
        b"a"
    )

    file_b = make_upload_file(
        "archivo.txt",
        b"b"
    )

    with pytest.raises(ValueError):
        Package([
            file_a,
            file_b
        ])


def test_duplicate_filename_case_insensitive():

    file_a = make_upload_file(
        "Archivo.txt",
        b"a"
    )

    file_b = make_upload_file(
        "archivo.TXT",
        b"b"
    )

    with pytest.raises(ValueError):
        Package([
            file_a,
            file_b
        ])


def test_files_are_sorted_by_filename():

    file_b = make_upload_file(
        "b.txt",
        b"b"
    )

    file_a = make_upload_file(
        "a.txt",
        b"a"
    )

    package = Package([
        file_b,
        file_a
    ])

    assert [
        file["filename"]
        for file in package.manifest
    ] == [
        "a.txt",
        "b.txt"
    ]


def test_filename_is_part_of_file_hash():

    file_a = make_upload_file(
        "a.txt",
        b"hola"
    )

    file_b = make_upload_file(
        "b.txt",
        b"hola"
    )

    package_a = Package([file_a])
    package_b = Package([file_b])

    assert package_a.manifest[0]["hash"] != (
        package_b.manifest[0]["hash"]
    )


def test_same_filename_and_content_same_hash():

    package_a = Package([
        make_upload_file(
            "archivo.txt",
            b"hola"
        )
    ])

    package_b = Package([
        make_upload_file(
            "archivo.txt",
            b"hola"
        )
    ])

    assert package_a.hash == package_b.hash


def test_single_file_root_equals_leaf_hash():

    filename = "archivo.txt"
    content = b"hola mundo"

    package = Package([
        make_upload_file(
            filename,
            content
        )
    ])

    leaf_hash = package.manifest[0]["hash"]

    assert package.hash == leaf_hash


def test_two_file_merkle_root():

    package = Package([
        make_upload_file(
            "a.txt",
            b"a"
        ),
        make_upload_file(
            "b.txt",
            b"b"
        )
    ])

    hashes = [
        entry["hash"]
        for entry in package.manifest
    ]

    expected_root = _merkle_root(
        hashes
    )

    assert package.hash == expected_root


def test_three_file_merkle_root():

    package = Package([
        make_upload_file(
            "a.txt",
            b"a"
        ),
        make_upload_file(
            "b.txt",
            b"b"
        ),
        make_upload_file(
            "c.txt",
            b"c"
        )
    ])

    hashes = [
        entry["hash"]
        for entry in package.manifest
    ]

    expected_root = _merkle_root(
        hashes
    )

    assert package.hash == expected_root


def test_four_file_merkle_root():

    package = Package([
        make_upload_file(
            "a.txt",
            b"a"
        ),
        make_upload_file(
            "b.txt",
            b"b"
        ),
        make_upload_file(
            "c.txt",
            b"c"
        ),
        make_upload_file(
            "d.txt",
            b"d"
        )
    ])

    hashes = [
        entry["hash"]
        for entry in package.manifest
    ]

    expected_root = _merkle_root(
        hashes
    )

    assert package.hash == expected_root


def test_five_file_merkle_root():

    package = Package([
        make_upload_file(
            "a.txt",
            b"a"
        ),
        make_upload_file(
            "b.txt",
            b"b"
        ),
        make_upload_file(
            "c.txt",
            b"c"
        ),
        make_upload_file(
            "d.txt",
            b"d"
        ),
        make_upload_file(
            "e.txt",
            b"e"
        )
    ])

    hashes = [
        entry["hash"]
        for entry in package.manifest
    ]

    expected_root = _merkle_root(
        hashes
    )

    assert package.hash == expected_root


def test_upload_order_does_not_change_root():

    package_a = Package([
        make_upload_file(
            "a.txt",
            b"a"
        ),
        make_upload_file(
            "b.txt",
            b"b"
        ),
        make_upload_file(
            "c.txt",
            b"c"
        )
    ])

    package_b = Package([
        make_upload_file(
            "c.txt",
            b"c"
        ),
        make_upload_file(
            "a.txt",
            b"a"
        ),
        make_upload_file(
            "b.txt",
            b"b"
        )
    ])

    assert package_a.hash == package_b.hash


def test_one_byte_change_changes_root():

    package_a = Package([
        make_upload_file(
            "archivo.txt",
            b"hola"
        )
    ])

    package_b = Package([
        make_upload_file(
            "archivo.txt",
            b"holA"
        )
    ])

    assert package_a.hash != package_b.hash


def test_filename_change_changes_root():

    package_a = Package([
        make_upload_file(
            "archivo.txt",
            b"hola"
        )
    ])

    package_b = Package([
        make_upload_file(
            "otro.txt",
            b"hola"
        )
    ])

    assert package_a.hash != package_b.hash


def test_manifest_structure():

    package = Package([
        make_upload_file(
            "b.txt",
            b"b"
        ),
        make_upload_file(
            "a.txt",
            b"a"
        )
    ])

    expected_hashes = {
        "a.txt": _leaf_hash(
            (
                len(b"a.txt").to_bytes(4, "big")
                + b"a.txt"
                + b"a"
            )
        ),
        "b.txt": _leaf_hash(
            (
                len(b"b.txt").to_bytes(4, "big")
                + b"b.txt"
                + b"b"
            )
        )
    }

    assert package.manifest == [
        {
            "index": 0,
            "filename": "a.txt",
            "hash": expected_hashes["a.txt"]
        },
        {
            "index": 1,
            "filename": "b.txt",
            "hash": expected_hashes["b.txt"]
        }
    ]


def test_manifest_indexes_are_sequential():

    package = Package([
        make_upload_file(
            "c.txt",
            b"c"
        ),
        make_upload_file(
            "a.txt",
            b"a"
        ),
        make_upload_file(
            "b.txt",
            b"b"
        )
    ])

    assert [
        entry["index"]
        for entry in package.manifest
    ] == [0, 1, 2]


def test_manifest_contains_filename_and_hash():

    package = Package([
        make_upload_file(
            "archivo.txt",
            b"hola"
        )
    ])

    entry = package.manifest[0]

    assert set(entry.keys()) == {
        "index",
        "filename",
        "hash"
    }

    assert entry["filename"] == "archivo.txt"

    assert isinstance(
        entry["hash"],
        str
    )

    assert len(entry["hash"]) == 64


def test_get_proof_for_existing_file():

    package = Package([
        make_upload_file(
            "a.txt",
            b"a"
        ),
        make_upload_file(
            "b.txt",
            b"b"
        ),
        make_upload_file(
            "c.txt",
            b"c"
        )
    ])

    proof = package.get_proof(
        "b.txt"
    )

    assert isinstance(
        proof,
        list
    )


def test_get_proof_is_case_insensitive():

    package = Package([
        make_upload_file(
            "archivo.txt",
            b"hola"
        )
    ])

    assert package.get_proof(
        "ARCHIVO.TXT"
    ) == []


def test_get_proof_unknown_file():

    package = Package([
        make_upload_file(
            "archivo.txt",
            b"hola"
        )
    ])

    with pytest.raises(ValueError):

        package.get_proof(
            "otro.txt"
        )
