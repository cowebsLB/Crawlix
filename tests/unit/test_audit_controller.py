from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from crawlix.db.models import Base, Page, Project, SeoAudit
from crawlix.ui.controllers_audit import (
    build_audit_row_meta,
    issue_count,
    query_audit_results_rows,
)


def test_issue_count_handles_non_list() -> None:
    assert issue_count(None) == 0
    assert issue_count({"a": 1}) == 0
    assert issue_count([1, 2, 3]) == 3


def test_build_audit_row_meta_normalizes_payload() -> None:
    meta = build_audit_row_meta(
        page_id=5,
        url_norm="https://example.com/p",
        issues={"bad": True},
        inbound=2,
        outbound=3,
    )
    assert meta["page_id"] == 5
    assert meta["url_norm"] == "https://example.com/p"
    assert meta["issues"] == []
    assert meta["inbound"] == 2
    assert meta["outbound"] == 3


def test_query_audit_results_rows_prioritizes_page() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    s = Session()
    proj = Project(name="T", slug="t")
    s.add(proj)
    s.commit()
    a = Page(project_id=proj.id, url_norm="https://ex.test/a")
    b = Page(project_id=proj.id, url_norm="https://ex.test/b")
    c = Page(project_id=proj.id, url_norm="https://ex.test/c")
    s.add_all([a, b, c])
    s.commit()
    t_new = datetime(2025, 6, 1, tzinfo=UTC)
    t_mid = datetime(2025, 3, 1, tzinfo=UTC)
    t_old = datetime(2025, 1, 1, tzinfo=UTC)
    s.add(SeoAudit(page_id=a.id, issues_json=[], audited_at=t_new))
    s.add(SeoAudit(page_id=b.id, issues_json=[], audited_at=t_mid))
    s.add(SeoAudit(page_id=c.id, issues_json=[], audited_at=t_old))
    s.commit()
    default = query_audit_results_rows(s, proj.id, limit=10)
    assert [x[1].id for x in default] == [a.id, b.id, c.id]
    pinned = query_audit_results_rows(s, proj.id, limit=10, prioritize_page_id=c.id)
    assert [x[1].id for x in pinned] == [c.id, a.id, b.id]


def test_query_audit_results_rows_unknown_page_unchanged() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    s = Session()
    proj = Project(name="T2", slug="t2")
    s.add(proj)
    s.commit()
    p = Page(project_id=proj.id, url_norm="https://ex.test/p")
    s.add(p)
    s.commit()
    s.add(SeoAudit(page_id=p.id, issues_json=[]))
    s.commit()
    base = query_audit_results_rows(s, proj.id, limit=10)
    same = query_audit_results_rows(s, proj.id, limit=10, prioritize_page_id=99999)
    assert len(base) == len(same) == 1
    assert base[0][0].id == same[0][0].id
