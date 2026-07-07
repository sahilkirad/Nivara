from app.db.session import Base, engine
from app.models import context  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)