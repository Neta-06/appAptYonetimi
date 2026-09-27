"""Ödeme ve aidat durumu teşhis."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models import Aidat, Odeme, OdemeDetay


async def main():
    async with AsyncSessionLocal() as db:
        # Aidat 2 durumu
        a = await db.get(Aidat, 2)
        print("=" * 60)
        print("AIDAT 2 DURUMU")
        print("=" * 60)
        print(f"  Tutar : {a.tutar}")
        print(f"  Odenen: {a.odenen_tutar}")
        print(f"  Durum : {a.durum}")

        # Aidat 2'ye bağlı ödeme detayları
        r = await db.execute(
            select(OdemeDetay, Odeme)
            .join(Odeme, Odeme.odeme_no == OdemeDetay.odeme_no)
            .where(OdemeDetay.aidat_no == 2)
            .order_by(Odeme.odeme_no)
        )
        rows = list(r.all())
        print(f"\nAidat 2'ye bagli {len(rows)} odeme detayi:")
        onay_map = {1: "ONAYLANDI", 2: "BEKLIYOR", 3: "REDDEDILDI"}
        for d, o in rows:
            print(
                f"  Odeme #{o.odeme_no}: tutar={d.tutar} "
                f"onay={onay_map.get(o.onay_durum_no, o.onay_durum_no)}"
            )

        # Tüm ödemeler
        r = await db.execute(select(Odeme).order_by(Odeme.odeme_no))
        odemeler = list(r.scalars().all())
        print(f"\nToplam {len(odemeler)} odeme:")
        for o in odemeler:
            onay = onay_map.get(o.onay_durum_no, o.onay_durum_no)
            print(f"  #{o.odeme_no}: tutar={o.toplam_tutar} onay={onay} site={o.site_no}")


if __name__ == "__main__":
    asyncio.run(main())