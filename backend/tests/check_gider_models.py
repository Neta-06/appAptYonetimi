"""Cari ve gider modelleri kolon eşleşmesi."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect
from app.db.session import engine
from app.models import (
    CariHesap, CariHareket, CariIslemTipi,
    Gider, GiderKalemi, GiderKategori, Gelir,
)


async def main():
    async with engine.connect() as conn:
        for model in [CariHesap, CariHareket, CariIslemTipi, Gider, GiderKalemi, GiderKategori, Gelir]:
            def sync_inspect(sync_conn, table=model.__tablename__):
                return inspect(sync_conn).get_columns(table)
            cols = await conn.run_sync(sync_inspect)
            mysql_names = {c["name"] for c in cols}
            model_names = {c.name for c in model.__table__.columns}
            status = "OK  " if mysql_names == model_names else "WARN"
            print(f"{status} {model.__tablename__:25s} MySQL={len(mysql_names):2d} Model={len(model_names):2d}")
            if mysql_names != model_names:
                if mysql_names - model_names:
                    print(f"      MySQL-only: {sorted(mysql_names - model_names)}")
                if model_names - mysql_names:
                    print(f"      Model-only: {sorted(model_names - mysql_names)}")


if __name__ == "__main__":
    asyncio.run(main())