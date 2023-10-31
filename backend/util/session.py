from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


# create session factory to generate new database sessions
SessionFactory = sessionmaker(
    bind=create_engine('mysql://root:180981@localhost:3306/car-door-plate', echo=True),
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