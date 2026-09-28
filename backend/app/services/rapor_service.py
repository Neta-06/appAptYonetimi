"""Rapor iş mantığı - mevcut verilerden özet çıkarır."""

import logging
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BulunamadiHatasi
from app.models import (
    Aidat,
    Blok,
    Daire,
    DaireDoluluk,
    DaireKullanim,
    DaireSakin,
    Gelir,
    Gider,
    GiderKalemi,
    GiderKategori,
    Kullanici,
    Site,
)

logger = logging.getLogger(__name__)


# ============================================================
# YARDIMCI
# ============================================================
def _onceki_ay() -> tuple[int, int]:
    """İçinde bulunduğumuz ayı döner."""
    bugun = date.today()
    return bugun.year, bugun.month


# ============================================================
# 1) DASHBOARD
# ============================================================
async def get_dashboard(db: AsyncSession, site_no: int) -> dict:
    """Ana dashboard paneli — tüm özetler bir arada."""
    site = await db.get(Site, site_no)
    if site is None:
        raise BulunamadiHatasi("Site", kaynak_id=site_no)

    yil, ay = _onceki_ay()

    # --- Daire sayıları ---
    d_sonuc = await db.execute(
        select(DaireDoluluk.ad, func.count(Daire.daire_no))
        .join(Daire, Daire.doluluk_no == DaireDoluluk.doluluk_no)
        .where(Daire.site_no == site_no)
        .group_by(DaireDoluluk.ad)
    )
    doluluk_map = dict(d_sonuc.all())
    toplam_daire = sum(doluluk_map.values())
    dolu = doluluk_map.get("DOLU", 0)
    bos = doluluk_map.get("BOS", 0)
    doluluk_orani = (dolu / toplam_daire * 100) if toplam_daire > 0 else 0.0

    # --- Sakin sayıları ---
    s_sonuc = await db.execute(
        select(func.count(DaireSakin.kayit_no))
        .join(Daire, Daire.daire_no == DaireSakin.daire_no)
        .where(
            Daire.site_no == site_no,
            DaireSakin.cikis_tarihi.is_(None),
        )
    )
    toplam_sakin = int(s_sonuc.scalar() or 0)

    malik_sonuc = await db.execute(
        select(func.count(DaireSakin.kayit_no))
        .join(Daire, Daire.daire_no == DaireSakin.daire_no)
        .where(
            Daire.site_no == site_no,
            DaireSakin.cikis_tarihi.is_(None),
            DaireSakin.mulk_sahibi_mi.is_(True),
        )
    )
    malik = int(malik_sonuc.scalar() or 0)

    # --- Aidat özeti (bu ay) ---
    a_sonuc = await db.execute(
        select(
            func.coalesce(func.sum(Aidat.tutar), 0),
            func.coalesce(func.sum(Aidat.odenen_tutar), 0),
            func.sum(case((Aidat.durum == "ODENDI", 1), else_=0)),
            func.sum(case((Aidat.durum == "BEKLIYOR", 1), else_=0)),
            func.sum(case((Aidat.durum == "GECIKMIS", 1), else_=0)),
        )
        .where(
            Aidat.site_no == site_no,
            Aidat.donem_yil == yil,
            Aidat.donem_ay == ay,
            Aidat.durum != "IPTAL",
        )
    )
    a_row = a_sonuc.first()
    tahakkuk = Decimal(str(a_row[0] or 0))
    tahsilat = Decimal(str(a_row[1] or 0))
    kalan = tahakkuk - tahsilat
    odenmis = int(a_row[2] or 0)
    bekleyen = int(a_row[3] or 0)
    gecikmis = int(a_row[4] or 0)
    tahsilat_orani = float(tahsilat / tahakkuk * 100) if tahakkuk > 0 else 0.0

    # --- Finansal özet (bu ay) ---
    g_sonuc = await db.execute(
        select(func.coalesce(func.sum(Gider.tutar + Gider.kdv_tutar), 0)).where(
            Gider.site_no == site_no,
            func.year(Gider.gider_tarihi) == yil,
            func.month(Gider.gider_tarihi) == ay,
        )
    )
    toplam_gider = Decimal(str(g_sonuc.scalar() or 0))

    gl_sonuc = await db.execute(
        select(func.coalesce(func.sum(Gelir.tutar), 0)).where(
            Gelir.site_no == site_no,
            func.year(Gelir.gelir_tarihi) == yil,
            func.month(Gelir.gelir_tarihi) == ay,
        )
    )
    toplam_gelir = Decimal(str(gl_sonuc.scalar() or 0))
    net = toplam_gelir - toplam_gider

    return {
        "site_no": site.site_no,
        "site_adi": site.site_adi,
        "daire": {
            "toplam": toplam_daire,
            "dolu": dolu,
            "bos": bos,
            "doluluk_orani": round(doluluk_orani, 2),
        },
        "sakin": {
            "toplam_aktif": toplam_sakin,
            "malik": malik,
            "kiraci": toplam_sakin - malik,
        },
        "aidat": {
            "donem_yil": yil,
            "donem_ay": ay,
            "tahakkuk": tahakkuk,
            "tahsilat": tahsilat,
            "kalan": kalan,
            "tahsilat_orani": round(tahsilat_orani, 2),
            "odenmis": odenmis,
            "bekleyen": bekleyen,
            "gecikmis": gecikmis,
        },
        "finansal": {
            "donem_yil": yil,
            "donem_ay": ay,
            "toplam_gider": toplam_gider,
            "toplam_gelir": toplam_gelir,
            "net_durum": net,
            "kar_zarar": "KAR" if net >= 0 else "ZARAR",
        },
    }


