"""
SQLAlchemy Declarative Base ve ortak mixin'ler.
Tüm modeller buradaki Base sınıfından türer.
"""

from datetime import datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# ------------------------------------------------------------
# Constraint isimlendirme kuralları
# ------------------------------------------------------------
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# ------------------------------------------------------------
# Base sınıfı
# ------------------------------------------------------------
class Base(DeclarativeBase):
    """
    Tüm modellerin ortak atası.
    Naming convention metadata üzerinden tüm tablolara uygulanır.
    """
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# ------------------------------------------------------------
# Zaman damgası mixin'i
# ------------------------------------------------------------
class TimestampMixin:
    """
    Tüm tablolarda ortak olan zaman damgası kolonları.
    """

    olusturma_tarihi: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        nullable=False,
        comment="Kaydın oluşturulma zamanı",
    )

    guncellenme_tarihi: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
        comment="Kaydın son güncellenme zamanı",
    )