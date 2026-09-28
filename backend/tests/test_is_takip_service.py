"""İş emri servisi doğrudan test."""
import asyncio
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete
from app.db.session import AsyncSessionLocal
from app.models import IsEmri, IsEmriGuncelleme, IsEmriMalzeme
from app.services import is_takip_service


async def main():
    async with AsyncSessionLocal() as db:
        # Temizlik
        await db.execute(delete(IsEmriMalzeme))
        await db.execute(delete(IsEmriGuncelleme))
        await db.execute(delete(IsEmri).where(IsEmri.site_no == 1))
        await db.commit()
        print("[i] Eski is emirleri temizlendi\n")

        # 1) Lookup
        print("=" * 60)
        print("1) LOOKUP")
        print("=" * 60)
        oncelikler = await is_takip_service.list_oncelikler(db)
        for o in oncelikler:
            print(f"  Oncelik: [{o['oncelik_no']}] {o['ad']} (sir={o['siralama']})")
        durumlar = await is_takip_service.list_durumlar(db)
        for d in durumlar:
            print(f"  Durum  : [{d['durum_no']}] {d['ad']} (kapanis={d['kapanis_mi']})")

        # 2) Yeni is emri
        print()
        print("=" * 60)
        print("2) CREATE IS EMRi")
        print("=" * 60)
        is1 = await is_takip_service.create_is_emri(
            db, site_no=1,
            baslik="Balkon Suyu Sizintisi",
            aciklama="Daire 1 balkon drenaj kontrolu.",
            acan_no=11,
            atanan_no=3,
            oncelik_no=1,
            daire_no=1,
            termin_tarihi=datetime.now() + timedelta(days=3),
        )
        print(f"  Is #{is1.is_no}: {is1.baslik}")

        is2 = await is_takip_service.create_is_emri(
            db, site_no=1,
            baslik="Bahce Sulama Arizasi",
            acan_no=11,
            atanan_no=3,
            oncelik_no=3,
            termin_tarihi=datetime.now() + timedelta(days=10),
        )
        print(f"  Is #{is2.is_no}: {is2.baslik}")

        # 3) Liste
        print()
        print("=" * 60)
        print("3) LISTE")
        print("=" * 60)
        liste = await is_takip_service.list_is_emirleri(db, site_no=1)
        for i in liste:
            print(f"  [{i['is_no']}] {i['baslik']:30s} durum={i['durum_ad']:20s} oncelik={i['oncelik_ad']:6s} gecikti={i['gecikti_mi']}")

        # 4) Detay
        print()
        print("=" * 60)
        print("4) DETAY")
        print("=" * 60)
        detay = await is_takip_service.get_is_emri(db, is1.is_no, site_no=1)
        print(f"  Baslik: {detay['baslik']}")
        print(f"  Daire: {detay['daire_ozet']}")
        print(f"  Atanan: {detay['atanan_ad']}")
        print(f"  Malzeme sayisi: {detay['malzeme_sayisi']}")
        print(f"  Guncelleme sayisi: {detay['guncelleme_sayisi']}")

        # 5) Malzeme ekle
        print()
        print("=" * 60)
        print("5) MALZEME EKLE")
        print("=" * 60)
        m1 = await is_takip_service.malzeme_ekle(
            db, is1.is_no, site_no=1,
            ad="PVC Boru 50mm", adet=Decimal("2.5"), birim="m", birim_fiyat=Decimal("80.00"),
        )
        m2 = await is_takip_service.malzeme_ekle(
            db, is1.is_no, site_no=1,
            ad="Drenaj Izgarasi", adet=Decimal("1"), birim="adet", birim_fiyat=Decimal("250.00"),
        )
        print(f"  Malzeme #{m1.malzeme_no}: {m1.ad}")
        print(f"  Malzeme #{m2.malzeme_no}: {m2.ad}")

        # 6) Durum degistir
        print()
        print("=" * 60)
        print("6) DURUM DEGISTIR")
        print("=" * 60)
        # durum_no=3 -> UZERINDE_CALISIYOR (siralama 3)
        await is_takip_service.durum_degistir(
            db, is1.is_no, site_no=1, durum_no=3, degistiren_no=3,
            notlar="Drenaj borusu degistiriliyor.",
        )
        detay2 = await is_takip_service.get_is_emri(db, is1.is_no, site_no=1)
        print(f"  Yeni durum: {detay2['durum_ad']}")

        # 7) Tamamla (kapanis)
        print()
        print("=" * 60)
        print("7) TAMAMLA (KAPANIS)")
        print("=" * 60)
        await is_takip_service.durum_degistir(
            db, is1.is_no, site_no=1, durum_no=4, degistiren_no=3,
            notlar="Is tamamlandi, test edildi.",
        )
        detay3 = await is_takip_service.get_is_emri(db, is1.is_no, site_no=1)
        print(f"  Yeni durum: {detay3['durum_ad']}")
        print(f"  Tamamlanma: {detay3['tamamlanma_tarihi']}")
        print(f"  Toplam malzeme: {detay3['toplam_malzeme_tutar']} TL")
        print(f"  Guncelleme sayisi: {detay3['guncelleme_sayisi']}")

        # 8) Ozet
        print()
        print("=" * 60)
        print("8) OZET")
        print("=" * 60)
        ozet = await is_takip_service.get_ozet(db, site_no=1)
        print(f"  Toplam: {ozet['toplam']}, Acik: {ozet['acik']}, Kapali: {ozet['kapali']}")
        print(f"  Gecikmis: {ozet['gecikmis']}, Acil: {ozet['acil']}")
        print(f"  Ort. tamamlama: {ozet['ortalama_tamamlama_gun']} gun")
        print(f"  Durum dagilimi:")
        for d in ozet["durum_dagilimi"]:
            print(f"    {d['durum_ad']:25s} {d['adet']:3d} (%{d['yuzde']})")

        # 9) Benim islerim
        print()
        print("=" * 60)
        print("9) BENIM ISLERIM (kullanici=3)")
        print("=" * 60)
        benim = await is_takip_service.list_benim_islerim(db, site_no=1, kullanici_no=3)
        print(f"  Toplam: {len(benim)} acik is")
        for i in benim:
            print(f"    [{i['is_no']}] {i['baslik']}")

        # 10) Sil
        print()
        print("=" * 60)
        print("10) SIL")
        print("=" * 60)
        await is_takip_service.delete_is_emri(db, is2.is_no, site_no=1)
        print(f"  Is #{is2.is_no} silindi")

        # Temizlik
        await db.execute(delete(IsEmriMalzeme))
        await db.execute(delete(IsEmriGuncelleme))
        await db.execute(delete(IsEmri).where(IsEmri.site_no == 1))
        await db.commit()
        print()
        print("[DONE] Tum testler tamamlandi")


if __name__ == "__main__":
    asyncio.run(main())