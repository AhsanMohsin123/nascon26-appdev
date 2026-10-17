from sqlalchemy import Column, String, Text
from app.database import Base


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(String(64), primary_key=True)
    name = Column(String(120))


class Sport(Base):
    __tablename__ = "sports"
    id = Column(String(64), primary_key=True)
    name = Column(String(120))
    config = Column(Text)
