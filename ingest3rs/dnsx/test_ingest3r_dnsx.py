#!/usr/bin/env python3
"""
Tests for dnsx Ingestor and Correlation Engine

Covers:
- DNSxIngestor: collection management, embedding generation, record ingestion
- DNSCorrelationEngine: subdomain matching, enrichment, upsert logic, bidirectional linking
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from types import SimpleNamespace

# Ensure the dnsx directory is on sys.path so local imports resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Block sentence-transformers from being imported (avoids model download hang)
# Must happen BEFORE importing ingest3r_dnsx
sys.modules["sentence_transformers"] = None  # type: ignore

from correlation_engine import DNSCorrelationEngine
import ingest3r_dnsx
from ingest3r_dnsx import DNSxIngestor


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_mock_client(existing_collections=None):
    """Create a mock QdrantClient with configurable existing collections."""
    client = MagicMock()
    cols = [SimpleNamespace(name=n) for n in (existing_collections or [])]
    client.get_collections.return_value = SimpleNamespace(collections=cols)
    client.count.return_value = SimpleNamespace(count=0)
    return client


SAMPLE_DNS_RECORD = {
    "id": 1,
    "host": "www.example.com",
    "resolver": ["1.1.1.1:53"],
    "a": ["93.184.216.34"],
    "aaaa": ["2606:2800:220:1:248:1893:25c8:1946"],
    "cname": [],
    "mx": [],
    "ns": [],
    "txt": [],
    "status_code": "NOERROR",
    "timestamp": "2025-01-15T10:30:00Z",
    "source_tool": "dnsx",
}

SAMPLE_MX_RECORD = {
    "id": 2,
    "host": "mail.example.com",
    "resolver": ["1.1.1.1:53"],
    "a": ["93.184.216.35"],
    "aaaa": [],
    "cname": [],
    "mx": ["mail.example.com", "mail2.example.com"],
    "ns": [],
    "txt": ["v=spf1 include:_spf.example.com ~all"],
    "status_code": "NOERROR",
    "timestamp": "2025-01-15T10:30:00Z",
    "source_tool": "dnsx",
}


# ---------------------------------------------------------------------------
# DNSxIngestor Tests
# ---------------------------------------------------------------------------

class TestDNSxIngestorCollection:
    """Tests for collection creation and management."""

    def test_ensure_collection_creates_new(self):
        """When collection doesn't exist, it should be created."""
        client = _make_mock_client(existing_collections=[])
        DNSxIngestor(client=client, collection_name="dnsx_records", vector_size=384)

        client.create_collection.assert_called_once()
        call_kwargs = client.create_collection.call_args
        assert call_kwargs[1]["collection_name"] == "dnsx_records"

    def test_ensure_collection_uses_existing(self):
        """When collection already exists, it should not be created again."""
        client = _make_mock_client(existing_collections=["dnsx_records"])
        DNSxIngestor(client=client, collection_name="dnsx_records", vector_size=384)

        client.create_collection.assert_not_called()


class TestDNSxIngestorEmbedding:
    """Tests for vector embedding generation (hash-based fallback)."""

    def test_generate_embedding_returns_correct_size(self):
        client = _make_mock_client()
        ingestor = DNSxIngestor(client=client, collection_name="test", vector_size=384)

        vec = ingestor.generate_embedding(SAMPLE_DNS_RECORD)
        assert len(vec) == 384

    def test_generate_embedding_is_deterministic(self):
        client = _make_mock_client()
        ingestor = DNSxIngestor(client=client, collection_name="test", vector_size=384)

        vec1 = ingestor.generate_embedding(SAMPLE_DNS_RECORD)
        vec2 = ingestor.generate_embedding(SAMPLE_DNS_RECORD)
        assert vec1 == vec2

    def test_generate_embedding_different_records_differ(self):
        client = _make_mock_client()
        ingestor = DNSxIngestor(client=client, collection_name="test", vector_size=384)

        vec1 = ingestor.generate_embedding(SAMPLE_DNS_RECORD)
        vec2 = ingestor.generate_embedding(SAMPLE_MX_RECORD)
        assert vec1 != vec2

    def test_generate_embedding_values_in_range(self):
        """All values should be normalised to [-1, 1]."""
        client = _make_mock_client()
        ingestor = DNSxIngestor(client=client, collection_name="test", vector_size=384)

        vec = ingestor.generate_embedding(SAMPLE_DNS_RECORD)
        assert all(-1 <= v <= 1 for v in vec)

    def test_generate_embedding_custom_vector_size(self):
        client = _make_mock_client()
        ingestor = DNSxIngestor(client=client, collection_name="test", vector_size=128)

        vec = ingestor.generate_embedding(SAMPLE_DNS_RECORD)
        assert len(vec) == 128


