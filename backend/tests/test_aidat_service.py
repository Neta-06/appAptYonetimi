"""Aidat servisi doğrudan test — HTTP olmadan."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import AsyncSessionLocal
from app.services import aidat_service


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("1) AIDAT OZET (site 1)")
        print("=" * 60)
        ozet = await aidat_service.get_ozet(db, site_no=1)
        for k, v in ozet.items():
            print(f"  {k:25s}: {v}")

        print()
        print("=" * 60)
        print("2) AIDAT LISTESI (site 1, ilk 5)")
        print("=" * 60)
        aidatlar = await aidat_service.list_aidatlar(db, site_no=1, limit=5)
        for a in aidatlar:
            print(
                f"  [{a['aidat_no']}] {a['blok_adi']}-{a['daire_numarasi']} "
                f"{a['donem_yil']}/{a['donem_ay']:02d} "
                f"{a['tutar']} TL -> {a['durum']} (kalan: {a['kalan_tutar']})"
            )

        print()
        print("=" * 60)
        print("3) GECIKMIS AIDATLAR (site 1)")
        print("=" * 60)
        gecikmis = await aidat_service.list_gecikmis(db, site_no=1)
        print(f"  Toplam: {len(gecikmis)} gecikmis aidat")
        for a in gecikmis[:3]:
            print(
                f"  [{a['aidat_no']}] {a['blok_adi']}-{a['daire_numarasi']} "
                f"{a['gecikme_gun']} gun gecikti -> {a['durum']}"
            )

        print()
        print("=" * 60)
        print("4) DAIRE AIDAT GECMISI (daire 1)")
        print("=" * 60)
        gecmis = await aidat_service.list_daire_aidat_gecmisi(
            db, daire_no=1, site_no=1
        )
        print(f"  {gecmis['blok_adi']} - Daire {gecmis['daire_numarasi']}")
        print(f"  Toplam borc : {gecmis['toplam_borc']} TL")
        print(f"  Toplam odenen: {gecmis['toplam_odenen']} TL")
        print(f"  Kalan       : {gecmis['kalan']} TL")
        print(f"  Aidat sayisi: {len(gecmis['aidatlar'])}")


if __name__ == "__main__":
    asyncio.run(main())