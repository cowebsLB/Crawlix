from pathlib import Path

from sqlalchemy.orm import sessionmaker

from crawlix.db.models import Project
from crawlix.db.session import init_db, make_engine
from crawlix.ui.controllers_project import project_choices


def test_project_choices_sorted_by_name(tmp_path: Path) -> None:
    db = tmp_path / "project_controller.db"
    engine = make_engine(db)
    init_db(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as s:
        s.add_all(
            [
                Project(name="Zulu", slug="zulu"),
                Project(name="Alpha", slug="alpha"),
                Project(name="Mike", slug="mike"),
            ]
        )
        s.commit()
        rows = project_choices(s)
        assert [name for _pid, name in rows] == ["Alpha", "Mike", "Zulu"]
        assert all(isinstance(pid, int) for pid, _name in rows)
