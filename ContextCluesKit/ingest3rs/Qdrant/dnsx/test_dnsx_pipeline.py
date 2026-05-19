#!/usr/bin/env python3
"""Unit tests for dnsx conversion, correlation, and ingestion."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[3]
CONVERTER = ROOT / "convert3rs" / "dnsx" / "convert3r_dnsx.py"
INGESTOR = Path(__file__).with_name("ingest3r_dnsx.py")
CORRELATION = Path(__file__).with_name("correlation_engine.py")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def install_fake_qdrant_modules() -> None:
    class Distance:
        COSINE = "Cosine"

    class VectorParams:
        def __init__(self, size, distance):
            self.size = size
            self.distance = distance

    class PayloadSchemaType:
        KEYWORD = "keyword"

    class PointStruct:
        def __init__(self, id, vector, payload):
            self.id = id
            self.vector = vector
            self.payload = payload

    class MatchValue:
        def __init__(self, value):
            self.value = value

    class FieldCondition:
        def __init__(self, key, match):
            self.key = key
            self.match = match

    class Filter:
        def __init__(self, must):
            self.must = must

    fake_models = SimpleNamespace(
        Distance=Distance,
        VectorParams=VectorParams,
        PayloadSchemaType=PayloadSchemaType,
        PointStruct=PointStruct,
        MatchValue=MatchValue,
        FieldCondition=FieldCondition,
        Filter=Filter,
    )
    fake_qdrant = SimpleNamespace(QdrantClient=object, models=fake_models)
    sys.modules["qdrant_client"] = fake_qdrant
    sys.modules["qdrant_client.http"] = SimpleNamespace(models=fake_models)


def test_convert_dnsx_jsonl_normalizes_records():
    converter = load_module("convert3r_dnsx_test", CONVERTER)
    lines = [
        '{"host":"www.example.com","a":"93.184.216.34","resolver":"1.1.1.1:53","status_code":"NOERROR"}',
        "",
        "not json",
        '["not-object"]',
    ]

    records, skipped = converter.convert_dnsx_jsonl(lines, timestamp="2026-01-01T00:00:00Z")

    assert skipped == 3
    assert len(records) == 1
    assert records[0]["id"] == 1
    assert records[0]["host"] == "www.example.com"
    assert records[0]["a"] == ["93.184.216.34"]
    assert records[0]["resolver"] == ["1.1.1.1:53"]
    assert records[0]["raw_response"]["host"] == "www.example.com"


def test_correlation_matches_current_subfinder_hostname_payload():
    install_fake_qdrant_modules()
    correlation = load_module("dnsx_correlation_test", CORRELATION)
    client = MagicMock()
    client.get_collections.return_value = SimpleNamespace(collections=[SimpleNamespace(name="Subfinder_json")])
    client.scroll.return_value = ([SimpleNamespace(id=42, payload={"hostname": "www.example.com"})], None)

    engine = correlation.DNSCorrelationEngine(client, collections=["Subfinder_json"])
    record = engine.correlate_dns_record({"id": 1, "host": "www.example.com", "a": ["93.184.216.34"]})

    assert record["correlation_status"] == "matched"
    assert record["linked_subdomain_id"] == 42
    assert record["linked_collection"] == "Subfinder_json"
    assert record["resolved_ips"] == ["93.184.216.34"]


def test_correlation_updates_linked_subdomain_payload():
    install_fake_qdrant_modules()
    correlation = load_module("dnsx_correlation_update_test", CORRELATION)
    client = MagicMock()
    engine = correlation.DNSCorrelationEngine(client, collections=[])

    ok = engine.update_subdomain_with_dns_info(
        {
            "id": 9,
            "timestamp": "2026-01-01T00:00:00Z",
            "correlation_status": "matched",
            "linked_subdomain_id": 42,
            "linked_collection": "Subfinder_json",
            "a": ["93.184.216.34"],
            "aaaa": ["2001:db8::1"],
        }
    )

    assert ok is True
    client.set_payload.assert_called_once()
    payload = client.set_payload.call_args.kwargs["payload"]
    assert payload["latest_dns_record_id"] == 9
    assert payload["resolved_ips"] == ["93.184.216.34"]
    assert payload["resolved_ipv6"] == ["2001:db8::1"]


def test_ingestor_uploads_without_correlation():
    install_fake_qdrant_modules()
    ingestor_mod = load_module("dnsx_ingestor_test", INGESTOR)
    client = MagicMock()
    client.get_collections.return_value = SimpleNamespace(collections=[])
    client.count.return_value = SimpleNamespace(count=0)

    ingestor = ingestor_mod.DNSxIngestor(client, "dnsx_records", vector_size=8)
    stats = ingestor.ingest_records([{"id": 1, "host": "www.example.com", "a": ["93.184.216.34"]}], batch_size=100)

    assert stats == {"total": 1, "inserted": 1, "updated": 0, "correlated": 0, "errors": 0}
    client.create_collection.assert_called_once()
    client.upsert.assert_called_once()
    point = client.upsert.call_args.kwargs["points"][0]
    assert point.id == 1
    assert len(point.vector) == 8
    assert point.payload["host"] == "www.example.com"


def test_ingestor_reuses_existing_dns_record_id_on_update():
    install_fake_qdrant_modules()
    ingestor_mod = load_module("dnsx_ingestor_update_test", INGESTOR)
    client = MagicMock()
    client.get_collections.return_value = SimpleNamespace(collections=[SimpleNamespace(name="dnsx_records")])
    client.count.return_value = SimpleNamespace(count=1)
    engine = MagicMock()
    engine.correlate_dns_record.side_effect = lambda record: {**record, "correlation_status": "unmatched"}
    engine.prepare_upsert_operation.return_value = {"operation": "update", "point_id": 99, "record": {}}

    ingestor = ingestor_mod.DNSxIngestor(client, "dnsx_records", vector_size=8)
    stats = ingestor.ingest_records([{"id": 1, "host": "www.example.com"}], correlation_engine=engine)

    assert stats["updated"] == 1
    assert stats["inserted"] == 0
    point = client.upsert.call_args.kwargs["points"][0]
    assert point.id == 99
    assert point.payload["id"] == 99
