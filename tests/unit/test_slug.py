from pathlib import Path

from sqlalchemy.orm import sessionmaker

from crawlix.db.models import Project
from crawlix.db.session import init_db, make_engine
from crawlix.utils.slug import slugify, unique_project_slug


def test_slugify_strips_and_hyphenates() -> None:
    assert slugify("Hello  World!!") == "hello-world"


def test_unique_project_slug_collision(tmp_path: Path) -> None:
    db = tmp_path / "s.db"
    engine = make_engine(db)
    init_db(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    s = Session()
    try:
        s.add(Project(name="T", slug="acme", default_domain="acme.com"))
        s.commit()
        assert unique_project_slug(s, "ACME!!") == "acme-1"
    finally:
        s.close()
