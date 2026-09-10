from pathlib import Path

import pytest

from my_taste.core.models import Evidence
from my_taste.core.store import SQLiteTasteStore


def _evidence(*, source: str, context: str, domain: str = "writing", kind: str = "pairwise_text_choice") -> Evidence:
    return Evidence(kind=kind, domain=domain, context=context, source=source, payload={"fixture": True})


def test_query_evidence_preserves_provenance_scope(tmp_path: Path) -> None:
    store = SQLiteTasteStore(tmp_path / "taste.db")
    wanted = _evidence(source="explicit_choice", context="status update")
    store.add_evidence(wanted)
    store.add_evidence(_evidence(source="user_edit", context="status update"))
    store.add_evidence(_evidence(source="explicit_choice", context="release note"))
    store.add_evidence(_evidence(source="explicit_choice", context="status update", domain="design"))

    result = store.query_evidence(domain="writing", context="status update", source="explicit_choice")

    assert [item.id for item in result] == [wanted.id]
    assert all(item.domain == "writing" and item.context == "status update" and item.source == "explicit_choice" for item in result)


def test_query_evidence_can_filter_kind_without_collapsing_source(tmp_path: Path) -> None:
    store = SQLiteTasteStore(tmp_path / "taste.db")
    choice = _evidence(source="synthetic_a", context="status update")
    other = _evidence(source="synthetic_a", context="status update", kind="annotation")
    store.add_evidence(choice)
    store.add_evidence(other)

    result = store.query_evidence(domain="writing", context="status update", source="synthetic_a", kind="pairwise_text_choice")
    assert [item.id for item in result] == [choice.id]


def test_query_evidence_is_deterministic_and_fail_closed(tmp_path: Path) -> None:
    store = SQLiteTasteStore(tmp_path / "taste.db")
    store.add_evidence(_evidence(source="a", context="x"))
    first = store.query_evidence(domain="writing", limit=500)
    second = store.query_evidence(domain="writing", limit=500)
    assert [item.id for item in first] == [item.id for item in second]
    assert len(first) == 1
    with pytest.raises(ValueError):
        store.query_evidence(domain="   ")


@pytest.mark.parametrize("limit", [0, -1, 501])
def test_query_evidence_rejects_out_of_budget_limits(tmp_path: Path, limit: int) -> None:
    store = SQLiteTasteStore(tmp_path / "taste.db")
    with pytest.raises(ValueError):
        store.query_evidence(domain="writing", limit=limit)


@pytest.mark.parametrize("limit", [True, 1.5, "20"])
def test_query_evidence_rejects_non_integer_limits(tmp_path: Path, limit: object) -> None:
    store = SQLiteTasteStore(tmp_path / "taste.db")
    with pytest.raises(TypeError):
        store.query_evidence(domain="writing", limit=limit)  # type: ignore[arg-type]
