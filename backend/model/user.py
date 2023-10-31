from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column("id", primary_key=True)
    username: Mapped[str] = mapped_column("username", primary_key=True)
    password: Mapped[str] = mapped_column("password", primary_key=True)
    refresh_token: Mapped[str] = mapped_column("refresh_token", primary_key=True)
    user_type: Mapped[int] = mapped_column("user_type", primary_key=True)