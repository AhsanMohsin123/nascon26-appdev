from sqlalchemy import Column, String, UniqueConstraint
from app.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email"),)
    id = Column(String(64), primary_key=True, default=lambda: __import__("uuid").uuid4().hex)
    email = Column(String(120), unique=True)
    password_hash = Column(String(256))
    role = Column(String(32))
    tenant_id = Column(String(64))
    league_id = Column(String(64))
    club_id = Column(String(64))


class OfflineSyncAction(Base):
    __tablename__ = "offline_sync_actions"
    device_id = Column(String(64), primary_key=True)
    action_id = Column(String(64), primary_key=True)
