"""Rapor servisi doğrudan test."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import AsyncSessionLocal
from app.services import rapor_service


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("1) DASHBOARD (site 1)")
        print("=" * 60)
        d = await rapor_service.get_dashboard(db, site_no=1)
        print(f"  Site: {d['site_adi']}")
        print(f"  Daire: toplam={d['daire']['toplam']} dolu={d['daire']['dolu']} bos={d['daire']['bos']}")
        print(f"  Sakin: toplam={d['sakin']['toplam_aktif']} malik={d['sakin']['malik']} kiraci={d['sakin']['kiraci']}")
        print(f"  Aidat: tahakkuk={d['aidat']['tahakkuk']} tahsilat={d['aidat']['tahsilat']} kalan={d['aidat']['kalan']}")
        print(f"  Finansal: gider={d['finansal']['toplam_gider']} gelir={d['finansal']['toplam_gelir']} net={d['finansal']['net_durum']}")
        print(f"  Sonuc: {d['finansal']['kar_zarar']}")

        print()
        print("=" * 60)
        print("2) DAİRE DOLULUK")
        print("=" * 60)
        dd = await rapor_service.get_daire_doluluk(db, site_no=1)
        print(f"  Toplam: {dd['toplam_daire']}, Dolu: {dd['dolu']}, Bos: {dd['bos']}, Oran: {dd['doluluk_orani']}%")
        for b in dd["bloklar"]:
            print(f"    {b['blok_adi']}: {b['dolu']}/{b['toplam']} (%{b['doluluk_orani']})")

        print()
        print("=" * 60)
        print("3) AİDAT DURUMU")
        print("=" * 60)
        ad = await rapor_service.get_aidat_durumu(db, site_no=1)
        print(f"  Tahakkuk: {ad['toplam_tahakkuk']}, Tahsilat: {ad['toplam_tahsilat']}, Kalan: {ad['toplam_kalan']}")
        print(f"  Tahsilat orani: {ad['tahsilat_orani']}%")
        print(f"  Odenmis: {ad['odenmis_sayisi']}, Bekleyen: {ad['bekleyen_sayisi']}, Gecikmis: {ad['gecikmis_sayisi']}")

        print()
        print("=" * 60)
        print("4) BORÇLU DAİRELER")
        print("=" * 60)
        bd = await rapor_service.get_borclu_daireler(db, site_no=1, limit=5)
        print(f"  Toplam borclu: {bd['toplam_borclu_daire']}, Toplam borc: {bd['toplam_borc']}")
        for d in bd["daireler"]:
            print(f"    {d['blok_adi']}-{d['daire_numarasi']}: {d['toplam_borc']} TL (gecikmis: {d['gecikmis_borc']})")

        print()
        print("=" * 60)
        print("5) TREND (son 12 ay)")
        print("=" * 60)
        t = await rapor_service.get_trend(db, site_no=1, ay_sayisi=12)
        print(f"  Ay sayisi: {t['ay_sayisi']}")
        print(f"  Toplam gelir: {t['toplam_gelir']}, gider: {t['toplam_gider']}")
        for a in t["trend"][:5]:
            print(f"    {a['donem_yil']}/{a['donem_ay']:02d}: gelir={a['gelir']} gider={a['gider']} net={a['net']}")


if __name__ == "__main__":
    asyncio.run(main())