# ============================================================
# 2) FİNANSAL ÖZET
# ============================================================
async def get_finansal_ozet(
    db: AsyncSession, site_no: int, *, yil: int, ay: int
) -> dict:
    """Belirli bir dönem için detaylı finansal özet."""
    site = await db.get(Site, site_no)
    if site is None:
        raise BulunamadiHatasi("Site", kaynak_id=site_no)

    # Gelir kaynakları
    gl_sonuc = await db.execute(
        select(Gelir.kaynak, func.sum(Gelir.tutar))
        .where(
            Gelir.site_no == site_no,
            func.year(Gelir.gelir_tarihi) == yil,
            func.month(Gelir.gelir_tarihi) == ay,
        )
        .group_by(Gelir.kaynak)
    )
    gelir_kaynaklari = {k: Decimal(str(v or 0)) for k, v in gl_sonuc.all()}
    toplam_gelir = sum(gelir_kaynaklari.values(), Decimal("0.00"))

    # Gider kategorileri
    g_sonuc = await db.execute(
        select(GiderKategori.ad, func.sum(Gider.tutar + Gider.kdv_tutar))
        .join(GiderKalemi, GiderKalemi.kategori_no == GiderKategori.kategori_no)
        .join(Gider, Gider.kalem_no == GiderKalemi.kalem_no)
        .where(
            Gider.site_no == site_no,
            func.year(Gider.gider_tarihi) == yil,
            func.month(Gider.gider_tarihi) == ay,
        )
        .group_by(GiderKategori.ad)
    )
    gider_kategorileri = {k: Decimal(str(v or 0)) for k, v in g_sonuc.all()}
    toplam_gider = sum(gider_kategorileri.values(), Decimal("0.00"))

    net = toplam_gelir - toplam_gider
    return {
        "site_no": site.site_no,
        "site_adi": site.site_adi,
        "donem_yil": yil,
        "donem_ay": ay,
        "toplam_gelir": toplam_gelir,
        "toplam_gider": toplam_gider,
        "net": net,
        "kar_zarar": "KAR" if net >= 0 else "ZARAR",
        "gelir_kaynaklari": gelir_kaynaklari,
        "gider_kategorileri": gider_kategorileri,
    }


