"""Demirbaş ve zimmet modelleri."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Demirbas(Base):
    __tablename__ = "demirbas"
    demirbas_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("site.site_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    ad: Mapped[str] = mapped_column(String(100), nullable=False)
    kategori: Mapped[str | None] = mapped_column(String(50), nullable=True)
    adet: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    alis_fiyati: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    alis_tarihi: Mapped[date | None] = mapped_column(Date, nullable=True)
    bulundugu_yer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    durum: Mapped[str] = mapped_column(
        Enum("CALISIYOR", "ARIZALI", "HURDA", name="demirbas_durum_enum"),
        nullable=False,
        default="CALISIYOR",
    )

    hareketler: Mapped[list["DemirbasHareket"]] = relationship(
        back_populates="demirbas", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_demirbas_site_durum", "site_no", "durum"),
    )


class DemirbasHareket(Base):
    __tablename__ = "demirbas_hareket"
    hareket_no: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    demirbas_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("demirbas.demirbas_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    hareket_tipi: Mapped[str] = mapped_column(
        Enum(
            "ZIMBET", "BAKIM", "ONARIM", "YER_DEGISIKLIGI", "HURDA",
            name="demirbas_hareket_enum",
        ),
        nullable=False,
    )
    kullanici_no: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("kullanici.kullanici_no", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    tarih: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    aciklama: Mapped[str | None] = mapped_column(String(255), nullable=True)
    maliyet: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    demirbas: Mapped["Demirbas"] = relationship(back_populates="hareketler")