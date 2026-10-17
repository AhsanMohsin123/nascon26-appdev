from sqlalchemy import Column, String, Text
from app.database import Base


class Club(Base):
    __tablename__ = "clubs"
    id = Column(String(64), primary_key=True)
    tenant_id = Column(String(64))
    name = Column(String(120))


class Squad(Base):
    __tablename__ = "squads"
    id = Column(String(64), primary_key=True)
    league_id = Column(String(64))
    club_id = Column(String(64))
    tenant_id = Column(String(64))
    name = Column(String(120))


class Player(Base):
    __tablename__ = "players"
    id = Column(String(64), primary_key=True)
    club_id = Column(String(64))
    name = Column(String(120))
    position = Column(String(32))


class PlayerRegistration(Base):
    __tablename__ = "player_registrations"
    player_id = Column(String(64), primary_key=True)
    league_id = Column(String(64), primary_key=True)
    squad_id = Column(String(64))
    parent_squad_id = Column(String(64))
    role = Column(String(32))
    registration_type = Column(String(32))
    start_date = Column(String(10))
    loan_end_date = Column(String(10))


class RosterAudit(Base):
    __tablename__ = "roster_audit"
    id = Column(String(64), primary_key=True)
    league_id = Column(String(64))
    player_id = Column(String(64))
    action = Column(String(32))
    from_squad = Column(String(64))
    to_squad = Column(String(64))
    effective_date = Column(String(10))
    who = Column(String(120))
    why = Column(Text)
    when_ = Column(String(32))
    response = Column(Text)
