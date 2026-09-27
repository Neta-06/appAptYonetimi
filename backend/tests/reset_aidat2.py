"""Test verilerini temizle - aidat 2 ve ilgili ödemeler."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from decimal import Decimal
from sqlalchemy import delete, select
from app.db.session import AsyncSessionLocal
from app.models import Aidat, Odeme, OdemeDetay


async def main():
    async with AsyncSessionLocal() as db:
        # Aidat 2 ile ilişkili tüm ödemeleri bul
        r = await db.execute(
            select(OdemeDetay.odeme_no).where(OdemeDetay.aidat_no == 2)
        )
        odeme_nolar = list({row[0] for row in r.all()})

        print(f"Aidat 2 ile iliskili {len(odeme_nolar)} odeme silinecek: {odeme_nolar}")

        # Ödemeleri sil (CASCADE ile detaylar da gider)
        if odeme_nolar:
            await db.execute(delete(Odeme).where(Odeme.odeme_no.in_(odeme_nolar)))

        # Aidat 2'yi başlangıç durumuna getir
        a = await db.get(Aidat, 2)
        a.odenen_tutar = Decimal("0.00")
        a.durum = "BEKLIYOR"

        await db.commit()
        print("[OK] Aidat 2 sifirlandi (odenen=0, durum=BEKLIYOR)")

        # Kontrol
        a = await db.get(Aidat, 2)
        print(f"  Yeni durum: odenen={a.odenen_tutar}, durum={a.durum}")


if __name__ == "__main__":
    asyncio.run(main())