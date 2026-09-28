"""İş emri ve takip modelleri."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class IsOncelik(Base):
    __tablename__ = "is_oncelik"

    oncelik_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    siralama: Mapped[int] = mapped_column(SmallInteger, nullable=False)


class IsDurum(Base):
    __tablename__ = "is_durum"

    durum_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    kapanis_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class IsEmri(Base):
    __tablename__ = "is_emri"

    is_no: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    site_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("site.site_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    daire_no: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("daire.daire_no", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    acan_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("kullanici.kullanici_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    atanan_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("kullanici.kullanici_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    baslik: Mapped[str] = mapped_column(String(150), nullable=False)
    aciklama: Mapped[str | None] = mapped_column(Text, nullable=True)
    oncelik_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("is_oncelik.oncelik_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    durum_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("is_durum.durum_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    olusturma_tarihi: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    termin_tarihi: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    tamamlanma_tarihi: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    guncellenme_tarihi: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    oncelik: Mapped["IsOncelik"] = relationship()
    durum: Mapped["IsDurum"] = relationship()
    guncellemeler: Mapped[list["IsEmriGuncelleme"]] = relationship(
        back_populates="is_emri", cascade="all, delete-orphan"
    )
    malzemeler: Mapped[list["IsEmriMalzeme"]] = relationship(
        back_populates="is_emri", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_is_site_durum", "site_no", "durum_no"),
        Index("idx_is_atanan_durum", "atanan_no", "durum_no"),
        Index("idx_is_site_oncelik_durum", "site_no", "oncelik_no", "durum_no"),
    )


class IsEmriGuncelleme(Base):
    __tablename__ = "is_emri_guncelleme"

    guncelleme_no: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    is_no: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("is_emri.is_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    yazan_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("kullanici.kullanici_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    durum_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("is_durum.durum_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    notlar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    guncelleme_tarihi: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    is_emri: Mapped["IsEmri"] = relationship(back_populates="guncellemeler")
    durum: Mapped["IsDurum"] = relationship()


class IsEmriMalzeme(Base):
    __tablename__ = "is_emri_malzeme"

    malzeme_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    is_no: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("is_emri.is_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    ad: Mapped[str] = mapped_column(String(150), nullable=False)
    adet: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=1)
    birim: Mapped[str | None] = mapped_column(String(20), nullable=True)
    birim_fiyat: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    is_emri: Mapped["IsEmri"] = relationship(back_populates="malzemeler")