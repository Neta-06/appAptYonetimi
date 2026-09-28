"""Anket ve oylama modelleri."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Anket(Base):
    __tablename__ = "anket"

    anket_no: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    site_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("site.site_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    soru: Mapped[str] = mapped_column(String(300), nullable=False)
    aciklama: Mapped[str | None] = mapped_column(String(500), nullable=True)
    baslangic_tarihi: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    bitis_tarihi: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    olusturan_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("kullanici.kullanici_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    aktif_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    secenekler: Mapped[list["AnketSecenegi"]] = relationship(
        back_populates="anket", cascade="all, delete-orphan"
    )
    oy_haklari: Mapped[list["AnketOyHakki"]] = relationship(
        back_populates="anket", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_anket_site_tarih", "site_no", "bitis_tarihi"),
    )


class AnketSecenegi(Base):
    __tablename__ = "anket_secenegi"

    secenek_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    anket_no: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("anket.anket_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    secenek_metni: Mapped[str] = mapped_column(String(200), nullable=False)

    anket: Mapped["Anket"] = relationship(back_populates="secenekler")
    oylar: Mapped[list["AnketOyu"]] = relationship(
        back_populates="secenek", cascade="all, delete-orphan"
    )


class AnketOyHakki(Base):
    __tablename__ = "anket_oy_hakki"

    hak_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    anket_no: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("anket.anket_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    kullanici_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("kullanici.kullanici_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    oy_kullandi_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    anket: Mapped["Anket"] = relationship(back_populates="oy_haklari")

    __table_args__ = (
        UniqueConstraint("anket_no", "kullanici_no", name="uq_anket_oy_hakki"),
    )


class AnketOyu(Base):
    __tablename__ = "anket_oyu"

    oy_no: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    secenek_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("anket_secenegi.secenek_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    kullanici_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("kullanici.kullanici_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    oy_tarihi: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    secenek: Mapped["AnketSecenegi"] = relationship(back_populates="oylar")

    __table_args__ = (
        UniqueConstraint("secenek_no", "kullanici_no", name="uq_anket_oyu"),
    )