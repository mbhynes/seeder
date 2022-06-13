import os
import logging

import datetime

from urllib.parse import urlparse, parse_qs

import scrapy
from seeder.items import MatchItem

logger = logging.getLogger(__name__)


class TennisExplorerSpider(scrapy.Spider):
  
  max_future_days = 7
  name = 'tennisexplorer.com'
  allowed_domains = ['tennisexplorer.com']

  def __init__(self, start_date=None, max_future_date=None, stop_watermark=None, log=logger):
    self.start_date = (
      datetime.fromisoformat(start_date) if start_date is not None 
      else datetime.date.today()
    )
    self.stop_watermark = (
      datetime.fromisoformat(stop_watermark) if stop_watermark is not None
      else None
    )
    self.max_future_date = (
      datetime.fromisoformat(max_future_date) if max_future_date 
      else datetime.date.today() + datetime.timedelta(days=self.max_future_days)
    )
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
      '/results/': self._parse_match_listings,
    }
    url = urlparse(reponse.url)
    parser = endpoint_parsers.get(url.path) 
    if parser:
      yield parser(response)
    else:
      self.log.warn(f"Received reponse for path '{url.path}' which is not in the endpoint parsers mapping.")


  def _parse_match_listings(self, response):
    """
    Parse the match listings / results page for the url:
      tennisexplorer.com/results/{...}
    This method will return:
      - Requests for further player or match info endpoints
      - Requests for listings on other dates
      - Parses match items
    """
    url = urlparse(reponse.url)
    query = parser_qs(url.query)

    def _parse_date(qs):
      y = qs.get('year')
      m = qs.get('month')
      d = qs.get('day')
      if not all(len(y) == 1, len(m) == 1, len(d) == 1):
        self.log.warn(f"Query string for year was unexpected: {query} in {response.url}")
        return None
      try: 
        return parse(f'{y}-{m}-{d}')
      except Exception as e:
        self.log.error(f"Encountered exception {e} when parsing query string '{qs}'")


    # Retrieve links to the next day; each daily match summary
    # page has a set of 3 navigation links:
    #   '« previous day', 'today', 'next day »'
    for href in response.css('li.dNav a::attr(href)').getall():
      year_list = query.get('year')
      if len(year) != 1:
        continue
      yield scrapy.Request(response.urljoin(href), self.parse)
