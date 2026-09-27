"""
Kimlik doğrulama iş mantığı.

Görevler:
  - Kayıt (register)
  - Giriş (login + parola doğrulama + login denemesi kaydı)
  - Token üretimi (access + refresh + oturum kaydı)
  - Token yenileme (refresh)
  - Çıkış (logout)
  - Şifre değiştirme
  - Şifre sıfırlama talebi ve uygulaması

Bu modül HTTP'yi bilmez; sadece iş kurallarını uygular.
"""

import logging
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    BulunamadiHatasi,
    CakismaHatasi,
    HesapKilitliHatasi,
    IsKuraliHatasi,
    KimlikDogrulanmadiHatasi,
    TokenGecersizHatasi,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    encrypt_field,
    generate_url_safe_token,
    hash_password,
    hash_token,
    sha256_hash,
    verify_password,
)
from app.core.utils import ip_to_bytes, now_utc_naive
from app.models import (
    Kullanici,
    KvkkMetin,
    KvkkOnay,
    LoginDenemesi,
    Oturum,
    ParolaSifirlamaToken,
)
from app.schemas.auth import (
    KullaniciRegisterRequest,
    TokenResponse,
)

logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Sabitler
# ------------------------------------------------------------
MAX_BASARISIZ_GIRIS = 5         # Bu sayıdan sonra hesap kilitlenir
KILIT_SURESI_DAKIKA = 15        # Kilit ne kadar sürer
SIFRE_SIFIRLAMA_SURESI_DAKIKA = 30  # Token geçerlilik süresi


# ============================================================
# YARDIMCI: Login denemesi kaydı
# ============================================================

async def _log_login_denemesi(
    db: AsyncSession,
    *,
    e_posta: str | None,
    kullanici_no: int | None,
    ip_adresi: str | None,
    user_agent: str | None,
    basarili_mi: bool,
    hata_mesaji: str | None = None,
) -> None:
    """Her login denemesini kayıt altına alır (brute-force tespiti)."""
    deneme = LoginDenemesi(
        e_posta=e_posta,
        kullanici_no=kullanici_no,
        ip_adresi=ip_to_bytes(ip_adresi) or b"",
        user_agent=(user_agent or "")[:255] or None,
        basarili_mi=basarili_mi,
        hata_mesaji=(hata_mesaji or "")[:100] or None,
        deneme_tarihi=now_utc_naive(),
    )
    db.add(deneme)


# ============================================================
# KAYIT (REGISTER)
# ============================================================

