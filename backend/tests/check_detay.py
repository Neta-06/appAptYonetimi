"""OdemeDetay tablosu kontrol."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models import OdemeDetay, Odeme


async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(OdemeDetay).order_by(OdemeDetay.detay_no))
        detaylar = list(r.scalars().all())
        print(f"Toplam {len(detaylar)} OdemeDetay kaydi:")
        for d in detaylar:
            print(f"  detay#{d.detay_no}: odeme={d.odeme_no} aidat={d.aidat_no} tutar={d.tutar}")


if __name__ == "__main__":
    asyncio.run(main())