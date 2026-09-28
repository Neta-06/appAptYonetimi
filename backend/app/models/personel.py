"""Personel, izin, puantaj ve maaş modelleri."""

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CHAR,
    Computed,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Personel(Base):
    __tablename__ = "personel"

    personel_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    firma_no: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("yonetim_firmasi.firma_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    kullanici_no: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("kullanici.kullanici_no", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    ad: Mapped[str] = mapped_column(String(50), nullable=False)
    soyad: Mapped[str] = mapped_column(String(50), nullable=False)
    gorevi: Mapped[str] = mapped_column(String(50), nullable=False)
    telefon: Mapped[str | None] = mapped_column(String(15), nullable=True)
    e_posta: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tc_kimlik_sifreli: Mapped[bytes | None] = mapped_column(
        LargeBinary(128), nullable=True
    )
    ise_baslama_tarihi: Mapped[date] = mapped_column(Date, nullable=False)
    isten_cikis_tarihi: Mapped[date | None] = mapped_column(Date, nullable=True)
    aktif_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    siteler: Mapped[list["PersonelSite"]] = relationship(
        back_populates="personel", cascade="all, delete-orphan"
    )
    izinler: Mapped[list["PersonelIzin"]] = relationship(
        back_populates="personel", cascade="all, delete-orphan"
    )
    puantajlar: Mapped[list["PersonelPuantaj"]] = relationship(
        back_populates="personel", cascade="all, delete-orphan"
    )
    maas_odemeleri: Mapped[list["PersonelMaasOdeme"]] = relationship(
        back_populates="personel", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_personel_firma_aktif", "firma_no", "aktif_mi"),
    )


class PersonelSite(Base):
    __tablename__ = "personel_site"

    kayit_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    personel_no: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("personel.personel_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    site_no: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("site.site_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    baslangic_tarihi: Mapped[date] = mapped_column(Date, nullable=False)
    bitis_tarihi: Mapped[date | None] = mapped_column(Date, nullable=True)

    personel: Mapped["Personel"] = relationship(back_populates="siteler")

    __table_args__ = (
        UniqueConstraint(
            "personel_no", "site_no", "baslangic_tarihi",
            name="uq_personel_site_baslangic",
        ),
    )


class PersonelIzin(Base):
    __tablename__ = "personel_izin"

    izin_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    personel_no: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("personel.personel_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    izin_tipi: Mapped[str] = mapped_column(
        Enum(
            "YILLIK", "RAPOR", "MAZERET", "UCRETSIZ", "DOGUM", "EVLILIK",
            name="personel_izin_tipi_enum",
        ),
        nullable=False,
    )
    baslangic_tarihi: Mapped[date] = mapped_column(Date, nullable=False)
    bitis_tarihi: Mapped[date] = mapped_column(Date, nullable=False)
    gun_sayisi: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    aciklama: Mapped[str | None] = mapped_column(String(255), nullable=True)
    onaylayan_no: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("kullanici.kullanici_no", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    onay_durum_no: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("onay_durum.durum_no", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        default=2,
    )
    olusturma_tarihi: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    personel: Mapped["Personel"] = relationship(back_populates="izinler")

    __table_args__ = (
        Index("idx_pi_personel_tarih", "personel_no", "baslangic_tarihi"),
    )


class PersonelPuantaj(Base):
    __tablename__ = "personel_puantaj"

    puantaj_no: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    personel_no: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("personel.personel_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    tarih: Mapped[date] = mapped_column(Date, nullable=False)
    giris_saati: Mapped[time | None] = mapped_column(nullable=True)
    cikis_saati: Mapped[time | None] = mapped_column(nullable=True)
    toplam_saat: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    devamsiz_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    aciklama: Mapped[str | None] = mapped_column(String(255), nullable=True)

    personel: Mapped["Personel"] = relationship(back_populates="puantajlar")

    __table_args__ = (
        UniqueConstraint("personel_no", "tarih", name="uq_puantaj_personel_tarih"),
    )


class PersonelMaasOdeme(Base):
    __tablename__ = "personel_maas_odeme"

    maas_odeme_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    personel_no: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("personel.personel_no", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    donem_yil: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    donem_ay: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    brut_maas: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    kesintiler: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    net_maas: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        Computed("brut_maas - kesintiler", persisted=True),
        nullable=True,
        comment="GENERATED: brut_maas - kesintiler",
    )
    odeme_tarihi: Mapped[date | None] = mapped_column(Date, nullable=True)

    personel: Mapped["Personel"] = relationship(back_populates="maas_odemeleri")

    __table_args__ = (
        UniqueConstraint(
            "personel_no", "donem_yil", "donem_ay",
            name="uq_maas_personel_donem",
        ),
    )