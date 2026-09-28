"""Duyuru ve okuma takip modelleri."""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
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


class Duyuru(Base):
    __tablename__ = "duyuru"

    duyuru_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("site.site_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    baslik: Mapped[str] = mapped_column(String(150), nullable=False)
    icerik: Mapped[str] = mapped_column(Text, nullable=False)
    onem_derecesi: Mapped[str] = mapped_column(
        Enum("NORMAL", "ONEMLI", "ACIL", name="duyuru_onem_enum"),
        nullable=False,
        default="NORMAL",
    )
    yayin_tarihi: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    bitis_tarihi: Mapped[date | None] = mapped_column(Date, nullable=True)
    yayinlayan_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("kullanici.kullanici_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )

    okumalar: Mapped[list["DuyuruOkuma"]] = relationship(
        back_populates="duyuru", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_duyuru_site_tarih", "site_no", "yayin_tarihi"),
    )


class DuyuruOkuma(Base):
    __tablename__ = "duyuru_okuma"

    okuma_no: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    duyuru_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("duyuru.duyuru_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    kullanici_no: Mapped[int] = mapped_column(
        Integer, ForeignKey("kullanici.kullanici_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    okuma_tarihi: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    duyuru: Mapped["Duyuru"] = relationship(back_populates="okumalar")

    __table_args__ = (
        UniqueConstraint("duyuru_no", "kullanici_no", name="uq_duyuru_okuma"),
    )