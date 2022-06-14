import os
import logging

from datetime import MINYEAR, datetime, timedelta

from urllib.parse import urlparse, parse_qs

import scrapy
from seeder.items import MatchItem

logger = logging.getLogger(__name__)


class TennisExplorerSpider(scrapy.Spider):
  
  max_future_days = 7
  name = 'tennisexplorer.com'
  allowed_domains = ['tennisexplorer.com']

  def __init__(self, start_date=None, stop_watermark=None, start_watermark=None, log=logger):
    now = datetime.today()
    self.start_date = start_date or now
    self.start_watermark = start_watermark or datetime(MINYEAR, 1, 1)
    self.stop_watermark = stop_watermark or (now + timedelta(days=self.max_future_days))
    self.log = log

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
    # TODO; put this mapping into the constructor
    endpoint_parsers = {
      '/results/': self.parse_match_listings,
    }
    url = urlparse(reponse.url)
    parser = endpoint_parsers.get(url.path) 
    if parser:
      yield parser(response)
    else:
      self.log.warn(f"Received reponse for path '{url.path}' which is not in the endpoint parsers mapping.")

  def _is_datetime_bounded(self, dt):
    is_notnull = (dt is not None)
    return is_notnull and (self.start_watermark <= dt <= self.stop_watermark)

  def _parse_match_listings(self, response):
    """
    Parse the match listings / results page for the url:
      tennisexplorer.com/results/{...}
    This method will return:
      - Requests for further player or match info endpoints
      - Requests for listings on other dates
      - Parses match items
    """
    def _parse_date(url):
      dt = None
      try: 
        qs = parse_qs(urlparse(url).query)
        y = qs.get('year', [])
        m = qs.get('month', [])
        d = qs.get('day', [])
        if all([len(y) == 1, len(m) == 1, len(d) == 1]):
          dt = datetime(int(y[0]), int(m[0]), int(d[0]))
      except Exception as e:
        self.log.error(f"Encountered exception: '{e}' when parsing url: '{dt}'")
      finally:
        return dt

    # Retrieve links to the next day; each daily match summary
    # page has a set of 3 navigation links:
    #   '« previous day', 'today', 'next day »'
    for href in response.css('li.dNav a::attr(href)').getall():
      if self._is_datetime_bounded(_parse_date(href)):
        self.log.warning(href)
        yield scrapy.Request(response.urljoin(href), self.parse)
