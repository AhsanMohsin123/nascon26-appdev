from sqlalchemy import Column, String, Integer, Text
from app.database import Base


class Product(Base):
    __tablename__ = "products"
    id = Column(String(64), primary_key=True)
    tenant_id = Column(String(64))
    name = Column(String(120))


class ProductVariant(Base):
    __tablename__ = "product_variants"
    id = Column(String(64), primary_key=True)
    product_id = Column(String(64))
    size = Column(String(32))
    color = Column(String(32))
    price_minor = Column(Integer)
    currency = Column(String(8))
    stock = Column(Integer, default=0)


class Order(Base):
    __tablename__ = "orders"
    id = Column(String(64), primary_key=True)
    customer_id = Column(String(64))
    status = Column(String(32))
    response = Column(Text)
