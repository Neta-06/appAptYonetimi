"""Sayaç servisi doğrudan test."""
import asyncio
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete
from app.db.session import AsyncSessionLocal
from app.models import DaireSayaci, SayacFaturaPayi, SayacFaturasi, SayacOkuma
from app.services import sayac_service


async def main():
    async with AsyncSessionLocal() as db:
        # Temizlik
        await db.execute(delete(SayacFaturaPayi))
        await db.execute(delete(SayacFaturasi).where(SayacFaturasi.site_no == 1))
        await db.execute(delete(SayacOkuma))
        await db.execute(delete(DaireSayaci).where(DaireSayaci.daire_sayac_no > 5))
        await db.commit()
        print("[i] Temizlendi\n")

        # 1) Lookup
        print("=" * 60)
        print("1) LOOKUP")
        print("=" * 60)
        birimler = await sayac_service.list_birimler(db)
        print(f"  Birimler: {len(birimler)}")
        for b in birimler:
            print(f"    [{b['birim_no']}] {b['ad']}")
        turler = await sayac_service.list_sayac_turleri(db)
        print(f"  Turler: {len(turler)}")
        for t in turler:
            print(f"    [{t['sayac_turu_no']}] {t['adi']} ({t['birim_ad']})")

        # 2) Daire sayaclari
        print()
        print("=" * 60)
        print("2) DAIRE 1 SAYACLARI")
        print("=" * 60)
        sayaclar = await sayac_service.list_daire_sayaclari(db, site_no=1, daire_no=1)
        for s in sayaclar:
            print(f"  [{s['daire_sayac_no']}] {s['sayac_turu']} ({s['birim']}) seri={s['seri_no']}")
            print(f"      Son okuma: {s['son_okuma_degeri']} ({s['son_okuma_tarihi']})")

        # 3) Yeni sayac
        print()
        print("=" * 60)
        print("3) YENI SAYAC (daire 2, dogalgaz)")
        print("=" * 60)
        try:
            yeni = await sayac_service.create_daire_sayaci(
                db, site_no=1, daire_no=2,
                sayac_turu_no=3,  # Dogalgaz
                seri_no="DG-TEST-001",
                montaj_tarihi=date.today(),
                ilk_deger=Decimal("0.00"),
            )
            print(f"  Sayac #{yeni.daire_sayac_no} olusturuldu: {yeni.seri_no}")
        except Exception as e:
            print(f"  [i] {e}")

        # 4) Okuma ekle (daire 1 sayac 1)
        print()
        print("=" * 60)
        print("4) OKUMA EKLE")
        print("=" * 60)
        sayac_1 = sayaclar[0] if sayaclar else None
        if sayac_1:
            try:
                o1 = await sayac_service.create_okuma(
                    db, sayac_1["daire_sayac_no"], site_no=1,
                    okuma_tarihi=date.today(),
                    guncel_deger=Decimal("200.00"),
                    okuyan_no=3,
                )
                print(f"  Okuma #{o1.okuma_no}: deger={o1.guncel_deger} tuketim={o1.tuketim}")
            except Exception as e:
                print(f"  [i] {e}")

            # Ikinci okuma (tuketim hesaplanmali)
            try:
                o2 = await sayac_service.create_okuma(
                    db, sayac_1["daire_sayac_no"], site_no=1,
                    okuma_tarihi=date.today() + timedelta(days=30),
                    guncel_deger=Decimal("230.00"),
                    okuyan_no=3,
                )
                print(f"  Okuma #{o2.okuma_no}: deger={o2.guncel_deger} tuketim={o2.tuketim} (30 olmali)")
            except Exception as e:
                print(f"  [i] {e}")

            # Okuma gecmisi
            print()
            gecmis = await sayac_service.list_okumalar(db, sayac_1["daire_sayac_no"], site_no=1)
            print(f"  Okuma gecmisi: {len(gecmis)} kayit")

        # 5) Fatura olustur (esit dagitim)
        print()
        print("=" * 60)
        print("5) FATURA OLUSTUR (ESIT dagitim)")
        print("=" * 60)
        try:
            fatura = await sayac_service.create_fatura(
                db, site_no=1,
                sayac_turu_no=1, donem_yil=2026, donem_ay=11,
                toplam_tutar=Decimal("1000.00"),
                ortak_alan_tutar=Decimal("100.00"),
                dagitim_sekli="ESIT",
            )
            print(f"  Fatura #{fatura.fatura_no}: toplam={fatura.toplam_tutar}")

            detay = await sayac_service.get_fatura(db, fatura.fatura_no, site_no=1)
            print(f"  Paylar: {len(detay['paylar'])}")
            print(f"  Toplam dagitilan: {detay['toplam_dagitilan']}")
            for p in detay["paylar"]:
                print(f"    {p['daire_ozet']}: {p['daire_tutari']} TL")
        except Exception as e:
            print(f"  [FAIL] {e}")

        # 6) Fatura listesi
        print()
        print("=" * 60)
        print("6) FATURA LISTESI")
        print("=" * 60)
        faturalar = await sayac_service.list_faturalar(db, site_no=1)
        print(f"  Toplam: {len(faturalar)} fatura")
        for f in faturalar[:3]:
            print(f"    #{f['fatura_no']} {f['sayac_turu']} {f['donem_yil']}/{f['donem_ay']:02d} = {f['toplam_tutar']} TL")

        # 7) Ozet
        print()
        print("=" * 60)
        print("7) OZET")
        print("=" * 60)
        ozet = await sayac_service.get_ozet(db, site_no=1)
        print(f"  Aktif sayac: {ozet['aktif_sayac_sayisi']}")
        print(f"  Toplam okuma: {ozet['toplam_okuma_sayisi']}")
        print(f"  Toplam fatura: {ozet['toplam_fatura_sayisi']}, tutar={ozet['toplam_fatura_tutar']}")
        print(f"  Tuketim ozetleri:")
        for t in ozet["tuketim_ozetleri"]:
            print(f"    {t['sayac_turu']}: {t['toplam_tuketim']} {t['birim']} ({t['okuma_sayisi']} okuma)")

        print()
        print("[DONE] Tum testler tamamlandi")


if __name__ == "__main__":
    asyncio.run(main())