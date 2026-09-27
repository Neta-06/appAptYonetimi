"""
Merkezi hata yönetimi.

Tüm özel hatalar AppException'dan türer.
main.py'de global exception handler ile HTTP yanıtına çevrilir.
"""

from typing import Any


class AppException(Exception):
    """
    Uygulamaya özel tüm hataların temel sınıfı.

    Kullanım:
        raise BulunamadiHatasi("Site", site_no=5)
        raise YetkiYokHatasi("aidat.sil")
    """

    status_code: int = 500
    kod: str = "INTERNAL_ERROR"
    mesaj: str = "Beklenmeyen bir hata olustu."

    def __init__(
        self,
        mesaj: str | None = None,
        *,
        kod: str | None = None,
        detay: dict[str, Any] | None = None,
    ) -> None:
        self.mesaj = mesaj or self.__class__.mesaj
        self.kod = kod or self.__class__.kod
        self.detay = detay or {}
        super().__init__(self.mesaj)

    def to_dict(self) -> dict[str, Any]:
        """FastAPI JSON yanitina cevrilebilir sozluk."""
        sonuc = {
            "error": self.kod,
            "message": self.mesaj,
        }
        if self.detay:
            sonuc["details"] = self.detay
        return sonuc


# ============================================================
# 400 — İş Kuralı İhlali
# ============================================================

class IsKuraliHatasi(AppException):
    """İş kuralı ihlali. Örn: 'Bu dairede zaten aktif sakin var.'"""
    status_code = 400
    kod = "IS_KURALI_IHLALI"
    mesaj = "Is kurali ihlal edildi."


# ============================================================
# 401 — Kimlik Doğrulanmadı
# ============================================================

class KimlikDogrulanmadiHatasi(AppException):
    """Token yok, geçersiz veya süresi dolmuş."""
    status_code = 401
    kod = "KIMLIK_DOGRULANMADI"
    mesaj = "Kimlik dogrulanmadi. Lutfen giris yapin."


class TokenGecersizHatasi(KimlikDogrulanmadiHatasi):
    """Token geçersiz."""
    kod = "TOKEN_GECERSIZ"
    mesaj = "Oturum tokeni gecersiz."


class TokenSuresiDolmusHatasi(KimlikDogrulanmadiHatasi):
    """Token süresi dolmuş."""
    kod = "TOKEN_SURESI_DOLMUS"
    mesaj = "Oturum suresi dolmus. Lutfen tekrar giris yapin."


class HesapKilitliHatasi(KimlikDogrulanmadiHatasi):
    """Çok fazla başarısız giriş denemesi."""
    kod = "HESAP_KILITLI"
    mesaj = "Hesabiniz gecici olarak kilitlendi."


# ============================================================
# 403 — Yetki Yok
# ============================================================

class YetkiYokHatasi(AppException):
    """Kullanıcının bu işlem için yetkisi yok."""
    status_code = 403
    kod = "YETKI_YOK"
    mesaj = "Bu islem icin yetkiniz yok."


class SiteErisimYokHatasi(YetkiYokHatasi):
    """Kullanıcı bu siteye erişemez."""
    kod = "SITE_ERISIM_YOK"
    mesaj = "Bu siteye erisim yetkiniz yok."


class PasifKullaniciHatasi(YetkiYokHatasi):
    """Kullanıcı pasif durumda."""
    kod = "PASIF_KULLANICI"
    mesaj = "Hesabiniz aktif degil."


# ============================================================
# 404 — Bulunamadı
# ============================================================

class BulunamadiHatasi(AppException):
    """Kayıt bulunamadı."""
    status_code = 404
    kod = "BULUNAMADI"
    mesaj = "Kayit bulunamadi."

    def __init__(
        self,
        kaynak: str = "Kayit",
        *,
        kaynak_id: int | str | None = None,
        kod: str | None = None,
        detay: dict[str, Any] | None = None,
    ) -> None:
        mesaj = f"{kaynak} bulunamadi."
        if kaynak_id is not None:
            mesaj = f"{kaynak} (id={kaynak_id}) bulunamadi."
            detay = {**(detay or {}), "kaynak_id": kaynak_id}
        super().__init__(mesaj, kod=kod, detay=detay)


# ============================================================
# 409 — Çakışma
# ============================================================

class CakismaHatasi(AppException):
    """Unique kısıt ihlali, aynı kayıt zaten var."""
    status_code = 409
    kod = "CAKISMA"
    mesaj = "Bu kayit zaten mevcut."

    def __init__(
        self,
        alan: str | None = None,
        *,
        deger: Any = None,
        kod: str | None = None,
        detay: dict[str, Any] | None = None,
    ) -> None:
        mesaj = self.__class__.mesaj
        if alan:
            mesaj = f"'{alan}' alani zaten kullaniliyor."
            detay = {**(detay or {}), "alan": alan}
            if deger is not None:
                detay["deger"] = str(deger)
        super().__init__(mesaj, kod=kod, detay=detay)


# ============================================================
# 422 — Doğrulama Hatası
# ============================================================

class DogrulamaHatasi(AppException):
    """Pydantic doğrulama hatası (manuel fırlatma için)."""
    status_code = 422
    kod = "DOGRULAMA_HATASI"
    mesaj = "Gonderilen veriler gecersiz."


# ============================================================
# 429 — Hız Sınırı
# ============================================================

class HizSiniriAsildiHatasi(AppException):
    """Rate limit aşıldı."""
    status_code = 429
    kod = "HIZ_SINIRI_ASILDI"
    mesaj = "Cok fazla istek gonderdiniz. Lutfen bekleyin."

    def __init__(
        self,
        *,
        saniye: int | None = None,
        kod: str | None = None,
        detay: dict[str, Any] | None = None,
    ) -> None:
        if saniye:
            detay = {**(detay or {}), "yeniden_deneme_saniye": saniye}
        super().__init__(kod=kod, detay=detay)