async def register_user(
    db: AsyncSession,
    data: KullaniciRegisterRequest,
    *,
    ip_adresi: str | None = None,
    user_agent: str | None = None,
) -> Kullanici:
    """
    Yeni kullanıcı kaydı.

    Adımlar:
      1. E-posta zaten var mı?
      2. Parola hash'le (Argon2id)
      3. Telefon şifrele (AES-256-GCM)
      4. Kullanıcı kaydı oluştur
      5. Aktif KVKK metnini bul ve onay kaydı ekle
      6. Commit

    Raises:
        CakismaHatasi: E-posta zaten kayıtlı.
        IsKuraliHatasi: Aktif KVKK metni yok.
    """
    # 1) E-posta çakışması
    mevcut = await db.execute(
        select(Kullanici.kullanici_no).where(Kullanici.e_posta == data.e_posta)
    )
    if mevcut.scalar_one_or_none() is not None:
        raise CakismaHatasi(alan="e_posta", deger=data.e_posta)

    # 2) Parola hash
    sifre_hash = hash_password(data.parola)

    # 3) Telefon şifrele
    telefon_sifreli = None
    if data.telefon:
        telefon_sifreli = encrypt_field(data.telefon)

    # 4) Kullanıcı oluştur
    kullanici = Kullanici(
        ad=data.ad,
        soyad=data.soyad,
        e_posta=data.e_posta,
        telefon_sifreli=telefon_sifreli,
        sifre_hash=sifre_hash,
        aktif_mi=True,
        mfa_aktif_mi=False,
        basarisiz_giris_sayisi=0,
        hesap_kilitli_mi=False,
    )
    db.add(kullanici)

    try:
        await db.flush()  # kullanici_no üretilsin
    except IntegrityError as exc:
        await db.rollback()
        raise CakismaHatasi(alan="e_posta", deger=data.e_posta) from exc

    # 5) KVKK onay kaydı
    kvkk_sonuc = await db.execute(
        select(KvkkMetin).where(KvkkMetin.aktif_mi.is_(True)).order_by(
            KvkkMetin.yayin_tarihi.desc()
        ).limit(1)
    )
    kvkk = kvkk_sonuc.scalar_one_or_none()
    if kvkk is None:
        raise IsKuraliHatasi(
            "Sistemde aktif KVKK metni bulunamadi. Lutfen yonetime basvurun."
        )

    onay = KvkkOnay(
        kullanici_no=kullanici.kullanici_no,
        metin_no=kvkk.metin_no,
        onay_tipi="AYDINLATMA",
        onaylandi_mi=True,
        onay_tarihi=now_utc_naive(),
        ip_adresi=ip_to_bytes(ip_adresi),
    )
    db.add(onay)

    # 6) Login denemesi kaydı (başarılı kayıt)
    await _log_login_denemesi(
        db,
        e_posta=data.e_posta,
        kullanici_no=kullanici.kullanici_no,
        ip_adresi=ip_adresi,
        user_agent=user_agent,
        basarili_mi=True,
        hata_mesaji="KAYIT",
    )

    await db.commit()
    await db.refresh(kullanici)

    logger.info(
        "Yeni kullanici kaydi: no=%s email=%s",
        kullanici.kullanici_no, kullanici.e_posta,
    )
    return kullanici


# ============================================================
# GİRİŞ (LOGIN)
# ============================================================

