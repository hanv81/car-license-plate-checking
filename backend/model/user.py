from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column("id", primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column("username", unique=True)
    password: Mapped[str] = mapped_column("password")
    refresh_token: Mapped[str] = mapped_column("refresh_token")
    user_type: Mapped[int] = mapped_column("user_type", default=1)

class Plate(Base):
    __tablename__ = 'user_plate'

    id: Mapped[int] = mapped_column("id", primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column("username")
    plate: Mapped[str] = mapped_column("plate", unique=True)

class Config(Base):
    __tablename__ = 'config'

    id: Mapped[int] = mapped_column("id", primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("name", unique=True)
    value: Mapped[str] = mapped_column("value")