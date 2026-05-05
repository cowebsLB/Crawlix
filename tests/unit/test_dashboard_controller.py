from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from crawlix.db.models import Base, Job, Page, Project, SeoAudit
from crawlix.ui.controllers_dashboard import format_dashboard_summary_line, load_dashboard_summary


def test_dashboard_summary_and_formatting() -> None:
    eng = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        p = Project(name="P", slug="p")
        s.add(p)
        s.flush()
        s.add(Page(project_id=p.id, url_norm="https://x.test/", last_crawled_at=datetime.now(UTC)))
        s.add(Job(project_id=p.id, type="crawl", status="completed"))
        s.flush()
        pg = s.query(Page).first()
        assert pg is not None
        s.add(SeoAudit(page_id=pg.id, overall_score=90.0))
        s.commit()
        sm = load_dashboard_summary(s, p.id)
        line = format_dashboard_summary_line(sm)
        assert sm.pages == 1
        assert sm.jobs == 1
        assert sm.audits == 1
        assert "Pages: 1" in line