async def authenticate_user(
    db: AsyncSession,
    *,
    e_posta: str,
    parola: str,
    ip_adresi: str | None = None,
    user_agent: str | None = None,
) -> Kullanici:
    """
    E-posta + parola doğrular.

    Adımlar:
      1. Kullanıcıyı bul
      2. Hesap kilitli mi kontrol et
      3. Parola doğrula
      4. Başarısızsa sayacı artır
      5. Başarılıysa sayacı sıfırla, son giriş tarihini güncelle
      6. Her denemeyi LoginDenemesi'ne yaz

    Raises:
        KimlikDogrulanmadiHatasi: Kullanıcı yok veya parola yanlış.
        HesapKilitliHatasi: Çok fazla başarısız deneme.
    """
    # 1) Kullanıcıyı bul
    sonuc = await db.execute(
        select(Kullanici).where(Kullanici.e_posta == e_posta)
    )
    kullanici = sonuc.scalar_one_or_none()

    # Kullanıcı yoksa: aynı hatayı dön (user enumeration'ı önle)
    if kullanici is None:
        await _log_login_denemesi(
            db, e_posta=e_posta, kullanici_no=None,
            ip_adresi=ip_adresi, user_agent=user_agent,
            basarili_mi=False, hata_mesaji="KULLANICI_YOK",
        )
        await db.commit()
        raise KimlikDogrulanmadiHatasi("E-posta veya parola hatali.")

    # 2) Hesap kilitli mi?
    if kullanici.hesap_kilitli_mi:
        if kullanici.kilit_acilma_tarihi and kullanici.kilit_acilma_tarihi > now_utc_naive():
            await _log_login_denemesi(
                db, e_posta=e_posta, kullanici_no=kullanici.kullanici_no,
                ip_adresi=ip_adresi, user_agent=user_agent,
                basarili_mi=False, hata_mesaji="HESAP_KILITLI",
            )
            await db.commit()
            raise HesapKilitliHatasi(
                f"Hesabiniz kilitli. Kilit acilma: {kullanici.kilit_acilma_tarihi}"
            )
        else:
            # Kilit süresi dolmuş, aç
            kullanici.hesap_kilitli_mi = False
            kullanici.kilit_acilma_tarihi = None
            kullanici.basarisiz_giris_sayisi = 0

    # 3) Parola doğrula
    if not verify_password(parola, kullanici.sifre_hash):
        kullanici.basarisiz_giris_sayisi += 1
        hata = "PAROLA_YANLIS"

        # Kilit kontrolü
        if kullanici.basarisiz_giris_sayisi >= MAX_BASARISIZ_GIRIS:
            kullanici.hesap_kilitli_mi = True
            kullanici.kilit_acilma_tarihi = (
                now_utc_naive() + timedelta(minutes=KILIT_SURESI_DAKIKA)
            )
            hata = "KILITLENDI"
            logger.warning(
                "Hesap kilitlendi: no=%s email=%s",
                kullanici.kullanici_no, kullanici.e_posta,
            )

        await _log_login_denemesi(
            db, e_posta=e_posta, kullanici_no=kullanici.kullanici_no,
            ip_adresi=ip_adresi, user_agent=user_agent,
            basarili_mi=False, hata_mesaji=hata,
        )
        await db.commit()
        raise KimlikDogrulanmadiHatasi("E-posta veya parola hatali.")

    # 4) Aktif mi?
    if not kullanici.aktif_mi:
        await _log_login_denemesi(
            db, e_posta=e_posta, kullanici_no=kullanici.kullanici_no,
            ip_adresi=ip_adresi, user_agent=user_agent,
            basarili_mi=False, hata_mesaji="PASIF",
        )
        await db.commit()
        raise KimlikDogrulanmadiHatasi("Hesabiniz aktif degil.")

    # 5) Başarılı — sayacı sıfırla
    kullanici.basarisiz_giris_sayisi = 0
    kullanici.hesap_kilitli_mi = False
    kullanici.kilit_acilma_tarihi = None
    kullanici.son_giris_tarihi = now_utc_naive()

    await _log_login_denemesi(
        db, e_posta=e_posta, kullanici_no=kullanici.kullanici_no,
        ip_adresi=ip_adresi, user_agent=user_agent,
        basarili_mi=True, hata_mesaji=None,
    )

    await db.commit()
    await db.refresh(kullanici)

    logger.info("Basarili giris: no=%s", kullanici.kullanici_no)
    return kullanici


# ============================================================
# TOKEN ÜRETİMİ
# ============================================================

async def create_tokens(
    db: AsyncSession,
    kullanici: Kullanici,
    *,
    ip_adresi: str | None = None,
    user_agent: str | None = None,
) -> TokenResponse:
    """
    Access + refresh token üretir ve oturumu kaydeder.

    Refresh token'ın kendisi DB'ye YAZILMAZ.
    Sadece SHA-256 hash'i saklanır (çalınırsa kötüye kullanılamasın).
    """
    access = create_access_token(kullanici.kullanici_no)
    refresh = create_refresh_token(kullanici.kullanici_no)
    refresh_hash = hash_token(refresh)

    oturum = Oturum(
        kullanici_no=kullanici.kullanici_no,
        refresh_token_hash=refresh_hash,
        ip_adresi=ip_to_bytes(ip_adresi),
        user_agent=(user_agent or "")[:255] or None,
        olusturma_tarihi=now_utc_naive(),
        son_kullanma_tarihi=(
            now_utc_naive() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        ),
        iptal_mi=False,
    )
    db.add(oturum)
    await db.commit()

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ============================================================
# TOKEN YENİLEME (REFRESH)
# ============================================================