# ============================================================
# 3) AİDAT DURUMU
# ============================================================
async def get_aidat_durumu(db: AsyncSession, site_no: int) -> dict:
    """Site geneli aidat durum özeti."""
    site = await db.get(Site, site_no)
    if site is None:
        raise BulunamadiHatasi("Site", kaynak_id=site_no)

    sonuc = await db.execute(
        select(
            func.coalesce(func.sum(Aidat.tutar), 0),
            func.coalesce(func.sum(Aidat.odenen_tutar), 0),
            func.sum(case((Aidat.durum == "ODENDI", 1), else_=0)),
            func.sum(case((Aidat.durum == "BEKLIYOR", 1), else_=0)),
            func.sum(case((Aidat.durum == "GECIKMIS", 1), else_=0)),
            func.sum(case((Aidat.durum == "KISMI_ODENDI", 1), else_=0)),
            func.count(func.distinct(Aidat.daire_no)),
        )
        .where(Aidat.site_no == site_no, Aidat.durum != "IPTAL")
    )
    row = sonuc.first()
    tahakkuk = Decimal(str(row[0] or 0))
    tahsilat = Decimal(str(row[1] or 0))
    kalan = tahakkuk - tahsilat
    oran = float(tahsilat / tahakkuk * 100) if tahakkuk > 0 else 0.0
    daire_sayisi = int(row[6] or 0)
    ort_borc = (kalan / daire_sayisi) if daire_sayisi > 0 else Decimal("0.00")

    return {
        "site_no": site.site_no,
        "site_adi": site.site_adi,
        "toplam_tahakkuk": tahakkuk,
        "toplam_tahsilat": tahsilat,
        "toplam_kalan": kalan,
        "tahsilat_orani": round(oran, 2),
        "odenmis_sayisi": int(row[2] or 0),
        "bekleyen_sayisi": int(row[3] or 0),
        "gecikmis_sayisi": int(row[4] or 0),
        "kismi_odenmis_sayisi": int(row[5] or 0),
        "daire_bazli_ortalama_borc": ort_borc.quantize(Decimal("0.01")),
    }


# ============================================================
# 4) GİDER DAĞILIMI
# ============================================================
async def get_gider_dagilim(db: AsyncSession, site_no: int) -> dict:
    """Kategori bazlı gider dağılımı + aylık trend."""
    site = await db.get(Site, site_no)
    if site is None:
        raise BulunamadiHatasi("Site", kaynak_id=site_no)

    # Kategori dağılımı
    k_sonuc = await db.execute(
        select(
            GiderKategori.kategori_no,
            GiderKategori.ad,
            func.coalesce(func.sum(Gider.tutar + Gider.kdv_tutar), 0),
            func.count(Gider.gider_no),
        )
        .join(GiderKalemi, GiderKalemi.kategori_no == GiderKategori.kategori_no)
        .join(Gider, Gider.kalem_no == GiderKalemi.kalem_no)
        .where(Gider.site_no == site_no)
        .group_by(GiderKategori.kategori_no, GiderKategori.ad)
        .order_by(func.sum(Gider.tutar + Gider.kdv_tutar).desc())
    )
    satirlar = list(k_sonuc.all())
    genel_toplam = sum((Decimal(str(r[2] or 0)) for r in satirlar), Decimal("0.00"))

    kategoriler = []
    for r in satirlar:
        tutar = Decimal(str(r[2] or 0))
        yuzde = float(tutar / genel_toplam * 100) if genel_toplam > 0 else 0.0
        kategoriler.append({
            "kategori_no": r[0],
            "kategori_adi": r[1],
            "toplam": tutar,
            "yuzde": round(yuzde, 2),
            "kayit_sayisi": int(r[3] or 0),
        })

    # Aylık trend (son 12 ay)
    a_sonuc = await db.execute(
        select(
            func.year(Gider.gider_tarihi),
            func.month(Gider.gider_tarihi),
            func.coalesce(func.sum(Gider.tutar + Gider.kdv_tutar), 0),
        )
        .where(Gider.site_no == site_no)
        .group_by(func.year(Gider.gider_tarihi), func.month(Gider.gider_tarihi))
        .order_by(
            func.year(Gider.gider_tarihi).desc(),
            func.month(Gider.gider_tarihi).desc(),
        )
        .limit(12)
    )
    aylik = [
        {
            "donem_yil": int(r[0]),
            "donem_ay": int(r[1]),
            "toplam": Decimal(str(r[2] or 0)),
        }
        for r in a_sonuc.all()
    ]

    return {
        "site_no": site.site_no,
        "toplam_gider": genel_toplam,
        "kategoriler": kategoriler,
        "aylik_trend": aylik,
    }


