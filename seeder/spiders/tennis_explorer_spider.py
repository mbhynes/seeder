from copy import deepcopy
import logging
import os
import re

from datetime import MINYEAR, datetime, timedelta

from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup
import scrapy

from seeder.items import MatchItem
from seeder.spiders.parsers.match_parser import MatchParser

logger = logging.getLogger(__name__)


class TennisExplorerSpider(scrapy.Spider):

  ENDPOINT_PARSERS = {
    '/results/': MatchParser,
  }
  
  max_future_days = 7
  name = 'tennisexplorer'
  allowed_domains = ['tennisexplorer.com']

  def __init__(self, start_date=None, stop_watermark=None, start_watermark=None, log=logger):
    now = datetime.today()
    self.start_date = start_date or now
    self.start_watermark = start_watermark or datetime(MINYEAR, 1, 1)
    self.stop_watermark = stop_watermark or (now + timedelta(days=self.max_future_days))
    self.log = log
    ctx = {
      'log': self.log,
      'start_watermark': self.start_watermark,
      'stop_watermark': self.stop_watermark,
    }
    self.parsers = {endpoint: cls(**ctx) for (endpoint, cls) in self.ENDPOINT_PARSERS.items()}

  @classmethod
  def from_crawler(cls, crawler):
    return cls(
      start_date=crawler.settings.get('SEEDER_START_DATE'),
      stop_watermark=crawler.settings.get('SEEDER_STOP_WATERMARK'),
      start_watermark=crawler.settings.get('SEEDER_START_WATERMARK'),
    )

  def start_requests(self):
    url = "https://www.tennisexplorer.com/results/?type=all&year={year}&month={month}&day={day}".format(
      year=self.start_date.strftime('%Y'),
      month=self.start_date.strftime('%m'),
      day=self.start_date.strftime('%d'),
    )
    yield scrapy.Request(url, self.parse)

  def parse(self, response):
    """
    Parsing responses into further requests or items.

    This method is an entrypoint to route reponses to respective parse methods
    based on the url path, but doesn't do any parsing itself.
    """
    url = urlparse(response.url)
    parser = self.parsers.get(url.path) 
    if not parser:
      self.log.warn(f"Received reponse for path '{url.path}' which is not in the endpoint parsers mapping.")
      return

    for item in parser.parse_items(response):
      yield item

    for href in parser.parse_links(response):
      yield scrapy.Request(response.urljoin(href), self.parse)
