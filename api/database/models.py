from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    packages: Mapped[list["Package"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Package(Base):
    __tablename__ = "packages"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(
    String(255),
    nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    manifest: Mapped[list] = mapped_column(
        JSON,
        nullable=False
    )

    merkle_root: Mapped[str] = mapped_column(
        String(64),
        nullable=False
    )

    user: Mapped["User"] = relationship(
        back_populates="packages"
    )