# ============================================================
# 5) DAİRE DOLULUK
# ============================================================
async def get_daire_doluluk(db: AsyncSession, site_no: int) -> dict:
    """Blok bazlı doluluk özeti."""
    site = await db.get(Site, site_no)
    if site is None:
        raise BulunamadiHatasi("Site", kaynak_id=site_no)

    # Genel
    genel_sonuc = await db.execute(
        select(DaireDoluluk.ad, func.count(Daire.daire_no))
        .join(Daire, Daire.doluluk_no == DaireDoluluk.doluluk_no)
        .where(Daire.site_no == site_no)
        .group_by(DaireDoluluk.ad)
    )
    doluluk_map = dict(genel_sonuc.all())
    toplam = sum(doluluk_map.values())
    dolu = doluluk_map.get("DOLU", 0)
    bos = doluluk_map.get("BOS", 0)
    oran = (dolu / toplam * 100) if toplam > 0 else 0.0

    # Kiralık (DaireKullanim.ad == "KIRACI")
    kiralik_sonuc = await db.execute(
        select(func.count(Daire.daire_no))
        .join(DaireKullanim, DaireKullanim.kullanim_no == Daire.kullanim_no)
        .where(Daire.site_no == site_no, DaireKullanim.ad == "KIRACI")
    )
    kiralik = int(kiralik_sonuc.scalar() or 0)

    # Blok bazlı
    b_sonuc = await db.execute(
        select(
            Blok.blok_no,
            Blok.blok_adi,
            DaireDoluluk.ad,
            func.count(Daire.daire_no),
        )
        .join(Daire, Daire.blok_no == Blok.blok_no)
        .join(DaireDoluluk, DaireDoluluk.doluluk_no == Daire.doluluk_no)
        .where(Blok.site_no == site_no)
        .group_by(Blok.blok_no, Blok.blok_adi, DaireDoluluk.ad)
        .order_by(Blok.blok_adi)
    )
    # Blok bazında grupla
    bloklar_dict: dict[int, dict] = {}
    for r in b_sonuc.all():
        b_no, b_adi, d_ad, adet = r
        if b_no not in bloklar_dict:
            bloklar_dict[b_no] = {
                "blok_no": b_no,
                "blok_adi": b_adi,
                "toplam": 0,
                "dolu": 0,
                "bos": 0,
            }
        bloklar_dict[b_no]["toplam"] += adet
        if d_ad == "DOLU":
            bloklar_dict[b_no]["dolu"] += adet
        elif d_ad == "BOS":
            bloklar_dict[b_no]["bos"] += adet

    bloklar = []
    for b in bloklar_dict.values():
        b_oran = (b["dolu"] / b["toplam"] * 100) if b["toplam"] > 0 else 0.0
        bloklar.append({
            **b,
            "doluluk_orani": round(b_oran, 2),
        })

    return {
        "site_no": site.site_no,
        "site_adi": site.site_adi,
        "toplam_daire": toplam,
        "dolu": dolu,
        "bos": bos,
        "kiralik": kiralik,
        "doluluk_orani": round(oran, 2),
        "bloklar": bloklar,
    }


