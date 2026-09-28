"""Personel servisi doğrudan test."""
import asyncio
import sys
from datetime import date, time, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete
from app.core.utils import now_utc_naive
from app.db.session import AsyncSessionLocal
from app.models import (
    Personel, PersonelIzin, PersonelMaasOdeme,
    PersonelPuantaj, PersonelSite,
)
from app.services import personel_service


async def main():
    async with AsyncSessionLocal() as db:
        # Temizlik
        await db.execute(delete(PersonelMaasOdeme))
        await db.execute(delete(PersonelPuantaj))
        await db.execute(delete(PersonelIzin))
        await db.execute(delete(PersonelSite))
        await db.execute(delete(Personel).where(Personel.firma_no == 1))
        await db.commit()
        print("[i] Eski test personeli temizlendi\n")

        # 1) Yeni personel
        print("=" * 60)
        print("1) CREATE PERSONEL")
        print("=" * 60)
        p1 = await personel_service.create_personel(
            db, firma_no=1,
            ad="Mehmet", soyad="Demir",
            gorevi="TEKNIK PERSONEL",
            telefon="05011110003",
            e_posta="mehmet@ornek.com",
            kullanici_no=3,
            ise_baslama_tarihi=date(2025, 1, 1),
            site_nolar=[1, 2],
        )
        print(f"  Personel #{p1.personel_no}: {p1.ad} {p1.soyad} ({p1.gorevi})")

        p2 = await personel_service.create_personel(
            db, firma_no=1,
            ad="Emine", soyad="Temiz",
            gorevi="TEMIZLIK PERSONELI",
            ise_baslama_tarihi=date(2025, 3, 1),
            site_nolar=[1],
        )
        print(f"  Personel #{p2.personel_no}: {p2.ad} {p2.soyad}")

        # 2) Liste
        print()
        print("=" * 60)
        print("2) LISTE")
        print("=" * 60)
        liste = await personel_service.list_personel(db, firma_no=1)
        for p in liste:
            print(f"  [{p['personel_no']}] {p['ad']} {p['soyad']:15s} gorev={p['gorevi']:20s} site={p['site_sayisi']}")

        # 3) Detay
        print()
        print("=" * 60)
        print("3) DETAY")
        print("=" * 60)
        detay = await personel_service.get_personel(db, p1.personel_no, firma_no=1)
        print(f"  Ad: {detay['ad']} {detay['soyad']}")
        print(f"  Gorev: {detay['gorevi']}")
        print(f"  Siteler: {[s['site_adi'] for s in detay['siteler']]}")
        print(f"  Izinler: {len(detay['izinler'])}")
        print(f"  Toplam izin gunu: {detay['toplam_izin_gun']}")

        # 4) Izin talebi
        print()
        print("=" * 60)
        print("4) IZIN TALEP ET")
        print("=" * 60)
        izin = await personel_service.izin_talep_et(
            db, p1.personel_no, firma_no=1,
            izin_tipi="YILLIK",
            baslangic_tarihi=date(2026, 10, 1),
            bitis_tarihi=date(2026, 10, 5),
            aciklama="Yillik izin",
        )
        print(f"  Izin #{izin.izin_no}: {izin.izin_tipi}, {izin.gun_sayisi} gun")
        print(f"  Onay durum: {izin.onay_durum_no} (2=BEKLIYOR)")

        # 5) Izin onayla
        print()
        print("=" * 60)
        print("5) IZIN ONAYLA")
        print("=" * 60)
        onay = await personel_service.izin_onayla(
            db, izin.izin_no, firma_no=1,
            onay_durum_no=1, onaylayan_no=11,
            aciklama="Onaylandi",
        )
        print(f"  Yeni onay durum: {onay.onay_durum_no} (1=ONAYLANDI)")
        print(f"  Onaylayan: {onay.onaylayan_no}")

        # 6) List izinler
        print()
        print("=" * 60)
        print("6) IZIN LISTESI")
        print("=" * 60)
        izinler = await personel_service.list_izinler(db, firma_no=1)
        print(f"  Toplam: {len(izinler)} izin")

        # 7) Puantaj ekle (3 gun)
        print()
        print("=" * 60)
        print("7) PUANTAJ EKLE (3 gun)")
        print("=" * 60)
        for i in range(3):
            tarih = date(2026, 9, 1 + i)
            pt = await personel_service.puantaj_ekle(
                db, p1.personel_no, firma_no=1,
                tarih=tarih,
                giris_saati=time(8, 0),
                cikis_saati=time(17, 0),
            )
            print(f"  Puantaj #{pt.puantaj_no}: {pt.tarih}, saat={pt.toplam_saat}")

        # 8) Aylik puantaj ozeti
        print()
        print("=" * 60)
        print("8) AYLIK PUANTAJ OZETI")
        print("=" * 60)
        ozet = await personel_service.puantaj_aylik_ozet(
            db, firma_no=1, donem_yil=2026, donem_ay=9
        )
        for o in ozet:
            print(f"  {o['ad']} {o['soyad']}: {o['calisilan_gun']}/{o['toplam_gun']} gun, {o['toplam_saat']} saat")

        # 9) Maas ekle
        print()
        print("=" * 60)
        print("9) MAAS EKLE")
        print("=" * 60)
        maas = await personel_service.maas_ekle(
            db, p1.personel_no, firma_no=1,
            donem_yil=2026, donem_ay=9,
            brut_maas=Decimal("30000.00"),
            kesintiler=Decimal("4500.00"),
            odeme_tarihi=date(2026, 9, 30),
        )
        print(f"  Maas #{maas.maas_odeme_no}: brut={maas.brut_maas}, net={maas.net_maas}")

        # 10) Maas listesi
        print()
        print("=" * 60)
        print("10) MAAS LISTESI")
        print("=" * 60)
        maaslar = await personel_service.list_maaslar(db, p1.personel_no, firma_no=1)
        print(f"  Toplam: {len(maaslar)} maas")
        for m in maaslar:
            print(f"    {m['donem_yil']}/{m['donem_ay']:02d}: brut={m['brut_maas']} net={m['net_maas']}")

        # 11) Ozet
        print()
        print("=" * 60)
        print("11) OZET")
        print("=" * 60)
        ozet = await personel_service.get_ozet(db, firma_no=1)
        print(f"  Toplam: {ozet['toplam_personel']}")
        print(f"  Aktif: {ozet['aktif_personel']}, Pasif: {ozet['pasif_personel']}")
        print(f"  Aktif izinli: {ozet['aktif_izinli']}")
        print(f"  Toplam yillik izin: {ozet['toplam_yillik_izin_gun']} gun")
        print(f"  Ort. hizmet yili: {ozet['ortalama_hizmet_yili']}")
        print(f"  Gorev dagilimi:")
        for g in ozet["gorev_dagilimi"]:
            print(f"    {g['gorevi']:25s} {g['sayi']} (%{g['yuzde']})")

        # 12) Site ata
        print()
        print("=" * 60)
        print("12) SITE ATA")
        print("=" * 60)
        try:
            ps = await personel_service.site_ata(
                db, p2.personel_no, firma_no=1, site_no=2
            )
            print(f"  Atama #{ps.kayit_no}: personel={ps.personel_no}, site={ps.site_no}")
        except Exception as e:
            print(f"  [i] {e}")

        # 13) Isten cikis
        print()
        print("=" * 60)
        print("13) ISTEN CIKIS")
        print("=" * 60)
        cikis = await personel_service.isten_cikis(
            db, p2.personel_no, firma_no=1,
            isten_cikis_tarihi=date(2026, 9, 30),
            aciklama="Istifa",
        )
        print(f"  Personel #{p2.personel_no} aktif_mi={cikis.aktif_mi}")
        print(f"  Cikis tarihi: {cikis.isten_cikis_tarihi}")

        # 14) Sil
        print()
        print("=" * 60)
        print("14) SIL")
        print("=" * 60)
        await personel_service.delete_personel(db, p2.personel_no, firma_no=1)
        print(f"  Personel #{p2.personel_no} silindi")

        # Temizlik
        await db.execute(delete(PersonelMaasOdeme))
        await db.execute(delete(PersonelPuantaj))
        await db.execute(delete(PersonelIzin))
        await db.execute(delete(PersonelSite))
        await db.execute(delete(Personel).where(Personel.firma_no == 1))
        await db.commit()
        print()
        print("[DONE] Tum testler tamamlandi")


if __name__ == "__main__":
    asyncio.run(main())