async def refresh_tokens(
    db: AsyncSession,
    refresh_token: str,
    *,
    ip_adresi: str | None = None,
    user_agent: str | None = None,
) -> TokenResponse:
    """
    Refresh token'ı doğrular, yeni access + refresh üretir.

    Rotasyon stratejisi: Eski refresh token iptal edilir, yeni üretilir.
    (Refresh token rotation — OAuth 2.0 Best Current Practice)
    """
    try:
        payload = decode_refresh_token(refresh_token)
    except Exception as exc:
        raise TokenGecersizHatasi("Refresh token gecersiz.") from exc

    kullanici_no = int(payload["sub"])
    token_hash = hash_token(refresh_token)

    # Oturumu bul
    sonuc = await db.execute(
        select(Oturum).where(Oturum.refresh_token_hash == token_hash)
    )
    oturum = sonuc.scalar_one_or_none()

    if oturum is None:
        raise TokenGecersizHatasi("Oturum bulunamadi.")

    if oturum.iptal_mi:
        raise TokenGecersizHatasi("Oturum iptal edilmis.")

    if oturum.son_kullanma_tarihi < now_utc_naive():
        oturum.iptal_mi = True
        await db.commit()
        raise TokenGecersizHatasi("Refresh token suresi dolmus.")

    # Kullanıcıyı yükle
    kullanici = await db.get(Kullanici, kullanici_no)
    if kullanici is None or not kullanici.aktif_mi:
        raise KimlikDogrulanmadiHatasi("Kullanici aktif degil.")

    # Eski oturumu iptal et (rotation)
    oturum.iptal_mi = True
    oturum.iptal_tarihi = now_utc_naive()

    # Yeni token üret
    return await create_tokens(
        db, kullanici, ip_adresi=ip_adresi, user_agent=user_agent
    )


# ============================================================
# ÇIKIŞ (LOGOUT)
# ============================================================

async def logout_user(
    db: AsyncSession,
    *,
    refresh_token: str,
) -> None:
    """
    Oturumu iptal eder. Token DB'de bulunamazsa hata verir.
    Zaten iptal edilmişse sessizce geçer (idempotent).
    """
    token_hash = hash_token(refresh_token)
    sonuc = await db.execute(
        select(Oturum).where(Oturum.refresh_token_hash == token_hash)
    )
    oturum = sonuc.scalar_one_or_none()

    if oturum is None:
        raise TokenGecersizHatasi("Oturum bulunamadi.")

    if oturum.iptal_mi:
        logger.info("Zaten iptal edilmis oturum: %s", oturum.oturum_no)
        return

    oturum.iptal_mi = True
    oturum.iptal_tarihi = now_utc_naive()
    await db.commit()
    logger.info(
        "Cikis: kullanici_no=%s oturum_no=%s",
        oturum.kullanici_no, oturum.oturum_no,
    )
# ============================================================
# ŞİFRE DEĞİŞTİRME
# ============================================================

async def change_password(
    db: AsyncSession,
    kullanici: Kullanici,
    *,
    eski_parola: str,
    yeni_parola: str,
) -> None:
    """
    Kullanıcının parolasını değiştirir.
    Eski parolayı doğrular, tüm aktif oturumları iptal eder.
    """
    if not verify_password(eski_parola, kullanici.sifre_hash):
        raise KimlikDogrulanmadiHatasi("Eski parola hatali.")

    if verify_password(yeni_parola, kullanici.sifre_hash):
        raise IsKuraliHatasi("Yeni parola eskisiyle ayni olamaz.")

    kullanici.sifre_hash = hash_password(yeni_parola)
    kullanici.sifre_degistirme_tarihi = now_utc_naive()
    kullanici.sifre_hatirlatma_zorunlu = False

    # Güvenlik: tüm oturumları iptal et
    await db.execute(
        update(Oturum)
        .where(Oturum.kullanici_no == kullanici.kullanici_no, Oturum.iptal_mi.is_(False))
        .values(iptal_mi=True, iptal_tarihi=now_utc_naive())
    )

    await db.commit()
    logger.info("Parola degistirildi: kullanici_no=%s", kullanici.kullanici_no)


