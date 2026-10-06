"""Tests for S.A.B.E.R. Pillar 2 -- reproducible loader manifest."""

from __future__ import annotations

import pytest
from oraculus_di_auditor.legal.saber.manifest import LoaderManifest
from oraculus_di_auditor.legal.saber.signing import SigningKey


@pytest.fixture()
def signing_key():
    return SigningKey.generate()


def test_record_creates_manifest():
    m = LoaderManifest.record(
        corpus_id="cpra",
        source_description="Embedded provisions in cpra_corpus.py",
        source_hash="a" * 64,
        snapshot_hash="b" * 64,
        provision_count=13,
    )
    assert m.corpus_id == "cpra"
    assert m.provision_count == 13
    assert m.snapshot_hash == "b" * 64


def test_manifest_includes_env():
    m = LoaderManifest.record("cpra", "test", "a" * 64, "b" * 64, 1)
    d = m.to_dict()
    assert "loader_env" in d
    assert "python" in d["loader_env"]
    assert "liboqs_available" in d["loader_env"]


def test_manifest_records_loaded_at():
    m = LoaderManifest.record("cpra", "test", "a" * 64, "b" * 64, 1)
    assert m.loaded_at


def test_manifest_unsigned_verify_returns_false():
    m = LoaderManifest.record("cpra", "test", "a" * 64, "b" * 64, 1)
    assert not m.verify_signature()


def test_manifest_signed_verify_returns_true(signing_key):
    m = LoaderManifest.record(
        corpus_id="cpra",
        source_description="test",
        source_hash="a" * 64,
        snapshot_hash="b" * 64,
        provision_count=1,
        signing_key=signing_key,
    )
    assert m.verify_signature()


def test_save_and_load_roundtrip(tmp_path):
    m = LoaderManifest.record("cpra", "test source", "a" * 64, "b" * 64, 5)
    saved_path = m.save(tmp_path / "manifests")
    assert saved_path.exists()
    loaded = LoaderManifest.load(saved_path)
    assert loaded.corpus_id == "cpra"
    assert loaded.provision_count == 5
    assert loaded.snapshot_hash == "b" * 64


def test_save_filename_contains_corpus_id(tmp_path):
    m = LoaderManifest.record("us_code", "test", "a" * 64, "b" * 64, 100)
    path = m.save(tmp_path / "manifests")
    assert "us_code" in path.name


def test_to_dict_contains_all_fields():
    m = LoaderManifest.record("cfr", "test", "a" * 64, "b" * 64, 0)
    d = m.to_dict()
    required_fields = {
        "manifest_version",
        "saber_manifest",
        "corpus_id",
        "loader_hash",
        "source_description",
        "source_hash",
        "snapshot_hash",
        "provision_count",
        "loaded_at",
        "loader_env",
        "signature",
    }
    assert required_fields.issubset(d.keys())


def test_signed_manifest_json_roundtrip(tmp_path, signing_key):
    m = LoaderManifest.record(
        corpus_id="cal_codes",
        source_description="test",
        source_hash="c" * 64,
        snapshot_hash="d" * 64,
        provision_count=42,
        signing_key=signing_key,
    )
    path = m.save(tmp_path / "manifests")
    loaded = LoaderManifest.load(path)
    assert loaded.verify_signature()
    d = loaded.to_dict()
    assert d["signature"]["algorithm"] in ("ed25519", "ed25519+ml-dsa-65")
