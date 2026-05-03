from pathlib import Path

from sqlalchemy.orm import sessionmaker

from crawlix.db.models import Page, Project, SeoAudit
from crawlix.db.session import init_db, make_engine
from crawlix.services.exporters import export_pages_csv, export_seo_audits_csv, export_seo_audits_json


def test_export_pages_csv_roundtrip(tmp_path: Path) -> None:
    db = tmp_path / "e.db"
    engine = make_engine(db)
    init_db(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    s = Session()
    try:
        p = Project(name="P", slug="p", default_domain="ex.com")
        s.add(p)
        s.commit()
        s.add(Page(project_id=p.id, url_norm="https://ex.com/", url_final="https://ex.com/", title="Home"))
        s.commit()
        out = tmp_path / "pages.csv"
        n = export_pages_csv(s, p.id, out)
        assert n == 1
        assert "https://ex.com/" in out.read_text(encoding="utf-8")
    finally:
        s.close()


def test_export_audits_json(tmp_path: Path) -> None:
    db = tmp_path / "a.db"
    engine = make_engine(db)
    init_db(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    s = Session()
    try:
        p = Project(name="P", slug="p2", default_domain="ex.com")
        s.add(p)
        s.commit()
        pg = Page(project_id=p.id, url_norm="https://ex.com/a", url_final="https://ex.com/a", title="A")
        s.add(pg)
        s.commit()
        s.add(SeoAudit(page_id=pg.id, overall_score=80.0, issues_json=[{"id": "x"}], category_scores_json={}))
        s.commit()
        jpath = tmp_path / "aud.json"
        export_seo_audits_json(s, p.id, jpath)
        assert "issues_json" in jpath.read_text(encoding="utf-8")
        export_seo_audits_csv(s, p.id, tmp_path / "aud.csv")
    finally:
        s.close()
