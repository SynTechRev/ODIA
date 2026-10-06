"""Tests for S.A.B.E.R. Pillar 3 -- append-only Merkle audit log."""

from __future__ import annotations

import json

import pytest
from oraculus_di_auditor.legal.saber.audit_log import _GENESIS_PREV_HASH, AuditLog


@pytest.fixture()
def log(tmp_path):
    return AuditLog(tmp_path / "audit" / "saber.log")


def test_append_single_entry(log):
    entry = log.append("init", "cpra")
    assert entry["seq"] == 0
    assert entry["op"] == "init"
    assert entry["corpus_id"] == "cpra"
    assert entry["prev_hash"] == _GENESIS_PREV_HASH
    assert len(entry["entry_hash"]) == 64


def test_append_chains_prev_hash(log):
    e0 = log.append("init", "cpra")
    e1 = log.append("put", "cpra", citation="1798.121", sha256="a" * 64)
    assert e1["prev_hash"] == e0["entry_hash"]


def test_append_increments_seq(log):
    for i in range(5):
        e = log.append("put", "cpra")
        assert e["seq"] == i


def test_verify_chain_empty_returns_true(log):
    assert log.verify_chain()


def test_verify_chain_valid(log):
    for _ in range(10):
        log.append("put", "cpra")
    assert log.verify_chain()


def test_verify_chain_detects_tampered_entry(log):
    log.append("init", "cpra")
    log.append("put", "cpra")
    # Manually tamper the first entry
    raw = log._path.read_text(encoding="utf-8").split("\n")
    entry = json.loads(raw[0])
    entry["corpus_id"] = "TAMPERED"
    raw[0] = json.dumps(entry)
    log._path.write_text("\n".join(raw), encoding="utf-8")
    assert not log.verify_chain()


def test_verify_chain_detects_tampered_prev_hash(log):
    log.append("init", "cpra")
    log.append("put", "cpra")
    raw = log._path.read_text(encoding="utf-8").split("\n")
    entry = json.loads(raw[1])
    entry["prev_hash"] = "0" * 64  # wrong -- should be first entry's hash
    entry["entry_hash"] = "x" * 64  # also wrong so both checks can fail
    raw[1] = json.dumps(entry)
    log._path.write_text("\n".join(raw), encoding="utf-8")
    assert not log.verify_chain()


def test_root_hash_changes_on_append(log):
    r0 = log.root_hash()
    log.append("init", "cpra")
    r1 = log.root_hash()
    log.append("put", "cpra")
    r2 = log.root_hash()
    assert r0 != r1
    assert r1 != r2


def test_root_hash_empty_log(log):
    h = log.root_hash()
    assert len(h) == 64


def test_entry_count(log):
    assert log.entry_count() == 0
    for i in range(7):
        log.append("put", "cpra")
    assert log.entry_count() == 7


def test_entries_returns_all(log):
    log.append("init", "cpra")
    log.append("put", "cpra", citation="1798.121")
    entries = log.entries()
    assert len(entries) == 2
    assert entries[0]["op"] == "init"
    assert entries[1]["citation"] == "1798.121"


def test_write_checkpoint(log, tmp_path):
    log.append("init", "cpra")
    log.append("put", "cpra")
    out = tmp_path / "checkpoints" / "cp.json"
    root = log.write_checkpoint(out)
    assert out.exists()
    cp = json.loads(out.read_text(encoding="utf-8"))
    assert cp["root_hash"] == root
    assert cp["entry_count"] == 2
    assert cp["saber_audit_checkpoint"] is True


def test_miss_result_recorded(log):
    e = log.append("resolve", "cpra", citation="9999.999", result="miss")
    assert e["result"] == "miss"
