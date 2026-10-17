from sqlalchemy import Column, String, Integer, Text
from app.database import Base


class MatchEvent(Base):
    __tablename__ = "match_events"
    id = Column(String(64), primary_key=True)
    match_id = Column(String(64), index=True)
    sequence = Column(Integer)
    match_version = Column(Integer)
    type = Column(String(32))
    payload = Column(Text)
    signature = Column(String(128))
