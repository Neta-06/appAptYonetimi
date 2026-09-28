"""Toplantı modelleri."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
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


class Toplanti(Base):
    __tablename__ = "toplanti"

    toplanti_no: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    site_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("site.site_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    baslik: Mapped[str] = mapped_column(String(150), nullable=False)
    aciklama: Mapped[str | None] = mapped_column(Text, nullable=True)
    toplanti_tarihi: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    yer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    olusturan_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("kullanici.kullanici_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    durum: Mapped[str] = mapped_column(
        Enum("PLANLANDI", "YAPILDI", "IPTAL", name="toplanti_durum_enum"),
        nullable=False,
        default="PLANLANDI",
    )

    katilimcilar: Mapped[list["ToplantiKatilimci"]] = relationship(
        back_populates="toplanti", cascade="all, delete-orphan"
    )
    kararlar: Mapped[list["ToplantiKarar"]] = relationship(
        back_populates="toplanti", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_toplanti_site_tarih", "site_no", "toplanti_tarihi"),
    )


class ToplantiKatilimci(Base):
    __tablename__ = "toplanti_katilimci"

    katilim_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    toplanti_no: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("toplanti.toplanti_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    kullanici_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("kullanici.kullanici_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    katildi_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    vekalet_kullanici_no: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("kullanici.kullanici_no", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )

    toplanti: Mapped["Toplanti"] = relationship(back_populates="katilimcilar")

    __table_args__ = (
        UniqueConstraint("toplanti_no", "kullanici_no", name="uq_toplanti_katilimci"),
    )


class ToplantiKarar(Base):
    __tablename__ = "toplanti_karar"

    karar_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    toplanti_no: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("toplanti.toplanti_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    karar_metni: Mapped[str] = mapped_column(Text, nullable=False)
    karar_tarihi: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    toplanti: Mapped["Toplanti"] = relationship(back_populates="kararlar")