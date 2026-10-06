"""Tests for S.A.B.E.R. Pillar 1 -- content-addressed storage."""

from __future__ import annotations

from datetime import date

import pytest
from oraculus_di_auditor.legal.saber.content_store import ContentAddress, ContentStore
from oraculus_di_auditor.legal.saber.signing import SigningKey


@pytest.fixture()
def store(tmp_path):
    s = ContentStore(tmp_path / "saber_store")
    s.initialize()
    return s


@pytest.fixture()
def signing_key():
    return SigningKey.generate()


SAMPLE_TEXT = (
    "No person shall be compelled to be a witness against himself. "
    "Test provision for S.A.B.E.R. Phase 1."
)


def test_initialize_creates_directories(tmp_path):
    store = ContentStore(tmp_path / "new_store")
    store.initialize()
    assert (tmp_path / "new_store" / "blobs").is_dir()
    assert (tmp_path / "new_store" / "lookup").is_dir()
    assert (tmp_path / "new_store" / "index.json").exists()


def test_initialize_is_idempotent(store):
    store.initialize()
    store.initialize()  # should not raise
    assert store.blob_count() == 0


def test_put_returns_content_address(store):
    addr = store.put("cpra", "1798.121", SAMPLE_TEXT)
    assert isinstance(addr, ContentAddress)
    assert len(addr.sha256) == 64
    assert len(addr.sha3_512) == 128
    assert addr.content_length == len(SAMPLE_TEXT.encode("utf-8"))


def test_put_is_idempotent(store):
    addr1 = store.put("cpra", "1798.121", SAMPLE_TEXT)
    addr2 = store.put("cpra", "1798.121", SAMPLE_TEXT)
    assert addr1.sha256 == addr2.sha256
    assert store.blob_count() == 1


def test_get_returns_stored_text(store):
    addr = store.put("cpra", "1798.121", SAMPLE_TEXT)
    retrieved = store.get(addr.sha256)
    assert retrieved == SAMPLE_TEXT


def test_get_miss_returns_none(store):
    assert store.get("a" * 64) is None


def test_verify_blob_valid(store):
    addr = store.put("cpra", "1798.121", SAMPLE_TEXT)
    assert store.verify_blob(addr)


def test_verify_blob_after_tamper(store, tmp_path):
    addr = store.put("cpra", "1798.121", SAMPLE_TEXT)
    # Manually corrupt the blob
    blob_path = store._blobs / f"{addr.sha256}.txt"
    blob_path.write_text("TAMPERED", encoding="utf-8")
    assert not store.verify_blob(addr)


def test_resolve_citation(store):
    store.put("cpra", "1798.121", SAMPLE_TEXT)
    result = store.resolve_citation("cpra", "1798.121")
    assert result is not None
    text, addr = result
    assert text == SAMPLE_TEXT
    assert addr.sha256


def test_resolve_citation_miss_returns_none(store):
    assert store.resolve_citation("cpra", "9999.999") is None


def test_resolve_citation_as_of(store):
    old_text = "Old version of provision."
    new_text = "New version of provision."
    store.put("cpra", "1798.121", old_text, effective_date=date(2020, 1, 1))
    store.put("cpra", "1798.121", new_text, effective_date=date(2023, 1, 1))

    result_old = store.resolve_citation("cpra", "1798.121", as_of=date(2021, 6, 1))
    assert result_old is not None
    assert result_old[0] == old_text

    result_new = store.resolve_citation("cpra", "1798.121", as_of=date(2024, 1, 1))
    assert result_new is not None
    assert result_new[0] == new_text


def test_resolve_as_of_before_any_version_returns_none(store):
    store.put("cpra", "1798.121", SAMPLE_TEXT, effective_date=date(2020, 1, 1))
    result = store.resolve_citation("cpra", "1798.121", as_of=date(2019, 1, 1))
    assert result is None


def test_list_citations(store):
    store.put("cpra", "1798.100", "Provision 100.")
    store.put("cpra", "1798.121", "Provision 121.")
    citations = store.list_citations("cpra")
    assert "1798.100" in citations
    assert "1798.121" in citations


def test_corpus_ids(store):
    store.put("cpra", "1798.121", SAMPLE_TEXT)
    store.put("cal_codes", "CIV 1798.100", "Another provision.")
    ids = store.corpus_ids()
    assert "cpra" in ids
    assert "cal_codes" in ids


def test_lookup_signature_verification(store, signing_key):
    store.put("cpra", "1798.121", SAMPLE_TEXT, signing_key=signing_key)
    vk = signing_key.public_key()
    assert store.verify_lookup_signature("cpra", vk)


def test_lookup_signature_unsigned_returns_false(store, signing_key):
    store.put("cpra", "1798.121", SAMPLE_TEXT)  # no signing key
    vk = signing_key.public_key()
    assert not store.verify_lookup_signature("cpra", vk)


def test_multiple_corpora_independent_blobs(store):
    addr1 = store.put("cpra", "1798.121", SAMPLE_TEXT)
    addr2 = store.put("us_code", "42 USC 1983", SAMPLE_TEXT)
    # Identical text = same SHA-256 blob, but separate lookup entries
    assert addr1.sha256 == addr2.sha256
    assert store.blob_count() == 1
    assert store.list_citations("us_code") == ["42 USC 1983"]
