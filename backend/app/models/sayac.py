"""Sayaç modelleri."""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class SayacBirim(Base):
    __tablename__ = "sayac_birim"
    birim_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)


class SayacTuru(Base):
    __tablename__ = "sayac_turu"
    sayac_turu_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    adi: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    birim_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("sayac_birim.birim_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )

    birim: Mapped["SayacBirim"] = relationship()


class DaireSayaci(Base):
    __tablename__ = "daire_sayaci"
    daire_sayac_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    daire_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("daire.daire_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    sayac_turu_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("sayac_turu.sayac_turu_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    seri_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    montaj_tarihi: Mapped[date | None] = mapped_column(Date, nullable=True)
    sokulme_tarihi: Mapped[date | None] = mapped_column(Date, nullable=True)
    ilk_deger: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    aktif_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    sayac_turu: Mapped["SayacTuru"] = relationship()

    __table_args__ = (Index("idx_ds_aktif", "aktif_mi"),)


class SayacOkuma(Base):
    __tablename__ = "sayac_okuma"
    okuma_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    daire_sayac_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("daire_sayaci.daire_sayac_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    okuma_tarihi: Mapped[date] = mapped_column(Date, nullable=False)
    guncel_deger: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    tuketim: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    okuyan_no: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("kullanici.kullanici_no", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    olusturma_tarihi: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    __table_args__ = (
        UniqueConstraint("daire_sayac_no", "okuma_tarihi", name="uq_okuma_sayac_tarih"),
        Index("idx_so_sayac_tarih", "daire_sayac_no", "okuma_tarihi"),
    )


class SayacFaturasi(Base):
    __tablename__ = "sayac_faturasi"
    fatura_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("site.site_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    sayac_turu_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("sayac_turu.sayac_turu_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    donem_yil: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    donem_ay: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    toplam_tutar: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    ortak_alan_tutar: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    dagitim_sekli: Mapped[str] = mapped_column(String(20), nullable=False, default="TUKETIME_GORE")
    olusturma_tarihi: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    __table_args__ = (
        UniqueConstraint("site_no", "sayac_turu_no", "donem_yil", "donem_ay", name="uq_fatura_donem"),
    )


class SayacFaturaPayi(Base):
    __tablename__ = "sayac_fatura_payi"
    pay_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fatura_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("sayac_faturasi.fatura_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    daire_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("daire.daire_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    tuketim: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    daire_tutari: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    aidat_no: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("aidat.aidat_no", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )

    __table_args__ = (UniqueConstraint("fatura_no", "daire_no", name="uq_pay_fatura_daire"),)