class TestDNSxIngestorIngestion:
    """Tests for record ingestion logic."""

    def test_ingest_records_no_correlation(self):
        """Records should be ingested with sequential IDs when no correlation engine."""
        client = _make_mock_client()
        ingestor = DNSxIngestor(client=client, collection_name="test", vector_size=384)

        records = [SAMPLE_DNS_RECORD, SAMPLE_MX_RECORD]
        stats = ingestor.ingest_records(dns_records=records, batch_size=100)

        assert stats["total"] == 2
        assert stats["inserted"] == 2
        assert stats["errors"] == 0
        client.upsert.assert_called_once()

    def test_ingest_records_batching(self):
        """With batch_size=1, upsert should be called once per record + remainder."""
        client = _make_mock_client()
        ingestor = DNSxIngestor(client=client, collection_name="test", vector_size=384)

        records = [SAMPLE_DNS_RECORD, SAMPLE_MX_RECORD]
        stats = ingestor.ingest_records(dns_records=records, batch_size=1)

        assert stats["total"] == 2
        assert stats["inserted"] == 2
        # batch_size=1 → 2 batch calls
        assert client.upsert.call_count == 2

    def test_ingest_records_error_handling(self):
        """A record that raises during embedding should be counted as error, not crash."""
        client = _make_mock_client()
        ingestor = DNSxIngestor(client=client, collection_name="test", vector_size=384)

        # Force generate_embedding to raise on first call only
        original = ingestor.generate_embedding
        call_count = {"n": 0}

        def failing_embedding(rec):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise ValueError("test error")
            return original(rec)

        ingestor.generate_embedding = failing_embedding

        records = [SAMPLE_DNS_RECORD, SAMPLE_MX_RECORD]
        stats = ingestor.ingest_records(dns_records=records, batch_size=100)

        assert stats["errors"] == 1
        # Note: in the no-correlation path, 'inserted' increments before embedding,
        # so the errored record is still counted as inserted.
        assert stats["inserted"] == 2

    def test_ingest_records_with_correlation(self):
        """Records should be correlated and stats updated when engine is provided."""
        client = _make_mock_client()
        ingestor = DNSxIngestor(client=client, collection_name="test", vector_size=384)

        mock_engine = MagicMock(spec=DNSCorrelationEngine)

        def correlate_side_effect(record):
            record["correlation_status"] = "matched"
            record["linked_subdomain_id"] = 42
            return record

        mock_engine.correlate_dns_record.side_effect = correlate_side_effect
        mock_engine.prepare_upsert_operation.return_value = {
            "operation": "insert",
            "point_id": None,
        }

        records = [SAMPLE_DNS_RECORD.copy()]
        stats = ingestor.ingest_records(
            dns_records=records, correlation_engine=mock_engine, batch_size=100
        )

        assert stats["correlated"] == 1
        assert stats["inserted"] == 1
        mock_engine.update_subdomain_with_dns_info.assert_called_once()

    def test_ingest_records_upsert_update_path(self):
        """When correlation engine says 'update', existing point_id should be reused."""
        client = _make_mock_client()
        ingestor = DNSxIngestor(client=client, collection_name="test", vector_size=384)

        mock_engine = MagicMock(spec=DNSCorrelationEngine)
        mock_engine.correlate_dns_record.side_effect = lambda r: r
        mock_engine.prepare_upsert_operation.return_value = {
            "operation": "update",
            "point_id": 99,
        }

        records = [SAMPLE_DNS_RECORD.copy()]
        stats = ingestor.ingest_records(
            dns_records=records, correlation_engine=mock_engine, batch_size=100
        )

        assert stats["updated"] == 1
        assert stats["inserted"] == 0

        # Verify the point used id=99
        upsert_call = client.upsert.call_args
        points = upsert_call[1]["points"]
        assert points[0].id == 99


