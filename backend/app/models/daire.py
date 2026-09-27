"""Blok, daire ve sakin modelleri."""

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


class DaireTipi(Base):
    __tablename__ = "daire_tipi"
    tip_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    daireler: Mapped[list["Daire"]] = relationship(back_populates="daire_tipi")


class DaireDoluluk(Base):
    __tablename__ = "daire_doluluk"
    doluluk_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    daireler: Mapped[list["Daire"]] = relationship(back_populates="doluluk")


class DaireKullanim(Base):
    __tablename__ = "daire_kullanim"
    kullanim_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)

    daireler: Mapped[list["Daire"]] = relationship(back_populates="kullanim")


class Blok(Base):
    __tablename__ = "blok"
    blok_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("site.site_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    blok_adi: Mapped[str] = mapped_column(String(20), nullable=False)
    kat_sayisi: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=5)
    olusturma_tarihi: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    daireler: Mapped[list["Daire"]] = relationship(back_populates="blok", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("site_no", "blok_adi", name="uq_blok_site_adi"),)


class Daire(Base, TimestampMixin):
    __tablename__ = "daire"
    daire_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("site.site_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    blok_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("blok.blok_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    daire_numarasi: Mapped[str] = mapped_column(String(10), nullable=False)
    kat: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    daire_tipi_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("daire_tipi.tip_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    brut_metrekare: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    ozel_aidat: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    doluluk_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("daire_doluluk.doluluk_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False, default=1,
    )
    kullanim_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("daire_kullanim.kullanim_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False, default=1,
    )

    blok: Mapped["Blok"] = relationship(back_populates="daireler")
    daire_tipi: Mapped["DaireTipi"] = relationship(back_populates="daireler")
    doluluk: Mapped["DaireDoluluk"] = relationship(back_populates="daireler")
    kullanim: Mapped["DaireKullanim"] = relationship(back_populates="daireler")
    sakinler: Mapped[list["DaireSakin"]] = relationship(back_populates="daire", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("blok_no", "daire_numarasi", name="uq_daire_blok_numara"),
        Index("idx_daire_site_doluluk", "site_no", "doluluk_no"),
    )


class DaireSakin(Base, TimestampMixin):
    __tablename__ = "daire_sakin"
    kayit_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    daire_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("daire.daire_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    kullanici_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("kullanici.kullanici_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    mulk_sahibi_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    giris_tarihi: Mapped[date] = mapped_column(Date, nullable=False)
    cikis_tarihi: Mapped[date | None] = mapped_column(Date, nullable=True)

    daire: Mapped["Daire"] = relationship(back_populates="sakinler")

    __table_args__ = (
        Index("idx_ds_daire_aktif", "daire_no", "cikis_tarihi"),
        Index("idx_ds_kullanici_aktif", "kullanici_no", "cikis_tarihi"),
    )