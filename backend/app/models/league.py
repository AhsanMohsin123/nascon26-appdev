from sqlalchemy import Column, String, Text, ForeignKey
from app.database import Base


class League(Base):
    __tablename__ = "leagues"
    id = Column(String(64), primary_key=True)
    tenant_id = Column(String(64))
    sport_id = Column(String(64))
    config = Column(Text)


class LeagueTeam(Base):
    __tablename__ = "league_teams"
    league_id = Column(String(64), primary_key=True)
    team_id = Column(String(64), primary_key=True)


class Match(Base):
    __tablename__ = "matches"
    id = Column(String(64), primary_key=True)
    league_id = Column(String(64))
    sport_id = Column(String(64))
    home_team_id = Column(String(64))
    away_team_id = Column(String(64))
    status = Column(String(32), default="upcoming")
