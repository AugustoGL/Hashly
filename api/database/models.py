from datetime import datetime, timezone

from sqlalchemy import (
    DateTime, ForeignKey, Integer, JSON, LargeBinary, String
)
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

    api_keys: Mapped[list["ApiKey"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


class ApiKey(Base):
    __tablename__ = "api_keys"

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
        String(100),
        nullable=False
    )

    # Primeros caracteres de la key, solo para mostrarla en listados
    prefix: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    # SHA-256 de la key completa: la key en sí nunca se guarda
    key_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    user: Mapped["User"] = relationship(
        back_populates="api_keys"
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

    # "ots" (gratis, Bitcoin) o "smart_contract" (NFT, próximamente)
    verification_method: Mapped[str] = mapped_column(
        String(20),
        default="ots",
        server_default="ots",
        nullable=False
    )

    user: Mapped["User"] = relationship(
        back_populates="packages"
    )

    timestamp: Mapped["PackageTimestamp | None"] = relationship(
        back_populates="package",
        uselist=False,
        cascade="all, delete-orphan"
    )


class PackageTimestamp(Base):
    __tablename__ = "package_timestamps"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    package_id: Mapped[int] = mapped_column(
        ForeignKey("packages.id"),
        unique=True,
        nullable=False,
        index=True
    )

    # creating -> pending -> confirmed | failed
    status: Mapped[str] = mapped_column(
        String(20),
        default="creating",
        nullable=False,
        index=True
    )

    ots_proof: Mapped[bytes | None] = mapped_column(
        LargeBinary,
        nullable=True
    )

    bitcoin_block_height: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    error: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    package: Mapped["Package"] = relationship(
        back_populates="timestamp"
    )



class WaitlistEntry(Base):
    __tablename__ = "waitlist"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    # "contrato" (vía NFT, próximamente) o "bitcoin"
    interest: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
