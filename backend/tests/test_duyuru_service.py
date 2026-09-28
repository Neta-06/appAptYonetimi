"""Duyuru servisi doğrudan test."""
import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete
from app.db.session import AsyncSessionLocal
from app.models import Duyuru, DuyuruOkuma
from app.services import duyuru_service


async def main():
    async with AsyncSessionLocal() as db:
        # Temizlik
        await db.execute(delete(DuyuruOkuma))
        await db.execute(delete(Duyuru).where(Duyuru.site_no == 1))
        await db.commit()
        print("[i] Eski test duyurulari temizlendi\n")

        # 1) Yeni duyuru olustur
        print("=" * 60)
        print("1) CREATE DUYURU")
        print("=" * 60)
        d1 = await duyuru_service.create_duyuru(
            db, site_no=1,
            baslik="Su Kesintisi",
            icerik="25 Ekim 09:00-15:00 arasi su kesintisi olacaktir. Lutfen onlem aliniz.",
            yayinlayan_no=11,
            onem_derecesi="ACIL",
            bitis_tarihi=date.today() + timedelta(days=7),
        )
        print(f"  Duyuru #{d1.duyuru_no}: {d1.baslik} (onem={d1.onem_derecesi})")

        d2 = await duyuru_service.create_duyuru(
            db, site_no=1,
            baslik="Asansor Bakimi",
            icerik="Asansor periyodik bakimi 30 Ekim'de yapilacaktir.",
            yayinlayan_no=11,
            onem_derecesi="ONEMLI",
        )
        print(f"  Duyuru #{d2.duyuru_no}: {d2.baslik} (onem={d2.onem_derecesi})")

        # 2) Liste
        print()
        print("=" * 60)
        print("2) LISTE (kullanici=11)")
        print("=" * 60)
        liste = await duyuru_service.list_duyurular(db, site_no=1, kullanici_no=11)
        for d in liste:
            print(f"  [{d['duyuru_no']}] {d['baslik']:25s} onem={d['onem_derecesi']:8s} okundu={d['okundu_mu']}")

        # 3) Detay
        print()
        print("=" * 60)
        print("3) DETAY (kullanici=11)")
        print("=" * 60)
        detay = await duyuru_service.get_duyuru(db, d1.duyuru_no, site_no=1, kullanici_no=11)
        print(f"  Baslik: {detay['baslik']}")
        print(f"  Icerik: {detay['icerik'][:60]}...")
        print(f"  Okundu mu: {detay['okundu_mu']}")
        print(f"  Toplam okuma: {detay['toplam_okuma']}")

        # 4) Okundu isaretle
        print()
        print("=" * 60)
        print("4) OKUNDU ISARETLE (kullanici=11)")
        print("=" * 60)
        sonuc = await duyuru_service.mark_okundu(db, d1.duyuru_no, site_no=1, kullanici_no=11)
        print(f"  Zaten okunmus: {sonuc['zaten_okunmus']}")

        # Idempotency testi
        sonuc2 = await duyuru_service.mark_okundu(db, d1.duyuru_no, site_no=1, kullanici_no=11)
        print(f"  2. cagri - zaten okunmus: {sonuc2['zaten_okunmus']}")

        # Baska kullanici
        await duyuru_service.mark_okundu(db, d1.duyuru_no, site_no=1, kullanici_no=1)

        # 5) Tekrar detay
        print()
        print("=" * 60)
        print("5) DETAY (okundu sonrasi)")
        print("=" * 60)
        detay2 = await duyuru_service.get_duyuru(db, d1.duyuru_no, site_no=1, kullanici_no=11)
        print(f"  Okundu mu: {detay2['okundu_mu']}")
        print(f"  Toplam okuma: {detay2['toplam_okuma']} (2 olmali)")

        # 6) Okuma durumu
        print()
        print("=" * 60)
        print("6) OKUMA DURUMU (yonetici)")
        print("=" * 60)
        durum = await duyuru_service.get_okuma_durumu(db, d1.duyuru_no, site_no=1)
        print(f"  Toplam alici: {durum['toplam_alici']}")
        print(f"  Okuyan: {durum['okuyan_sayisi']}")
        print(f"  Okumayan: {durum['okumayan_sayisi']}")
        print(f"  Oran: {durum['okuma_orani']}%")

        # 7) Guncelle
        print()
        print("=" * 60)
        print("7) GUNCELLE")
        print("=" * 60)
        guncel = await duyuru_service.update_duyuru(
            db, d2.duyuru_no, site_no=1,
            baslik="Asansor Bakimi (Guncellendi)",
            onem_derecesi="ACIL",
        )
        print(f"  Yeni baslik: {guncel.baslik}")
        print(f"  Yeni onem: {guncel.onem_derecesi}")

        # 8) Sil
        print()
        print("=" * 60)
        print("8) SIL")
        print("=" * 60)
        await duyuru_service.delete_duyuru(db, d2.duyuru_no, site_no=1)
        print(f"  Duyuru #{d2.duyuru_no} silindi")

        # Dogrulama
        try:
            await duyuru_service.get_duyuru(db, d2.duyuru_no, site_no=1, kullanici_no=11)
            print("  HATA: hala var!")
        except Exception:
            print("  [OK] Silindi dogrulandi (404)")

        # Temizlik
        await db.execute(delete(DuyuruOkuma))
        await db.execute(delete(Duyuru).where(Duyuru.site_no == 1))
        await db.commit()
        print()
        print("[DONE] Tum testler tamamlandi")


if __name__ == "__main__":
    asyncio.run(main())