# ============================================================
# ŞİFRE SIFIRLAMA
# ============================================================

async def request_password_reset(
    db: AsyncSession,
    *,
    e_posta: str,
    ip_adresi: str | None = None,
) -> str | None:
    """
    Şifre sıfırlama token'ı üretir.

    Güvenlik: E-posta kayıtlı değilse de hata vermeyiz, sessizce None döneriz.
    (User enumeration önleme — saldırgan hangi e-postaların kayıtlı olduğunu
    öğrenemesin diye.)

    Döner: Token (varsa) — endpoint bunu e-posta ile gönderir.
    """
    sonuc = await db.execute(
        select(Kullanici).where(Kullanici.e_posta == e_posta)
    )
    kullanici = sonuc.scalar_one_or_none()

    if kullanici is None or not kullanici.aktif_mi:
        return None

    # Yeni token üret
    plain_token = generate_url_safe_token(32)
    token_hash = hash_token(plain_token)

    # Önceki aktif token'ları iptal et
    await db.execute(
        update(ParolaSifirlamaToken)
        .where(
            ParolaSifirlamaToken.kullanici_no == kullanici.kullanici_no,
            ParolaSifirlamaToken.kullanildi_mi.is_(False),
        )
        .values(kullanildi_mi=True, kullanilma_tarihi=now_utc_naive())
    )

    yeni_token = ParolaSifirlamaToken(
        kullanici_no=kullanici.kullanici_no,
        token_hash=token_hash,
        son_kullanma_tarihi=(
            now_utc_naive() + timedelta(minutes=SIFRE_SIFIRLAMA_SURESI_DAKIKA)
        ),
        kullanildi_mi=False,
        ip_adresi=ip_to_bytes(ip_adresi),
        olusturma_tarihi=now_utc_naive(),
    )
    db.add(yeni_token)
    await db.commit()

    logger.info("Sifre sifirlama talebi: kullanici_no=%s", kullanici.kullanici_no)
    return plain_token


async def reset_password(
    db: AsyncSession,
    *,
    token: str,
    yeni_parola: str,
) -> None:
    """
    Token ile parolayı sıfırlar. Token tek kullanımlıktır.
    Başarılı sıfırlama sonrası tüm oturumlar iptal edilir.
    """
    token_hash = hash_token(token)
    sonuc = await db.execute(
        select(ParolaSifirlamaToken).where(
            ParolaSifirlamaToken.token_hash == token_hash
        )
    )
    kayit = sonuc.scalar_one_or_none()

    if kayit is None:
        raise TokenGecersizHatasi("Sifre sifirlama tokeni gecersiz.")

    if kayit.kullanildi_mi:
        raise TokenGecersizHatasi("Bu token zaten kullanilmis.")

    if kayit.son_kullanma_tarihi < now_utc_naive():
        raise TokenGecersizHatasi("Token suresi dolmus.")

    kullanici = await db.get(Kullanici, kayit.kullanici_no)
    if kullanici is None:
        raise BulunamadiHatasi("Kullanici", kaynak_id=kayit.kullanici_no)

    kullanici.sifre_hash = hash_password(yeni_parola)
    kullanici.sifre_degistirme_tarihi = now_utc_naive()
    kullanici.sifre_hatirlatma_zorunlu = False
    kullanici.basarisiz_giris_sayisi = 0
    kullanici.hesap_kilitli_mi = False
    kullanici.kilit_acilma_tarihi = None

    kayit.kullanildi_mi = True
    kayit.kullanilma_tarihi = now_utc_naive()

    # Tüm oturumları iptal et
    await db.execute(
        update(Oturum)
        .where(Oturum.kullanici_no == kullanici.kullanici_no, Oturum.iptal_mi.is_(False))
        .values(iptal_mi=True, iptal_tarihi=now_utc_naive())
    )

    await db.commit()
    logger.info("Parola sifirlandi: kullanici_no=%s", kullanici.kullanici_no)
