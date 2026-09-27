"""
Kimlik, yetki, site ve güvenlik modelleri.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CHAR, JSON, BigInteger, Boolean, Date, DateTime, Enum,
    ForeignKey, Index, Integer, LargeBinary, Numeric,
    SmallInteger, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Rol(Base):
    __tablename__ = "rol"
    rol_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    aciklama: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sistem_rolu: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    yetkiler: Mapped[list["RolYetki"]] = relationship(back_populates="rol", cascade="all, delete-orphan")
    kullanici_siteleri: Mapped[list["KullaniciSite"]] = relationship(back_populates="rol")


class Yetki(Base):
    __tablename__ = "yetki"
    yetki_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kod: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    ad: Mapped[str] = mapped_column(String(150), nullable=False)
    modul: Mapped[str] = mapped_column(String(50), nullable=False)
    roller: Mapped[list["RolYetki"]] = relationship(back_populates="yetki", cascade="all, delete-orphan")


class RolYetki(Base):
    __tablename__ = "rol_yetki"
    rol_no: Mapped[int] = mapped_column(Integer, ForeignKey("rol.rol_no", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    yetki_no: Mapped[int] = mapped_column(Integer, ForeignKey("yetki.yetki_no", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    rol: Mapped["Rol"] = relationship(back_populates="yetkiler")
    yetki: Mapped["Yetki"] = relationship(back_populates="roller")


class SiteTipi(Base):
    __tablename__ = "site_tipi"
    tip_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    siteler: Mapped[list["Site"]] = relationship(back_populates="site_tipi")


class YonetimFirmasi(Base, TimestampMixin):
    __tablename__ = "yonetim_firmasi"
    firma_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    firma_adi: Mapped[str] = mapped_column(String(150), nullable=False)
    vergi_no: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True)
    adres: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefon: Mapped[str | None] = mapped_column(String(15), nullable=True)
    e_posta: Mapped[str | None] = mapped_column(String(100), nullable=True)
    yetkili_kisi: Mapped[str | None] = mapped_column(String(100), nullable=True)
    aktif_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    siteler: Mapped[list["Site"]] = relationship(back_populates="firma")
    kullanicilar: Mapped[list["Kullanici"]] = relationship(back_populates="firma")


class Site(Base, TimestampMixin):
    __tablename__ = "site"
    site_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    firma_no: Mapped[int] = mapped_column(Integer, ForeignKey("yonetim_firmasi.firma_no", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    site_adi: Mapped[str] = mapped_column(String(150), nullable=False)
    site_tipi_no: Mapped[int] = mapped_column(Integer, ForeignKey("site_tipi.tip_no", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    adres: Mapped[str | None] = mapped_column(String(255), nullable=True)
    il: Mapped[str | None] = mapped_column(String(30), nullable=True)
    ilce: Mapped[str | None] = mapped_column(String(30), nullable=True)
    daire_sayisi: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    aylik_aidat: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    aidat_gunu: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=5)
    otomatik_borclandir: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    aktif_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    firma: Mapped["YonetimFirmasi"] = relationship(back_populates="siteler")
    site_tipi: Mapped["SiteTipi"] = relationship(back_populates="siteler")
    kullanici_siteleri: Mapped[list["KullaniciSite"]] = relationship(back_populates="site", cascade="all, delete-orphan")
    __table_args__ = (Index("idx_site_firma_aktif", "firma_no", "aktif_mi"),)


class Kullanici(Base, TimestampMixin):
    __tablename__ = "kullanici"
    kullanici_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    firma_no: Mapped[int | None] = mapped_column(Integer, ForeignKey("yonetim_firmasi.firma_no", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    ad: Mapped[str] = mapped_column(String(50), nullable=False)
    soyad: Mapped[str] = mapped_column(String(50), nullable=False)
    tc_kimlik_sifreli: Mapped[bytes | None] = mapped_column(LargeBinary(128), nullable=True, unique=True)
    tc_kimlik_hash: Mapped[str | None] = mapped_column(CHAR(64), nullable=True, unique=True)
    telefon_sifreli: Mapped[bytes | None] = mapped_column(LargeBinary(128), nullable=True)
    e_posta: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    sifre_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    sifre_degistirme_tarihi: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sifre_hatirlatma_zorunlu: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mfa_aktif_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mfa_secret_sifreli: Mapped[bytes | None] = mapped_column(LargeBinary(255), nullable=True)
    son_giris_tarihi: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    basarisiz_giris_sayisi: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    hesap_kilitli_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    kilit_acilma_tarihi: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    aktif_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    firma: Mapped["YonetimFirmasi | None"] = relationship(back_populates="kullanicilar")
    kullanici_siteleri: Mapped[list["KullaniciSite"]] = relationship(back_populates="kullanici", cascade="all, delete-orphan")
    mfa_yedek_kodlari: Mapped[list["KullaniciMfaYedekKod"]] = relationship(back_populates="kullanici", cascade="all, delete-orphan")
    oturumlar: Mapped[list["Oturum"]] = relationship(back_populates="kullanici", cascade="all, delete-orphan")
    kvkk_onaylari: Mapped[list["KvkkOnay"]] = relationship(back_populates="kullanici", cascade="all, delete-orphan")
    __table_args__ = (Index("idx_kullanici_aktif", "aktif_mi"), Index("idx_kullanici_firma", "firma_no"))


class KullaniciSite(Base, TimestampMixin):
    __tablename__ = "kullanici_site"
    kayit_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kullanici_no: Mapped[int] = mapped_column(Integer, ForeignKey("kullanici.kullanici_no", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    site_no: Mapped[int] = mapped_column(Integer, ForeignKey("site.site_no", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    rol_no: Mapped[int] = mapped_column(Integer, ForeignKey("rol.rol_no", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    baslangic_tarihi: Mapped[date] = mapped_column(Date, nullable=False)
    bitis_tarihi: Mapped[date | None] = mapped_column(Date, nullable=True)
    aktif_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    kullanici: Mapped["Kullanici"] = relationship(back_populates="kullanici_siteleri")
    site: Mapped["Site"] = relationship(back_populates="kullanici_siteleri")
    rol: Mapped["Rol"] = relationship(back_populates="kullanici_siteleri")
    __table_args__ = (UniqueConstraint("kullanici_no", "site_no", name="uq_ks_kullanici_site"), Index("idx_ks_site_aktif", "site_no", "aktif_mi"), Index("idx_ks_kullanici_aktif", "kullanici_no", "aktif_mi"))


class KullaniciMfaYedekKod(Base):
    __tablename__ = "kullanici_mfa_yedek_kod"
    kod_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kullanici_no: Mapped[int] = mapped_column(Integer, ForeignKey("kullanici.kullanici_no", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    kod_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    kullanildi_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    kullanilma_tarihi: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    kullanici: Mapped["Kullanici"] = relationship(back_populates="mfa_yedek_kodlari")
    __table_args__ = (Index("idx_mfa_kullanici_kullanildi", "kullanici_no", "kullanildi_mi"),)


class Oturum(Base):
    __tablename__ = "oturum"
    oturum_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kullanici_no: Mapped[int] = mapped_column(Integer, ForeignKey("kullanici.kullanici_no", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False, unique=True)
    ip_adresi: Mapped[bytes | None] = mapped_column(LargeBinary(16), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    son_kullanma_tarihi: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    iptal_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    iptal_tarihi: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    kullanici: Mapped["Kullanici"] = relationship(back_populates="oturumlar")
    __table_args__ = (Index("idx_oturum_kullanici_aktif", "kullanici_no", "iptal_mi", "son_kullanma_tarihi"),)


class ParolaSifirlamaToken(Base):
    __tablename__ = "parola_sifirlama_token"
    token_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kullanici_no: Mapped[int] = mapped_column(Integer, ForeignKey("kullanici.kullanici_no", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False, unique=True)
    son_kullanma_tarihi: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    kullanildi_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    kullanilma_tarihi: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ip_adresi: Mapped[bytes | None] = mapped_column(LargeBinary(16), nullable=True)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    __table_args__ = (Index("idx_pst_kullanici_kullanildi", "kullanici_no", "kullanildi_mi"),)


class LoginDenemesi(Base):
    __tablename__ = "login_denemesi"
    deneme_no: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    e_posta: Mapped[str | None] = mapped_column(String(100), nullable=True)
    kullanici_no: Mapped[int | None] = mapped_column(Integer, ForeignKey("kullanici.kullanici_no", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    ip_adresi: Mapped[bytes] = mapped_column(LargeBinary(16), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    basarili_mi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    hata_mesaji: Mapped[str | None] = mapped_column(String(100), nullable=True)
    deneme_tarihi: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    __table_args__ = (Index("idx_ld_email_tarih", "e_posta", "deneme_tarihi"), Index("idx_ld_ip_tarih", "ip_adresi", "deneme_tarihi"))


class AuditLog(Base):
    __tablename__ = "audit_log"
    log_no: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    kullanici_no: Mapped[int | None] = mapped_column(Integer, ForeignKey("kullanici.kullanici_no", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    site_no: Mapped[int | None] = mapped_column(Integer, ForeignKey("site.site_no", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    tablo_adi: Mapped[str] = mapped_column(String(80), nullable=False)
    kayit_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    islem_tipi: Mapped[str] = mapped_column(Enum("INSERT", "UPDATE", "DELETE", "LOGIN", "LOGOUT", "EXPORT", name="audit_islem_tipi_enum"), nullable=False)
    eski_deger: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    yeni_deger: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_adresi: Mapped[bytes | None] = mapped_column(LargeBinary(16), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    islem_tarihi: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    __table_args__ = (Index("idx_al_tablo_kayit", "tablo_adi", "kayit_id"), Index("idx_al_kullanici_tarih", "kullanici_no", "islem_tarihi"), Index("idx_al_site_tarih", "site_no", "islem_tarihi"))


class KvkkMetin(Base):
    __tablename__ = "kvkk_metin"
    metin_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    baslik: Mapped[str] = mapped_column(String(150), nullable=False)
    icerik: Mapped[str] = mapped_column(Text, nullable=False)
    versiyon: Mapped[str] = mapped_column(String(20), nullable=False)
    yayin_tarihi: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    aktif_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    onaylar: Mapped[list["KvkkOnay"]] = relationship(back_populates="metin", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("baslik", "versiyon", name="uq_kvkk_baslik_versiyon"),)


class KvkkOnay(Base):
    __tablename__ = "kvkk_onay"
    onay_no: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kullanici_no: Mapped[int] = mapped_column(Integer, ForeignKey("kullanici.kullanici_no", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    metin_no: Mapped[int] = mapped_column(Integer, ForeignKey("kvkk_metin.metin_no", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    onay_tipi: Mapped[str] = mapped_column(Enum("AYDINLATMA", "ACIK_RIZA", "PAZARLAMA", "CEREZ", name="kvkk_onay_tipi_enum"), nullable=False)
    onaylandi_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    onay_tarihi: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    ip_adresi: Mapped[bytes | None] = mapped_column(LargeBinary(16), nullable=True)
    kullanici: Mapped["Kullanici"] = relationship(back_populates="kvkk_onaylari")
    metin: Mapped["KvkkMetin"] = relationship(back_populates="onaylar")
    __table_args__ = (UniqueConstraint("kullanici_no", "metin_no", "onay_tipi", name="uq_kvkk_kullanici_metin_tip"),)