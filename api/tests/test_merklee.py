import hashlib

import pytest

from package import (
    LEAF_PREFIX,
    NODE_PREFIX,
    _leaf_hash,
    _node_hash,
    _merkle_root,
    verify_merkle_proof,
    Package
)

from tests.test_package import make_upload_file


def test_leaf_hash_uses_prefix():

    data = b"hello"

    expected = hashlib.sha256(
        LEAF_PREFIX + data
    ).hexdigest()

    assert _leaf_hash(data) == expected


def test_leaf_hash_is_not_plain_sha256():

    data = b"hello"

    plain_hash = hashlib.sha256(
        data
    ).hexdigest()

    assert _leaf_hash(data) != plain_hash


def test_node_hash_uses_prefix():

    left = hashlib.sha256(
        b"left"
    ).hexdigest()

    right = hashlib.sha256(
        b"right"
    ).hexdigest()

    expected = hashlib.sha256(
        NODE_PREFIX
        + bytes.fromhex(left)
        + bytes.fromhex(right)
    ).hexdigest()

    assert _node_hash(
        left,
        right
    ) == expected


def test_two_leaf_merkle_root():

    a = _leaf_hash(b"a")
    b = _leaf_hash(b"b")

    expected = _node_hash(
        a,
        b
    )

    assert _merkle_root([
        a,
        b
    ]) == expected


def test_three_leaf_merkle_root():

    a = _leaf_hash(b"a")
    b = _leaf_hash(b"b")
    c = _leaf_hash(b"c")

    left = _node_hash(
        a,
        b
    )

    expected = _node_hash(
        left,
        c
    )

    assert _merkle_root([
        a,
        b,
        c
    ]) == expected


def test_four_leaf_merkle_root():

    a = _leaf_hash(b"a")
    b = _leaf_hash(b"b")
    c = _leaf_hash(b"c")
    d = _leaf_hash(b"d")

    left = _node_hash(a, b)
    right = _node_hash(c, d)

    expected = _node_hash(
        left,
        right
    )

    assert _merkle_root([
        a,
        b,
        c,
        d
    ]) == expected


def test_five_leaf_merkle_root():

    hashes = [
        _leaf_hash(b"a"),
        _leaf_hash(b"b"),
        _leaf_hash(b"c"),
        _leaf_hash(b"d"),
        _leaf_hash(b"e")
    ]

    ab = _node_hash(
        hashes[0],
        hashes[1]
    )

    cd = _node_hash(
        hashes[2],
        hashes[3]
    )

    abcd = _node_hash(
        ab,
        cd
    )

    expected = _node_hash(
        abcd,
        hashes[4]
    )

    assert _merkle_root(
        hashes
    ) == expected


def test_single_leaf_root():

    leaf = _leaf_hash(
        b"hello"
    )

    assert _merkle_root([
        leaf
    ]) == leaf


def test_merkle_proof_single_leaf():

    leaf = _leaf_hash(
        b"hello"
    )

    proof = []

    assert verify_merkle_proof(
        leaf,
        proof,
        leaf
    )


def test_merkle_proof_two_leaves():

    a = _leaf_hash(b"a")
    b = _leaf_hash(b"b")

    root = _merkle_root([
        a,
        b
    ])

    proof_a = [
        {
            "hash": b,
            "position": "right"
        }
    ]

    proof_b = [
        {
            "hash": a,
            "position": "left"
        }
    ]

    assert verify_merkle_proof(
        a,
        proof_a,
        root
    )

    assert verify_merkle_proof(
        b,
        proof_b,
        root
    )


def test_merkle_proof_three_leaves():

    hashes = [
        _leaf_hash(b"a"),
        _leaf_hash(b"b"),
        _leaf_hash(b"c")
    ]

    root = _merkle_root(
        hashes
    )

    proof_a = [
        {
            "hash": hashes[1],
            "position": "right"
        },
        {
            "hash": hashes[2],
            "position": "right"
        }
    ]

    proof_b = [
        {
            "hash": hashes[0],
            "position": "left"
        },
        {
            "hash": hashes[2],
            "position": "right"
        }
    ]

    proof_c = [
        {
            "hash": _node_hash(
                hashes[0],
                hashes[1]
            ),
            "position": "left"
        }
    ]

    assert verify_merkle_proof(
        hashes[0],
        proof_a,
        root
    )

    assert verify_merkle_proof(
        hashes[1],
        proof_b,
        root
    )

    assert verify_merkle_proof(
        hashes[2],
        proof_c,
        root
    )


def test_invalid_merkle_proof():

    a = _leaf_hash(b"a")
    b = _leaf_hash(b"b")

    root = _merkle_root([
        a,
        b
    ])

    invalid_proof = [
        {
            "hash": b,
            "position": "left"
        }
    ]

    assert not verify_merkle_proof(
        a,
        invalid_proof,
        root
    )


def test_invalid_position():

    a = _leaf_hash(b"a")

    proof = [
        {
            "hash": a,
            "position": "invalid"
        }
    ]

    assert not verify_merkle_proof(
        a,
        proof,
        a
    )


def test_package_generates_proof():

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

    for filename in [
        "a.txt",
        "b.txt",
        "c.txt"
    ]:

        leaf = next(
            entry["hash"]
            for entry in package.manifest
            if entry["filename"] == filename
        )

        proof = package.get_proof(
            filename
        )

        assert verify_merkle_proof(
            leaf,
            proof,
            package.hash
        )


def test_package_proof_is_case_insensitive():

    package = Package([
        make_upload_file(
            "archivo.txt",
            b"hola"
        )
    ])

    proof = package.get_proof(
        "ARCHIVO.TXT"
    )

    assert proof == []


def test_package_proof_unknown_file():

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

