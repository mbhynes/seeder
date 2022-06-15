import enum
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy import Integer, String, Boolean, DateTime, Float, Enum

from sqlalchemy.orm import declarative_base, relationship
Base = declarative_base()


class PlayerType(enum.Enum):
  single = 1
  double = 2


class Player(Base):
  __tablename__ = "players"
  id = Column(String, primary_key=True)
  name = Column(String)
  player_type = Column(Enum(PlayerType), nullable=False)

  p1 = Column(ForeignKey("players.id"), nullable=True)
  p2 = Column(ForeignKey("players.id"), nullable=True)
  
  team_members = relationship("Player")
  matches = relationship("Match", back_populates="player")
  

class Match(Base):
  __tablename__ = "matches"
  match_id = Column(Integer, primary_key=True)
  tournament = Column(String, nullable=False)
  match_at = Column(DateTime, nullable=False)
  match_type = Column(Enum(PlayerType), nullable=False)

  is_win_p1 = Column(Boolean, nullable=True)
  is_win_p2 = Column(Boolean, nullable=True)

  avg_odds_p1 = Column(Float, nullable=True)
  avg_odds_p2 = Column(Float, nullable=True)

  p1 = Column(String, ForeignKey('players.id'), nullable=False)
  result_p1 = Column(Integer, nullable=True)
  sets_p1 = Column(Integer, nullable=True)
  score1_p1 = Column(Integer, nullable=True)
  score2_p1 = Column(Integer, nullable=True)
  score3_p1 = Column(Integer, nullable=True)
  score4_p1 = Column(Integer, nullable=True)
  score5_p1 = Column(Integer, nullable=True)

  p2 = Column(String, ForeignKey('players.id'), nullable=False)
  result_p2 = Column(Integer, nullable=False)
  sets_p2 = Column(Integer, nullable=False)
  score1_p2 = Column(Integer, nullable=False)
  score2_p2 = Column(Integer, nullable=True)
  score3_p2 = Column(Integer, nullable=True)
  score4_p2 = Column(Integer, nullable=True)
  score5_p2 = Column(Integer, nullable=True)
