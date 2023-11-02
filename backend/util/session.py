from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from util import config

_, _, dburl = config.read_env()
SessionFactory = sessionmaker(
    bind=create_engine(dburl, echo=True),
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

def create_session() -> Iterator[Session]:
    session = SessionFactory()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()