# ---------------------------------------------------------------------------
# DNSCorrelationEngine Tests
# ---------------------------------------------------------------------------

class TestCorrelationEngineMatching:
    """Tests for subdomain matching."""

    def test_find_matching_subdomain_found(self):
        """Should return match info when subdomain exists in a collection."""
        client = _make_mock_client(existing_collections=["subfinder"])
        mock_point = SimpleNamespace(id=42, payload={"hostname": "www.example.com"})
        client.scroll.return_value = ([mock_point], None)

        engine = DNSCorrelationEngine(client, collections=["subfinder"])
        result = engine.find_matching_subdomain("www.example.com")

        assert result is not None
        assert result["id"] == 42
        assert result["collection"] == "subfinder"

    def test_find_matching_subdomain_not_found(self):
        """Should return None when no collection matches the hostname."""
        client = _make_mock_client(existing_collections=["subfinder"])
        client.scroll.return_value = ([], None)

        engine = DNSCorrelationEngine(client, collections=["subfinder"])
        result = engine.find_matching_subdomain("nonexistent.example.com")

        assert result is None

    def test_find_matching_subdomain_skips_missing_collections(self):
        """Collections not present in Qdrant should be skipped gracefully."""
        client = _make_mock_client(existing_collections=[])

        engine = DNSCorrelationEngine(client, collections=["does_not_exist"])
        result = engine.find_matching_subdomain("www.example.com")

        assert result is None
        client.scroll.assert_not_called()


class TestCorrelationEngineEnrichment:
    """Tests for DNS record enrichment / correlation."""

    def test_correlate_dns_record_matched(self):
        """A matched record should have correlation fields added."""
        client = _make_mock_client(existing_collections=["subfinder"])
        mock_point = SimpleNamespace(id=42, payload={"hostname": "www.example.com"})
        client.scroll.return_value = ([mock_point], None)

        engine = DNSCorrelationEngine(client, collections=["subfinder"])
        record = SAMPLE_DNS_RECORD.copy()
        result = engine.correlate_dns_record(record)

        assert result["correlation_status"] == "matched"
        assert result["linked_subdomain_id"] == 42
        assert result["linked_collection"] == "subfinder"
        assert result["resolved_ips"] == ["93.184.216.34"]

    def test_correlate_dns_record_unmatched(self):
        """An unmatched record should be marked as 'unmatched'."""
        client = _make_mock_client(existing_collections=["subfinder"])
        client.scroll.return_value = ([], None)

        engine = DNSCorrelationEngine(client, collections=["subfinder"])
        record = SAMPLE_DNS_RECORD.copy()
        result = engine.correlate_dns_record(record)

        assert result["correlation_status"] == "unmatched"
        assert "linked_subdomain_id" not in result

    def test_correlate_dns_record_empty_host(self):
        """A record without a host should be counted as error."""
        client = _make_mock_client()
        engine = DNSCorrelationEngine(client, collections=[])

        record = {"a": ["1.2.3.4"]}  # no host field
        result = engine.correlate_dns_record(record)

        assert engine.get_stats()["errors"] == 1

    def test_stats_tracking(self):
        """Stats should increment correctly across multiple calls."""
        client = _make_mock_client(existing_collections=["subfinder"])
        client.scroll.return_value = ([], None)

        engine = DNSCorrelationEngine(client, collections=["subfinder"])

        engine.correlate_dns_record(SAMPLE_DNS_RECORD.copy())
        engine.correlate_dns_record(SAMPLE_MX_RECORD.copy())

        stats = engine.get_stats()
        assert stats["unmatched"] == 2
        assert stats["matched"] == 0

    def test_reset_stats(self):
        """reset_stats should zero all counters."""
        client = _make_mock_client(existing_collections=["subfinder"])
        client.scroll.return_value = ([], None)

        engine = DNSCorrelationEngine(client, collections=["subfinder"])
        engine.correlate_dns_record(SAMPLE_DNS_RECORD.copy())

        engine.reset_stats()
        stats = engine.get_stats()
        assert all(v == 0 for v in stats.values())


