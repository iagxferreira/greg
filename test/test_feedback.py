"""Tests for src.feedback, with the DB connection mocked out (no real Postgres calls)."""

import json
from unittest.mock import Mock

from src.feedback import log_resolution
from src.models import CountryResult

RESULT = CountryResult(
    matched=True,
    name="Germany",
    iso2="DE",
    confidence=0.95,
    reason="Alemania is the Spanish translation for Germany",
)

CANDIDATES = [
    {"id": 1, "name": "Germany", "iso2": "DE", "similarity": 0.91, "content": "..."},
    {"id": 2, "name": "Armenia", "iso2": "AM", "similarity": 0.42, "content": "..."},
]


def _mock_connection():
    cursor = Mock()
    conn = Mock(cursor=Mock(return_value=cursor))
    return conn, cursor


def test_logs_query_source_result_and_candidate_summary(monkeypatch):
    conn, cursor = _mock_connection()
    monkeypatch.setattr("src.feedback.get_connection", lambda: conn)

    log_resolution("alemania", "rag", RESULT, CANDIDATES)

    cursor.execute.assert_called_once()
    sql, params = cursor.execute.call_args[0]
    assert "INSERT INTO resolution_feedback" in sql

    query, source, matched, name, iso2, confidence, reason, candidates_json = params
    assert query == "alemania"
    assert source == "rag"
    assert matched is True
    assert name == "Germany"
    assert iso2 == "DE"
    assert confidence == 0.95
    assert reason == RESULT.reason

    logged_candidates = json.loads(candidates_json)
    assert logged_candidates == [
        {"id": 1, "name": "Germany", "iso2": "DE", "similarity": 0.91},
        {"id": 2, "name": "Armenia", "iso2": "AM", "similarity": 0.42},
    ]
    conn.commit.assert_called_once()
    cursor.close.assert_called_once()
    conn.close.assert_called_once()


def test_logs_empty_candidates_when_none_considered(monkeypatch):
    conn, cursor = _mock_connection()
    monkeypatch.setattr("src.feedback.get_connection", lambda: conn)

    log_resolution("asdasdasd", "nominatim_fallback", CountryResult.no_match(), [])

    _, params = cursor.execute.call_args[0]
    assert json.loads(params[-1]) == []


def test_swallows_db_errors_and_warns(monkeypatch, capsys):
    monkeypatch.setattr(
        "src.feedback.get_connection", Mock(side_effect=RuntimeError("connection refused"))
    )

    log_resolution("alemania", "rag", RESULT, CANDIDATES)

    assert "failed to log resolution feedback" in capsys.readouterr().err
