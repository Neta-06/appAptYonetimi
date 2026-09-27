"""Cari hesap modelleri (tedarikÃƒÂ§i/firma borÃƒÂ§-alacak)."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CariIslemTipi(Base):
    __tablename__ = "cari_islem_tipi"
    tip_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)


class CariHesap(Base):
    __tablename__ = "cari_hesap"
    cari_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("site.site_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    unvan: Mapped[str] = mapped_column(String(150), nullable=False)
    vergi_no: Mapped[str | None] = mapped_column(String(20), nullable=True)
    telefon: Mapped[str | None] = mapped_column(String(15), nullable=True)
    e_posta: Mapped[str | None] = mapped_column(String(100), nullable=True)
    adres: Mapped[str | None] = mapped_column(String(255), nullable=True)
    iban: Mapped[str | None] = mapped_column(String(34), nullable=True)
    aktif_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    olusturma_tarihi: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    __table_args__ = (Index("idx_cari_site_aktif", "site_no", "aktif_mi"),)


class CariHareket(Base):
    __tablename__ = "cari_hareket"
    hareket_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cari_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("cari_hesap.cari_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    hareket_tarihi: Mapped[date] = mapped_column(Date, nullable=False)
    islem_tipi_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("cari_islem_tipi.tip_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    tutar: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    aciklama: Mapped[str | None] = mapped_column(String(255), nullable=True)
    belge_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gider_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    odeme_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    olusturan_no: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("kullanici.kullanici_no", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    olusturma_tarihi: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    __table_args__ = (Index("idx_ch_cari_tarih", "cari_no", "hareket_tarihi"),)