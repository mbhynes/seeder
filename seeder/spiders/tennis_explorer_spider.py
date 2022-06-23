from copy import deepcopy
import logging
import os
import re
import uuid

from datetime import MINYEAR, date, datetime, timedelta

from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup
import scrapy

from seeder.items import MatchItem
from seeder.parsers.match_result_parser import MatchResultParser
from seeder.parsers.match_detail_parser import MatchDetailParser
from seeder.util.urls import update_query

logger = logging.getLogger(__name__)


class TennisExplorerSpider(scrapy.Spider):

  ENDPOINT_PARSERS = {
    '/results/': {
      'parser': MatchResultParser,
      'parser_kwargs': {},
      'request_kwargs': {'priority': 1},
    },
    '/next/': {
      'parser': MatchResultParser,
      'parser_kwargs': {},
      'request_kwargs': {'priority': 1},
    },
    '/match-detail/': {
      'parser': MatchDetailParser,
      'parser_kwargs': {},
      'request_kwargs': {'priority': 0},
    },
  }
  
  default_start_watermark_offset = 2
  default_stop_watermark_offset = 3
  name = 'tennisexplorer'
  allowed_domains = ['tennisexplorer.com']

  def __init__(self, *args, start_date=None, start_watermark=None, stop_watermark=None, exclude_endpoints=None, **kwargs):
    super().__init__(*args, **kwargs)
    self.crawl_id = uuid.uuid4()
    today = datetime.fromordinal(date.today().toordinal())
    self.start_watermark = (
      start_watermark 
      or (today - timedelta(days=self.default_start_watermark_offset))
    )
    self.stop_watermark = (
      stop_watermark 
      or (today + timedelta(days=self.default_stop_watermark_offset))
    )
    self.start_date = start_date or min(self.start_watermark, self.stop_watermark)
    assert self.stop_watermark >= self.start_watermark
    assert self.start_date >= self.start_watermark

    ctx = {
      'logger': self.logger,
      'start_watermark': self.start_watermark,
      'stop_watermark': self.stop_watermark,
    }
    self.parsers = {
      endpoint: config['parser'](**ctx, **config.get('parser_kwargs', {})) 
      for (endpoint, config) in self.ENDPOINT_PARSERS.items()
      if endpoint not in (exclude_endpoints or set())
    }
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
      start_watermark=_parse_datetime(crawler.settings.get('SEEDER_START_WATERMARK')),
      stop_watermark=_parse_datetime(crawler.settings.get('SEEDER_STOP_WATERMARK')),
      exclude_endpoints=crawler.settings.getlist('SEEDER_EXCLUDE_ENDPOINTS'),
      **kwargs
    )
    return spider

  def start_requests(self):
    url = "https://www.tennisexplorer.com/results/?type=all&year={year}&month={month}&day={day}&timezone=+0".format(
      year=self.start_date.strftime('%Y'),
      month=self.start_date.strftime('%m'),
      day=self.start_date.strftime('%d'),
    )
    yield scrapy.Request(url, self.parse)

  def parse(self, response):
    """
    Parsing responses into further requests or items.

    This method is an entrypoint to route responses to respective parse methods
    based on the url path, but doesn't do any parsing itself.
    """
    url = urlparse(response.url)
    parser = self.parsers.get(url.path) 
    if not parser:
      self.logger.debug(
        f"{self.name.title()} spider got response for '{url.path}' but has no parser for this endpoint.")
      return

    for item in parser.parse_items(response):
      yield item

    for href in parser.parse_links(response):
      endpoint = urlparse(href).path
      if endpoint not in self.parsers:
        self.logger.debug(f"{self.name.title()} spider has no parser for '{endpoint}': SKIPPING '{href}'")
        continue
      request_kwargs = self.ENDPOINT_PARSERS.get(endpoint, {}).get('request_kwargs', {})
      url = update_query(response.urljoin(href), {'timezone': '+0'}) # UTC timestamps only
      yield scrapy.Request(url, self.parse, **request_kwargs)
