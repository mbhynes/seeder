import logging

from scrapy import signals

from seeder.db import DatabaseMixin, default_engine, upsert_item
from seeder.models import BaseModel, Crawl, CrawledUrl


class UrlCacheMiddleware(DatabaseMixin):
  """
  Populate a crawl & URL metadata table of when pages have been crawled 
  """

  def __init__(self, engine=default_engine):
    super().__init__(engine=engine)

  @classmethod
  def from_crawler(cls, crawler):
    middleware = cls()
    crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
    return middleware

  def process_spider_input(self, response, spider):
    CrawledUrl.insert(self.sessionmaker, response.url)
    return None

  def process_spider_output(self, response, result, spider):
    CrawledUrl.update(self.sessionmaker, spider, response.url)
    for i in result:
      yield i

  def spider_opened(self, spider):
    self.create_all(BaseModel)
    Crawl.insert(self.sessionmaker, spider)
