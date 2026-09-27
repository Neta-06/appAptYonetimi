"""
Denetim kaydi (audit log).

SQLAlchemy event listener ile kritik tablolardaki
INSERT / UPDATE / DELETE islemlerini otomatik kaydeder.
"""

import logging
from contextvars import ContextVar
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.core.utils import ip_to_bytes, now_utc_naive

logger = logging.getLogger(__name__)


# ============================================================
# Audit Context
# ============================================================
_audit_context: ContextVar[dict[str, Any]] = ContextVar(
    "audit_context", default={}
)


def set_audit_context(
    *,
    kullanici_no: int | None = None,
    site_no: int | None = None,
    ip_adresi: str | None = None,
    user_agent: str | None = None,
) -> None:
    _audit_context.set({
        "kullanici_no": kullanici_no,
        "site_no": site_no,
        "ip_adresi": ip_adresi,
        "user_agent": user_agent,
    })


def clear_audit_context() -> None:
    _audit_context.set({})


def get_audit_context() -> dict[str, Any]:
    return _audit_context.get() or {}


# ============================================================
# Izlenen tablolar
# ============================================================
IZLENEN_TABLOLAR = {
    # Kimlik ve yetki
    "kullanici",
    "kullanici_site",
    "rol",
    "yetki",
    "rol_yetki",
    # KVKK
    "kvkk_onay",
    # Firma / site
    "yonetim_firmasi",
    "site",
    "blok",
    "daire",
    "daire_sakin",
    # Finansal
    "aidat",
    "odeme",
    "odeme_detay",
    "gider",
    "gelir",
    "cari_hesap",
    "cari_hareket",
    "banka_hesabi",
    "banka_hareketi",
    # Personel
    "personel",
    "personel_site",
    "personel_izin",
    "personel_maas_odeme",
}


# ============================================================
# JSON serileştirme
# ============================================================
def _json_uyumlu(deger: Any) -> Any:
    if deger is None:
        return None
    if isinstance(deger, (str, int, float, bool)):
        return deger
    if isinstance(deger, Decimal):
        return str(deger)
    if isinstance(deger, (datetime, date)):
        return deger.isoformat()
    if isinstance(deger, bytes):
        return f"<binary {len(deger)} byte>"
    if isinstance(deger, (list, tuple, set)):
        return [_json_uyumlu(x) for x in deger]
    if isinstance(deger, dict):
        return {k: _json_uyumlu(v) for k, v in deger.items()}
    return str(deger)


def _row_to_dict(obj: Any) -> dict[str, Any]:
    sonuc: dict[str, Any] = {}
    for kolon in obj.__table__.columns:
        try:
            sonuc[kolon.name] = _json_uyumlu(getattr(obj, kolon.name, None))
        except Exception:
            sonuc[kolon.name] = None
    return sonuc


def _pk_degeri(obj: Any) -> str | None:
    try:
        pk = obj.__table__.primary_key
        degerler = [str(getattr(obj, k.name, "")) for k in pk.columns]
        return ",".join(degerler) if degerler else None
    except Exception:
        return None


# ============================================================
# Audit Log yazıcı
# ============================================================
def _audit_log_yaz(
    session: Session,
    *,
    tablo_adi: str,
    kayit_id: str | None,
    islem_tipi: str,
    eski_deger: dict | None,
    yeni_deger: dict | None,
) -> None:
    ctx = get_audit_context()

    from app.models.identity import AuditLog

    log = AuditLog(
        kullanici_no=ctx.get("kullanici_no"),
        site_no=ctx.get("site_no"),
        tablo_adi=tablo_adi,
        kayit_id=kayit_id,
        islem_tipi=islem_tipi,
        eski_deger=eski_deger,
        yeni_deger=yeni_deger,
        ip_adresi=ip_to_bytes(ctx.get("ip_adresi")),
        user_agent=(ctx.get("user_agent") or "")[:255] or None,
        islem_tarihi=now_utc_naive(),
    )
    session.add(log)


# ============================================================
# Event Listener'ları
# ============================================================
@event.listens_for(Session, "before_flush")
def _audit_before_flush(session: Session, flush_context, instances) -> None:
    """Flush öncesi nesneleri kuyruğa al (PK henüz yok)."""
    try:
        kuyruk: list = session.info.setdefault("_audit_kuyruk", [])

        # INSERT
        for obj in session.new:
            tablo = getattr(obj, "__tablename__", None)
            if tablo in IZLENEN_TABLOLAR:
                kuyruk.append({
                    "islem": "INSERT",
                    "obj": obj,
                    "eski": None,
                    "yeni": _row_to_dict(obj),
                })

        # UPDATE
        for obj in session.dirty:
            tablo = getattr(obj, "__tablename__", None)
            if tablo not in IZLENEN_TABLOLAR:
                continue
            if not session.is_modified(obj, include_collections=False):
                continue
            try:
                from sqlalchemy import inspect as sa_inspect
                attrs = sa_inspect(obj).attrs
                eski: dict[str, Any] = {}
                yeni: dict[str, Any] = {}
                for attr in attrs:
                    if attr.key.startswith("_"):
                        continue
                    h = attr.load_history()
                    if h.has_changes():
                        eski[attr.key] = _json_uyumlu(h.deleted[0] if h.deleted else None)
                        yeni[attr.key] = _json_uyumlu(h.added[0] if h.added else None)
                if not eski and not yeni:
                    continue
                kuyruk.append({
                    "islem": "UPDATE",
                    "obj": obj,
                    "eski": eski,
                    "yeni": yeni,
                })
            except Exception as exc:
                logger.debug("Audit UPDATE atlandi (%s): %s", tablo, exc)

        # DELETE
        for obj in session.deleted:
            tablo = getattr(obj, "__tablename__", None)
            if tablo in IZLENEN_TABLOLAR:
                kuyruk.append({
                    "islem": "DELETE",
                    "obj": obj,
                    "eski": _row_to_dict(obj),
                    "yeni": None,
                })

    except Exception as exc:
        logger.error("Audit before_flush hatasi: %s", exc, exc_info=True)


@event.listens_for(Session, "after_flush_postexec")
def _audit_after_flush(session: Session, flush_context) -> None:
    """Flush sonrası kuyruğu işle (PK artık set edilmiş)."""
    # Recursion önleme: audit log yazarken yeniden tetiklenmesin
    if session.info.get("_audit_in_progress"):
        return

    kuyruk: list = session.info.pop("_audit_kuyruk", [])
    if not kuyruk:
        return

    session.info["_audit_in_progress"] = True
    try:
        for kayit in kuyruk:
            tablo = getattr(kayit["obj"], "__tablename__", None)
            _audit_log_yaz(
                session,
                tablo_adi=tablo,
                kayit_id=_pk_degeri(kayit["obj"]),
                islem_tipi=kayit["islem"],
                eski_deger=kayit["eski"],
                yeni_deger=kayit["yeni"],
            )
        
    except Exception as exc:
        logger.error("Audit after_flush hatasi: %s", exc, exc_info=True)
    finally:
        session.info.pop("_audit_in_progress", None)
