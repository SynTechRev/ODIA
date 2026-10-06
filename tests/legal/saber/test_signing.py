"""Tests for S.A.B.E.R. Pillar 4 -- hybrid signing."""

from __future__ import annotations

import json

import pytest
from oraculus_di_auditor.legal.saber.signing import (
    _ALGORITHM_ED25519_ONLY,
    _ALGORITHM_HYBRID,
    _ML_DSA_AVAILABLE,
    HybridSignature,
    SigningKey,
    VerifyKey,
)


@pytest.fixture()
def key_pair(tmp_path):
    key = SigningKey.generate()
    key.save(tmp_path / "key")
    return key, tmp_path / "key"


def test_generate_produces_hybrid_or_ed25519_only():
    key = SigningKey.generate()
    assert key is not None


def test_sign_and_verify(key_pair):
    key, _ = key_pair
    data = b"corpus manifest bytes for testing"
    sig = key.sign(data)
    assert isinstance(sig, HybridSignature)
    assert key.public_key().verify(data, sig)


def test_verify_wrong_data_fails(key_pair):
    key, _ = key_pair
    sig = key.sign(b"correct data")
    assert not key.public_key().verify(b"tampered data", sig)


def test_algorithm_label(key_pair):
    key, _ = key_pair
    sig = key.sign(b"test")
    expected = _ALGORITHM_HYBRID if _ML_DSA_AVAILABLE else _ALGORITHM_ED25519_ONLY
    assert sig.algorithm == expected


def test_save_and_load_roundtrip(tmp_path, key_pair):
    key, key_dir = key_pair
    data = b"roundtrip test payload"
    sig = key.sign(data)
    loaded_key = SigningKey.load(key_dir)
    assert loaded_key.public_key().verify(data, sig)


def test_public_key_json_written(key_pair):
    _, key_dir = key_pair
    pub_path = key_dir / "public.json"
    assert pub_path.exists()
    pub = json.loads(pub_path.read_text(encoding="utf-8"))
    assert "ed25519_pub" in pub
    assert "algorithm" in pub


def test_verify_key_load(key_pair):
    key, key_dir = key_pair
    data = b"verify key load test"
    sig = key.sign(data)
    vk = VerifyKey.load(key_dir)
    assert vk.verify(data, sig)


def test_hybrid_signature_dict_roundtrip(key_pair):
    key, _ = key_pair
    data = b"dict roundtrip"
    sig = key.sign(data)
    d = sig.to_dict()
    sig2 = HybridSignature.from_dict(d)
    assert sig2.ed25519_sig == sig.ed25519_sig
    assert sig2.ml_dsa_sig == sig.ml_dsa_sig
    assert sig2.algorithm == sig.algorithm


def test_tampered_ed25519_sig_fails(key_pair):
    key, _ = key_pair
    data = b"original"
    sig = key.sign(data)
    bad_sig = HybridSignature(
        ed25519_sig=bytes(64),  # all-zero -- invalid
        ml_dsa_sig=sig.ml_dsa_sig,
        algorithm=sig.algorithm,
    )
    assert not key.public_key().verify(data, bad_sig)


@pytest.mark.skipif(_ML_DSA_AVAILABLE, reason="only runs without liboqs")
def test_ed25519_only_when_no_liboqs():
    key = SigningKey.generate()
    sig = key.sign(b"no liboqs test")
    assert sig.ml_dsa_sig is None
    assert sig.algorithm == _ALGORITHM_ED25519_ONLY
    assert key.public_key().verify(b"no liboqs test", sig)


@pytest.mark.skipif(not _ML_DSA_AVAILABLE, reason="requires liboqs")
def test_ml_dsa_upgrade_roundtrip(tmp_path):
    """An Ed25519-only key dir upgraded to hybrid produces valid hybrid signatures."""
    import oqs  # type: ignore[import]

    # Create a key dir with only Ed25519 (simulate pre-liboqs state)
    key_dir = tmp_path / "key"
    key_dir.mkdir()
    ed_key = SigningKey.generate()
    # Save only the ed25519 component by temporarily patching
    ed_key._ml = None
    ed_key.save(key_dir)
    assert not (key_dir / "ml_dsa.bin").exists()

    # Simulate what saber_upgrade_key.py does
    ml = oqs.Signature("ML-DSA-65")
    ml_pub: bytes = ml.generate_keypair()
    (key_dir / "ml_dsa.bin").write_bytes(ml.secret_key)
    pub = json.loads((key_dir / "public.json").read_text(encoding="utf-8"))
    pub["algorithm"] = _ALGORITHM_HYBRID
    pub["ml_dsa_pub"] = ml_pub.hex()
    (key_dir / "public.json").write_text(json.dumps(pub), encoding="utf-8")

    # Load the upgraded key and confirm hybrid signing works
    upgraded = SigningKey.load(key_dir)
    data = b"key upgrade integration test"
    sig = upgraded.sign(data)
    assert sig.algorithm == _ALGORITHM_HYBRID
    assert sig.ml_dsa_sig is not None
    assert upgraded.public_key().verify(data, sig)

    # VerifyKey.load() also verifies correctly
    vk = VerifyKey.load(key_dir)
    assert vk.verify(data, sig)
