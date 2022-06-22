import datetime
import enum
import re
import uuid

from urllib.parse import urlparse

from sqlalchemy import ForeignKey, Column
from sqlalchemy import Integer, String, Boolean, DateTime, Float, Enum
from sqlalchemy_utils import UUIDType

from sqlalchemy.orm import declarative_base, relationship

from seeder.db import upsert_dict


class Base(object):

  UUID_NAMESPACE = uuid.NAMESPACE_URL

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

  @classmethod
  def surrogate_key(cls, *args, **kwargs):
    raise NotImplementedError
 
  @classmethod
  def make(cls, **kwargs):
    return cls(**kwargs)

  @classmethod
  def make_dependencies(cls, *args, **kwargs):
    return []
  
  @classmethod
  def make_with_dependencies(cls, **kwargs):
    record = cls.make(**kwargs)
    deps = cls.make_dependencies(**kwargs)
    return deps + [record]

  def to_partial_dict(self):
    return {k: v for (k, v) in self.to_dict().items() if v is not None}

  def to_dict(self):
    return {
      column.name: getattr(self, column.name)
      for column in self.__table__.columns
    }



BaseModel = declarative_base(cls=Base)


class Crawl(BaseModel):
  __tablename__ = "crawls"

  crawl_id = Column(UUIDType(binary=True), primary_key=True)
  spider_name = Column(String)

  start_watermark = Column(DateTime, nullable=False)
  stop_watermark = Column(DateTime, nullable=False)

  @classmethod
  def surrogate_key(cls, spider):
    return spider.crawl_id

  @classmethod
  def insert(cls, session, spider):
    return upsert_dict(session, cls, {
      'crawl_id': cls.surrogate_key(spider),
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

  @classmethod
  def surrogate_key(cls, url):
    return uuid.uuid5(cls.UUID_NAMESPACE, url)

  @classmethod
  def insert(cls, session, url):
    return upsert_dict(session, cls, {
      'url_id': cls.surrogate_key(url),
      'url': url,
    })

  @classmethod
  def update(cls, session, spider, url):
    return upsert_dict(session, cls, {
      'url_id': cls.surrogate_key(url),
      'url': url,
      'is_crawled': True,
      'last_crawled_at': datetime.datetime.utcnow(),
      'last_crawl_id': spider.crawl_id,
    })
 

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

  player_id = Column(UUIDType(binary=True), primary_key=True, default=uuid.uuid4)
  slug = Column(String, index=True)
  name = Column(String)
  player_type = Column(Enum(PlayerType))

  p1 = Column(UUIDType(binary=True), ForeignKey("players.player_id"))
  member1 = relationship("Player", foreign_keys=[p1], remote_side=[player_id])

  p2 = Column(UUIDType(binary=True), ForeignKey("players.player_id"))
  member2 = relationship("Player", foreign_keys=[p2], remote_side=[player_id])

  @staticmethod
  def parse_slugs(slug):
    player_type = PlayerType.from_url(slug)
    if player_type == PlayerType.double:
      matches = re.match(r"/doubles-team/([\w\-]+)/([\w\-]+)/", slug)
      if not matches:
        raise ValueError(f"Could not parse doubles slug from {slug}")
      slugs = matches.groups()
      return (f'/player/{slugs[0]}/', f'/player/{slugs[1]}/')
    return slug

  @classmethod
  def surrogate_key(cls, slug):
    if slug is None:
      return None
    path = urlparse(slug).path
    return uuid.uuid5(cls.UUID_NAMESPACE, path)

  @classmethod
  def make(cls, **kwargs):
    payload = dict(**kwargs)
    slug = kwargs['slug']
    player_type = kwargs.get('player_type', PlayerType.from_url(slug))
    payload['player_id'] = cls.surrogate_key(slug)
    payload['player_type'] = kwargs.get('player_type', PlayerType.from_url(slug))
    if player_type == PlayerType.double:
      slugs = cls.parse_slugs(slug)
      payload['p1'] = cls.surrogate_key(kwargs.get('p1', slugs[0]))
      payload['p2'] = cls.surrogate_key(kwargs.get('p2', slugs[1]))
    return cls(**payload)

  @classmethod
  def make_dependencies(cls, **kwargs):
    slug = kwargs['slug']
    player_type = kwargs.get('player_type', PlayerType.from_url(slug))
    if player_type == PlayerType.double:
      slugs = cls.parse_slugs(slug)
      return [
        cls.make(slug=slugs[0]),
        cls.make(slug=slugs[1]),
      ]
    return []
  

class Match(BaseModel):
  __tablename__ = "matches"

  match_id = Column(UUIDType(binary=True), primary_key=True)
  match_number = Column(Integer, index=True)
  tournament = Column(String)
  match_at = Column(DateTime, index=True)
  match_type = Column(Enum(PlayerType))

  is_win_p1 = Column(Boolean)
  is_win_p2 = Column(Boolean)

  avg_odds_p1 = Column(Float)
  avg_odds_p2 = Column(Float)

  p1 = Column(UUIDType(binary=True), ForeignKey('players.player_id'), index=True)
  result_p1 = Column(Integer)
  sets_p1 = Column(Integer)
  score1_p1 = Column(Integer)
  score2_p1 = Column(Integer)
  score3_p1 = Column(Integer)
  score4_p1 = Column(Integer)
  score5_p1 = Column(Integer)

  p2 = Column(UUIDType(binary=True), ForeignKey('players.player_id'), index=True)
  result_p2 = Column(Integer)
  sets_p2 = Column(Integer)
  score1_p2 = Column(Integer)
  score2_p2 = Column(Integer)
  score3_p2 = Column(Integer)
  score4_p2 = Column(Integer)
  score5_p2 = Column(Integer)

  player1 = relationship("Player", foreign_keys=[p1])
  player2 = relationship("Player", foreign_keys=[p2])

  @classmethod
  def surrogate_key(cls, match_number):
    if match_number is None:
      return None
    return uuid.uuid5(cls.UUID_NAMESPACE, str(match_number))

  @classmethod
  def make(cls, **kwargs):
    payload = dict(**kwargs)
    payload['match_id'] = cls.surrogate_key(kwargs['match_number'])
    payload['p1'] = Player.surrogate_key(kwargs.get('p1'))
    payload['p2'] = Player.surrogate_key(kwargs.get('p2'))
    return cls(**payload)

  @classmethod
  def make_dependencies(cls, **kwargs):
    deps = []
    for player in ['p1', 'p2']:
      slug = kwargs.get(player)
      if slug:
        deps += Player.make_with_dependencies(slug=slug)
    return deps


class MatchOdds(BaseModel):
  __tablename__ = "match_odds"

  match_odds_id = Column(UUIDType(binary=True), primary_key=True, default=uuid.uuid4)
  match_id = Column(UUIDType(binary=True), ForeignKey("matches.match_id"))
  match_number = Column(Integer, index=True)
  issued_by = Column(String, index=True)
  issued_at = Column(DateTime, index=True)
  index = Column(Integer, index=True)
  index_rev = Column(Integer, index=True)
  is_opening = Column(Boolean)
  is_closing = Column(Boolean)
  odds_p1 = Column(Float)
  odds_p2 = Column(Float)

  issued_for = relationship("Match", foreign_keys=[match_id])

  @classmethod
  def surrogate_key(cls, match_number, issued_by, issued_at):
    name = '-'.join([str(match_number), issued_by, str(issued_at.timestamp())])
    return uuid.uuid5(cls.UUID_NAMESPACE, name)

  @classmethod
  def make(cls, **kwargs):
    payload = dict(**kwargs)
    payload['match_odds_id'] = cls.surrogate_key(
      kwargs['match_number'],
      kwargs['issued_by'],
      kwargs['issued_at'],
    )
    return cls(**payload)

  @classmethod
  def make_dependencies(cls, **kwargs):
    return [
      Match.make(match_number=kwargs['match_number'])
    ]
