import datetime
import enum
import uuid

from urllib.parse import urlparse

from sqlalchemy import ForeignKey, Column
from sqlalchemy import Integer, String, Boolean, DateTime, Float, Enum
from sqlalchemy_utils import UUIDType

from sqlalchemy.orm import declarative_base, relationship

from seeder.db import upsert_record 


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
	created_at._creation_order = 1000
	updated_at._creation_order = 1001
  

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


class Crawl(BaseModel):
  __tablename__ = "crawls"

  crawl_id = Column(UUIDType(binary=True), primary_key=True)
  spider_name = Column(String)

  start_watermark = Column(DateTime, nullable=False)
  stop_watermark = Column(DateTime, nullable=False)

  @classmethod
  def add(cls, session, spider):
    return upsert_record(session, cls, {
      'crawl_id': spider.crawl_id,
      'spider_name': spider.name,
      'start_watermark': spider.start_watermark,
      'stop_watermark': spider.stop_watermark,
    })


class CrawledUrl(BaseModel):
  __tablename__ = "crawled_urls"

  url_id = Column(UUIDType(binary=True), primary_key=True, default=uuid.uuid4)
  url = Column(String, nullable=False, index=True)
  is_crawled = Column(Boolean, default=False, nullable=False)
  last_crawled_at = Column(DateTime, nullable=True)
  last_crawl_id = Column(UUIDType(binary=True), ForeignKey("crawls.crawl_id"), nullable=True)

  last_crawl = relationship("Crawl", foreign_keys=[last_crawl_id])

  @staticmethod
  def _key_url(url):
    return uuid.uuid5(uuid.NAMESPACE_URL, url)

  @classmethod
  def add(cls, session, url):
    return upsert_record(session, cls, {
      'url_id': cls._key_url(url),
      'url': url,
    })

  @classmethod
  def update(cls, session, spider, url):
    return upsert_record(session, cls, {
      'url_id': cls._key_url(url),
      'url': url,
      'is_crawled': True,
      'last_crawled_at': datetime.datetime.utcnow(),
      'last_crawl_id': spider.crawl_id,
    })
 

class Player(BaseModel):
  __tablename__ = "players"

  player_id = Column(String, primary_key=True)
  name = Column(String)
  player_type = Column(Enum(PlayerType), nullable=False)

  p1 = Column(String, ForeignKey("players.player_id"))
  member1 = relationship("Player", foreign_keys=[p1], remote_side=[player_id])

  p2 = Column(String, ForeignKey("players.player_id"))
  member2 = relationship("Player", foreign_keys=[p2], remote_side=[player_id])
  

class Match(BaseModel):
  __tablename__ = "matches"
  match_id = Column(Integer, primary_key=True)
  tournament = Column(String, nullable=False)
  match_at = Column(DateTime, nullable=False, index=True)
  match_type = Column(Enum(PlayerType), nullable=False)

  is_win_p1 = Column(Boolean)
  is_win_p2 = Column(Boolean)

  avg_odds_p1 = Column(Float)
  avg_odds_p2 = Column(Float)

  p1 = Column(String, ForeignKey('players.player_id'), nullable=False, index=True)
  result_p1 = Column(Integer)
  sets_p1 = Column(Integer)
  score1_p1 = Column(Integer)
  score2_p1 = Column(Integer)
  score3_p1 = Column(Integer)
  score4_p1 = Column(Integer)
  score5_p1 = Column(Integer)

  p2 = Column(String, ForeignKey('players.player_id'), nullable=False, index=True)
  result_p2 = Column(Integer)
  sets_p2 = Column(Integer)
  score1_p2 = Column(Integer)
  score2_p2 = Column(Integer)
  score3_p2 = Column(Integer)
  score4_p2 = Column(Integer)
  score5_p2 = Column(Integer)

  player1 = relationship("Player", foreign_keys=[p1])
  player2 = relationship("Player", foreign_keys=[p2])
