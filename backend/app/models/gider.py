"""Gider ve gelir modelleri."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class GiderKategori(Base):
    __tablename__ = "gider_kategori"
    kategori_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)


class GiderKalemi(Base):
    __tablename__ = "gider_kalemi"
    kalem_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kalem_adi: Mapped[str] = mapped_column(String(100), nullable=False)
    kategori_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("gider_kategori.kategori_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )

    kategori: Mapped["GiderKategori"] = relationship()

    __table_args__ = (
        UniqueConstraint("kalem_adi", "kategori_no", name="uq_kalem_kategori"),
    )


class Gider(Base, TimestampMixin):
    __tablename__ = "gider"
    gider_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("site.site_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    kalem_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("gider_kalemi.kalem_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    cari_no: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("cari_hesap.cari_no", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    tutar: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    kdv_tutar: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )
    gider_tarihi: Mapped[date] = mapped_column(Date, nullable=False)
    belge_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    aciklama: Mapped[str | None] = mapped_column(String(255), nullable=True)
    kaydeden_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("kullanici.kullanici_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )

    kalem: Mapped["GiderKalemi"] = relationship()

    __table_args__ = (
        Index("idx_gider_site_tarih", "site_no", "gider_tarihi"),
        Index("idx_gider_site_kalem_tarih", "site_no", "kalem_no", "gider_tarihi"),
    )


class Gelir(Base):
    __tablename__ = "gelir"
    gelir_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("site.site_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    kaynak: Mapped[str] = mapped_column(String(100), nullable=False)
    tutar: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    gelir_tarihi: Mapped[date] = mapped_column(Date, nullable=False)
    aciklama: Mapped[str | None] = mapped_column(String(255), nullable=True)
    kaydeden_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("kullanici.kullanici_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    olusturma_tarihi: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    __table_args__ = (Index("idx_gelir_site_tarih", "site_no", "gelir_tarihi"),)