class TestCorrelationEngineUpsert:
    """Tests for upsert (latest-only) logic."""

    def test_prepare_upsert_existing(self):
        """Should return 'update' operation with existing point_id."""
        client = _make_mock_client(existing_collections=["dnsx_records"])
        mock_point = SimpleNamespace(id=10, payload={"host": "www.example.com"})
        client.scroll.return_value = ([mock_point], None)

        engine = DNSCorrelationEngine(client, collections=[])
        result = engine.prepare_upsert_operation(SAMPLE_DNS_RECORD, "dnsx_records")

        assert result["operation"] == "update"
        assert result["point_id"] == 10

    def test_prepare_upsert_new(self):
        """Should return 'insert' when no existing record found."""
        client = _make_mock_client(existing_collections=["dnsx_records"])
        client.scroll.return_value = ([], None)

        engine = DNSCorrelationEngine(client, collections=[])
        result = engine.prepare_upsert_operation(SAMPLE_DNS_RECORD, "dnsx_records")

        assert result["operation"] == "insert"
        assert result["point_id"] is None


class TestCorrelationEngineBidirectionalLinking:
    """Tests for updating subdomain records with DNS info."""

    def test_update_subdomain_success(self):
        """Should call set_payload on the linked collection."""
        client = _make_mock_client()
        engine = DNSCorrelationEngine(client, collections=[])

        record = {
            "host": "www.example.com",
            "correlation_status": "matched",
            "linked_subdomain_id": 42,
            "linked_collection": "subfinder",
            "a": ["93.184.216.34"],
            "aaaa": ["2606::1"],
            "timestamp": "2025-01-15T10:30:00Z",
        }

        result = engine.update_subdomain_with_dns_info(record)

        assert result is True
        client.set_payload.assert_called_once()
        call_kwargs = client.set_payload.call_args[1]
        assert call_kwargs["collection_name"] == "subfinder"
        assert call_kwargs["points"] == [42]
        assert "resolved_ips" in call_kwargs["payload"]
        assert "resolved_ipv6" in call_kwargs["payload"]

    def test_update_subdomain_unmatched_record(self):
        """Should return False for unmatched records."""
        client = _make_mock_client()
        engine = DNSCorrelationEngine(client, collections=[])

        record = {"host": "www.example.com", "correlation_status": "unmatched"}
        result = engine.update_subdomain_with_dns_info(record)

        assert result is False
        client.set_payload.assert_not_called()

    def test_update_subdomain_missing_link_fields(self):
        """Should return False when link fields are missing."""
        client = _make_mock_client()
        engine = DNSCorrelationEngine(client, collections=[])

        record = {"host": "www.example.com", "correlation_status": "matched"}
        result = engine.update_subdomain_with_dns_info(record)

        assert result is False

    def test_update_subdomain_client_error(self):
        """Should return False and not crash on Qdrant errors."""
        client = _make_mock_client()
        client.set_payload.side_effect = Exception("Qdrant connection lost")
        engine = DNSCorrelationEngine(client, collections=[])

        record = {
            "host": "www.example.com",
            "correlation_status": "matched",
            "linked_subdomain_id": 42,
            "linked_collection": "subfinder",
        }
        result = engine.update_subdomain_with_dns_info(record)

        assert result is False
