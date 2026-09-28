"""Sakin servisi doğrudan test."""
import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete
from app.db.session import AsyncSessionLocal
from app.models import DaireSakin
from app.services import sakin_service


async def main():
    async with AsyncSessionLocal() as db:
        # Temizlik — sadece test verilerini sil (kayit_no > 3)
        await db.execute(delete(DaireSakin).where(DaireSakin.kayit_no > 3))
        await db.commit()
        print("[i] Eski test verileri temizlendi\n")

        # 1) Liste
        print("=" * 60)
        print("1) SAKIN LISTESI (site 1)")
        print("=" * 60)
        liste = await sakin_service.list_sakinler(db, site_no=1)
        print(f"  Toplam: {len(liste)} aktif sakin")
        for s in liste:
            print(f"    [{s['kayit_no']}] {s['daire_ozet']:25s} {s['ad']} {s['soyad']:15s} mulk={s['mulk_sahibi_mi']}")

        # 2) Daire sakinleri
        print()
        print("=" * 60)
        print("2) DAIRE 1 SAKINLERI (gecmis dahil)")
        print("=" * 60)
        daire_sakinleri = await sakin_service.list_daire_sakinleri(db, site_no=1, daire_no=1)
        for s in daire_sakinleri:
            durum = "AKTIF" if s["aktif_mi"] else "GECMIS"
            print(f"    [{durum}] {s['ad']} {s['soyad']} ({s['giris_tarihi']} - {s['cikis_tarihi']})")

        # 3) Detay
        print()
        print("=" * 60)
        print("3) DETAY (ilk kayit)")
        print("=" * 60)
        if liste:
            detay = await sakin_service.get_sakin(db, liste[0]["kayit_no"], site_no=1)
            print(f"  {detay['ad']} {detay['soyad']}")
            print(f"  Daire: {detay['blok_adi']} - {detay['daire_numarasi']} ({detay['daire_tipi']})")
            print(f"  Mul sahibi: {detay['mulk_sahibi_mi']}")
            print(f"  Aktif: {detay['aktif_mi']}")
            print(f"  Diger sakin sayisi: {detay['diger_aktif_sakin_sayisi']}")

        # 4) Yeni sakin ekleme
        print()
        print("=" * 60)
        print("4) YENI SAKIN EKLE (daire 4, kullanici 5)")
        print("=" * 60)
        try:
            yeni = await sakin_service.create_sakin(
                db, site_no=1,
                daire_no=4, kullanici_no=5,
                mulk_sahibi_mi=False,
                giris_tarihi=date.today(),
            )
            print(f"  Kayit #{yeni.kayit_no} olusturuldu")
        except Exception as e:
            print(f"  [i] {e}")

        # Daire 4 doluluk kontrolü
        from app.models import Daire, DaireDoluluk
        d = await db.get(Daire, 4)
        dd = await db.get(DaireDoluluk, d.doluluk_no)
        print(f"  Daire 4 doluluk: {dd.ad}  (DOLU olmali)")

        # 5) Ozet
        print()
        print("=" * 60)
        print("5) OZET")
        print("=" * 60)
        ozet = await sakin_service.get_ozet(db, site_no=1)
        print(f"  Aktif: {ozet['toplam_aktif']}")
        print(f"  Malik: {ozet['toplam_malik']}, Kiraci: {ozet['toplam_kiraci']}")
        print(f"  Gecmis: {ozet['toplam_gecmis']}")
        print(f"  Daire basina ort: {ozet['daire_basina_ortalama_sakin']}")
        print(f"  En kalabalik: {ozet['en_kalabalik_daire']} ({ozet['en_kalabalik_sayi']} kisi)")

        # 6) Cikis yap
        print()
        print("=" * 60)
        print("6) CIKIS YAP")
        print("=" * 60)
        if liste:
            try:
                sonuc = await sakin_service.cikis_yap(
                    db, liste[-1]["kayit_no"], site_no=1,
                    cikis_tarihi=date.today(),
                )
                print(f"  {sonuc['mesaj']}")
            except Exception as e:
                print(f"  [i] {e}")

        # 7) Tasinma
        print()
        print("=" * 60)
        print("7) TASINMA (daire 1 -> daire 2)")
        print("=" * 60)
        aktif_liste = await sakin_service.list_sakinler(db, site_no=1, daire_no=1)
        if aktif_liste:
            try:
                sonuc = await sakin_service.tasindi_yap(
                    db, aktif_liste[0]["kayit_no"], site_no=1,
                    yeni_daire_no=2,
                    tasinma_tarihi=date.today(),
                )
                print(f"  {sonuc['mesaj']}")
                print(f"  Eski kayit: #{sonuc['eski_kayit_no']} -> Yeni: #{sonuc['yeni_kayit_no']}")
            except Exception as e:
                print(f"  [i] {e}")

        # Temizlik — bu sefer hepsini sil
        await db.execute(delete(DaireSakin).where(DaireSakin.kayit_no > 3))
        await db.commit()
        print()
        print("[DONE] Tum testler tamamlandi")


if __name__ == "__main__":
    asyncio.run(main())