"""Aidat, ödeme ve ilgili lookup modelleri."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CHAR,
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


# ============================================================
# Lookup tablolar
# ============================================================

class AidatTipi(Base):
    __tablename__ = "aidat_tipi"
    tip_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    aciklama: Mapped[str | None] = mapped_column(String(255), nullable=True)
    periyodik_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class OdemeKanali(Base):
    __tablename__ = "odeme_kanali"
    kanal_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)


class OnayDurum(Base):
    __tablename__ = "onay_durum"
    durum_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)


# ============================================================
# Site aidat ayarları
# ============================================================

class SiteAidatAyari(Base):
    __tablename__ = "site_aidat_ayari"
    ayar_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("site.site_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    aidat_tipi_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("aidat_tipi.tip_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    tutar: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    aktif_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    baslangic_tarihi: Mapped[date] = mapped_column(Date, nullable=False)
    bitis_tarihi: Mapped[date | None] = mapped_column(Date, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "site_no", "aidat_tipi_no", "baslangic_tarihi",
            name="uq_site_aidat_ayari"
        ),
    )


# ============================================================
# Aidat
# ============================================================

class Aidat(Base, TimestampMixin):
    __tablename__ = "aidat"
    aidat_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("site.site_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    daire_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("daire.daire_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    aidat_tipi_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("aidat_tipi.tip_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    donem_yil: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    donem_ay: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    tutar: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    odenen_tutar: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    son_odeme_tarihi: Mapped[date] = mapped_column(Date, nullable=False)
    durum: Mapped[str] = mapped_column(
        String(20), nullable=False, default="BEKLIYOR"
    )
    otomatik_islendi_mi: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    aidat_tipi: Mapped["AidatTipi"] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "daire_no", "donem_yil", "donem_ay", "aidat_tipi_no",
            name="uq_aidat_daire_donem_tip"
        ),
        Index("idx_aidat_site_donem", "site_no", "donem_yil", "donem_ay"),
        Index("idx_aidat_site_durum", "site_no", "durum"),
        Index("idx_aidat_daire_durum", "daire_no", "durum"),
        Index("idx_aidat_son_odeme", "son_odeme_tarihi", "durum"),
    )


# ============================================================
# Ödeme
# ============================================================

class Odeme(Base, TimestampMixin):
    __tablename__ = "odeme"
    odeme_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("site.site_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    odeme_tarihi: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    toplam_tutar: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    odeme_kanali_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("odeme_kanali.kanal_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    dekont_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    referans_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    onay_durum_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("onay_durum.durum_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False, default=1,
    )
    onaylayan_no: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("kullanici.kullanici_no", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    onay_tarihi: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    aciklama: Mapped[str | None] = mapped_column(String(255), nullable=True)
    olusturan_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("kullanici.kullanici_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )

    odeme_kanali: Mapped["OdemeKanali"] = relationship()
    onay_durum: Mapped["OnayDurum"] = relationship()
    detaylar: Mapped[list["OdemeDetay"]] = relationship(
        back_populates="odeme", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_odeme_site_tarih", "site_no", "odeme_tarihi"),
        Index("idx_odeme_onay", "onay_durum_no", "odeme_tarihi"),
    )


class OdemeDetay(Base):
    __tablename__ = "odeme_detay"
    detay_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    odeme_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("odeme.odeme_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    aidat_no: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("aidat.aidat_no", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    gider_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tutar: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    aciklama: Mapped[str | None] = mapped_column(String(255), nullable=True)

    odeme: Mapped["Odeme"] = relationship(back_populates="detaylar")

    __table_args__ = (
        Index("idx_od_detay_odeme", "odeme_no"),
        Index("idx_od_detay_aidat", "aidat_no"),
    )