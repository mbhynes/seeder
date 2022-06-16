import datetime
import enum

from urllib.parse import urlparse

from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy import Integer, String, Boolean, DateTime, Float, Enum

from sqlalchemy.orm import declarative_base, relationship


class Base(object):
	created_at = Column(
    DateTime(),
    default=datetime.datetime.utcnow,
    index=True,
  )
	updated_at = Column(
    DateTime(),
    onupdate=datetime.datetime.utcnow,
    default=datetime.datetime.utcnow,
    index=True,
  )
	updated_at._creation_order = 1000
	created_at._creation_order = 1000
  

BaseModel = declarative_base(cls=Base)


class PlayerType(enum.Enum):
  single = 1
  double = 2

  @classmethod
  def from_url(cls, url):
    path = urlparse(url).path
    if path.startswith('/player/'):
      return cls.single
    elif path.startswith('/doubles-team/'):
      return cls.double
    raise ValueError(f"url path {path} is not a valid endpoint.")


class Player(BaseModel):
  __tablename__ = "players"

  player_id = Column(String, primary_key=True)
  name = Column(String)
  player_type = Column(Enum(PlayerType), nullable=False)

  p1 = Column(String, ForeignKey("players.player_id"), nullable=True)
  member1 = relationship("Player", foreign_keys=[p1], remote_side=[player_id])

  p2 = Column(String, ForeignKey("players.player_id"), nullable=True)
  member2 = relationship("Player", foreign_keys=[p2], remote_side=[player_id])
  

class Match(BaseModel):
  __tablename__ = "matches"
  match_id = Column(Integer, primary_key=True)
  tournament = Column(String, nullable=False)
  match_at = Column(DateTime, nullable=False, index=True)
  match_type = Column(Enum(PlayerType), nullable=False)

  is_win_p1 = Column(Boolean, nullable=True)
  is_win_p2 = Column(Boolean, nullable=True)

  avg_odds_p1 = Column(Float, nullable=True)
  avg_odds_p2 = Column(Float, nullable=True)

  p1 = Column(String, ForeignKey('players.player_id'), nullable=False, index=True)
  result_p1 = Column(Integer, nullable=True)
  sets_p1 = Column(Integer, nullable=True)
  score1_p1 = Column(Integer, nullable=True)
  score2_p1 = Column(Integer, nullable=True)
  score3_p1 = Column(Integer, nullable=True)
  score4_p1 = Column(Integer, nullable=True)
  score5_p1 = Column(Integer, nullable=True)

  p2 = Column(String, ForeignKey('players.player_id'), nullable=False, index=True)
  result_p2 = Column(Integer, nullable=False)
  sets_p2 = Column(Integer, nullable=False)
  score1_p2 = Column(Integer, nullable=False)
  score2_p2 = Column(Integer, nullable=True)
  score3_p2 = Column(Integer, nullable=True)
  score4_p2 = Column(Integer, nullable=True)
  score5_p2 = Column(Integer, nullable=True)

  player1 = relationship("Player", foreign_keys=[p1])
  player2 = relationship("Player", foreign_keys=[p2])