# ============================================================
# 6) BORÇLU DAİRELER
# ============================================================
async def get_borclu_daireler(
    db: AsyncSession, site_no: int, *, limit: int = 20
) -> dict:
    """En çok borçlu daireleri listeler."""
    site = await db.get(Site, site_no)
    if site is None:
        raise BulunamadiHatasi("Site", kaynak_id=site_no)

    # Daire bazlı borç toplamı
    b_sonuc = await db.execute(
        select(
            Daire.daire_no,
            Blok.blok_adi,
            Daire.daire_numarasi,
            func.coalesce(func.sum(Aidat.tutar - Aidat.odenen_tutar), 0),
            func.coalesce(
                func.sum(
                    case(
                        (
                            (Aidat.durum == "GECIKMIS")
                            & (Aidat.son_odeme_tarihi < date.today()),
                            Aidat.tutar - Aidat.odenen_tutar,
                        ),
                        else_=0,
                    )
                ),
                0,
            ),
            func.sum(
                case(
                    (
                        (Aidat.durum.in_(["GECIKMIS", "BEKLIYOR", "KISMI_ODENDI"]))
                        & (Aidat.son_odeme_tarihi < date.today()),
                        1,
                    ),
                    else_=0,
                )
            ),
        )
        .join(Daire, Daire.daire_no == Aidat.daire_no)
        .join(Blok, Blok.blok_no == Daire.blok_no)
        .where(Aidat.site_no == site_no, Aidat.durum != "IPTAL")
        .group_by(Daire.daire_no, Blok.blok_adi, Daire.daire_numarasi)
        .having(func.sum(Aidat.tutar - Aidat.odenen_tutar) > 0)
        .order_by(func.sum(Aidat.tutar - Aidat.odenen_tutar).desc())
        .limit(limit)
    )

    daireler = []
    toplam_borc = Decimal("0.00")
    for r in b_sonuc.all():
        borc = Decimal(str(r[3] or 0))
        toplam_borc += borc
        daireler.append({
            "daire_no": r[0],
            "blok_adi": r[1],
            "daire_numarasi": r[2],
            "toplam_borc": borc,
            "gecikmis_borc": Decimal(str(r[4] or 0)),
            "gecikmis_aidat_sayisi": int(r[5] or 0),
        })

    # Toplam borçlu daire sayısı (limit'ten bağımsız)
    toplam_sonuc = await db.execute(
        select(func.count(func.distinct(Aidat.daire_no)))
        .where(Aidat.site_no == site_no, Aidat.durum != "IPTAL")
        .having(func.sum(Aidat.tutar - Aidat.odenen_tutar) > 0)
    )
    toplam_borclu = int(toplam_sonuc.scalar() or 0)

    return {
        "site_no": site.site_no,
        "toplam_borclu_daire": toplam_borclu,
        "toplam_borc": toplam_borc,
        "daireler": daireler,
    }


# ============================================================
# 7) TREND (Son N ay)
# ============================================================
async def get_trend(db: AsyncSession, site_no: int, *, ay_sayisi: int = 12) -> dict:
    """Son N ayın gelir/gider trendi."""
    site = await db.get(Site, site_no)
    if site is None:
        raise BulunamadiHatasi("Site", kaynak_id=site_no)

    # Aylık gider
    g_sonuc = await db.execute(
        select(
            func.year(Gider.gider_tarihi),
            func.month(Gider.gider_tarihi),
            func.coalesce(func.sum(Gider.tutar + Gider.kdv_tutar), 0),
        )
        .where(Gider.site_no == site_no)
        .group_by(func.year(Gider.gider_tarihi), func.month(Gider.gider_tarihi))
    )
    gider_map = {
        (int(r[0]), int(r[1])): Decimal(str(r[2] or 0))
        for r in g_sonuc.all()
    }

    # Aylık gelir
    gl_sonuc = await db.execute(
        select(
            func.year(Gelir.gelir_tarihi),
            func.month(Gelir.gelir_tarihi),
            func.coalesce(func.sum(Gelir.tutar), 0),
        )
        .where(Gelir.site_no == site_no)
        .group_by(func.year(Gelir.gelir_tarihi), func.month(Gelir.gelir_tarihi))
    )
    gelir_map = {
        (int(r[0]), int(r[1])): Decimal(str(r[2] or 0))
        for r in gl_sonuc.all()
    }

    # Tüm ayları birleştir
    tum_aylar = sorted(set(gider_map.keys()) | set(gelir_map.keys()), reverse=True)
    tum_aylar = tum_aylar[:ay_sayisi]

    trend = []
    toplam_gelir = Decimal("0.00")
    toplam_gider = Decimal("0.00")

    for yil, ay in tum_aylar:
        g = gelir_map.get((yil, ay), Decimal("0.00"))
        x = gider_map.get((yil, ay), Decimal("0.00"))
        toplam_gelir += g
        toplam_gider += x
        trend.append({
            "donem_yil": yil,
            "donem_ay": ay,
            "gelir": g,
            "gider": x,
            "net": g - x,
        })

    adet = len(trend) if trend else 1
    return {
        "site_no": site.site_no,
        "ay_sayisi": len(trend),
        "trend": trend,
        "toplam_gelir": toplam_gelir,
        "toplam_gider": toplam_gider,
        "ortalama_aylik_gelir": (toplam_gelir / adet).quantize(Decimal("0.01")),
        "ortalama_aylik_gider": (toplam_gider / adet).quantize(Decimal("0.01")),
    }