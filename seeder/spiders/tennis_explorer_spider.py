from copy import deepcopy
import logging
import os
import re

from datetime import MINYEAR, date, datetime, timedelta

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
  
  default_start_watermark_offset = 3
  default_stop_watermark_offset = 7
  name = 'tennisexplorer'
  allowed_domains = ['tennisexplorer.com']

  def __init__(self, *args, start_date=None, stop_watermark=None, start_watermark=None, **kwargs):
    super().__init__(*args, **kwargs)
    today = datetime.fromordinal(date.today().toordinal())
    self.start_date = start_date or today
    self.start_watermark = (
      start_watermark 
      or (today - timedelta(days=self.default_start_watermark_offset))
    )
    self.stop_watermark = (
      stop_watermark 
      or (today + timedelta(days=self.default_stop_watermark_offset))
    )
    ctx = {
      'logger': self.logger,
      'start_watermark': self.start_watermark,
      'stop_watermark': self.stop_watermark,
    }
    self.parsers = {endpoint: cls(**ctx) for (endpoint, cls) in self.ENDPOINT_PARSERS.items()}
    self.logger.info(f"Running {type(self)} spider over watermark span [{self.start_watermark}, {self.stop_watermark}] starting from {self.start_date}.")

  @classmethod
  def from_crawler(cls, crawler, *args, **kwargs):
    def _parse_datetime(d):
      if d is None:
        return None
      if type(d) is str:
        try:
          return datetime.fromisoformat(d)
        except ValueError as e:
          logger.error(f"Failed to parse string '{d}' using datetime.fromisoformat.")
          raise e from None
      return d
    spider = super(TennisExplorerSpider, cls).from_crawler(
      crawler,
      *args,
      start_date=_parse_datetime(crawler.settings.get('SEEDER_START_DATE')),
      stop_watermark=_parse_datetime(crawler.settings.get('SEEDER_STOP_WATERMARK')),
      start_watermark=_parse_datetime(crawler.settings.get('SEEDER_START_WATERMARK')),
      **kwargs
    )
    return spider

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
      self.logger.warn(f"Received reponse for path '{url.path}' which is not in the endpoint parsers mapping.")
      return

    for item in parser.parse_items(response):
      yield item

    for href in parser.parse_links(response):
      yield scrapy.Request(response.urljoin(href), self.parse)
