import datetime
from dateutil import parse
import os

import scrapy
from seeder.items import MatchItem

class MySpider(scrapy.Spider):
  name = 'tennisexplorer.com'
  allowed_domains = ['tennisexplorer.com']

  def __init__(self, start_date=None):
    self.start_date = parse(start_date) if start_date is not None else datetime.date.today()

  def start_requests(self):
    url = "https://www.tennisexplorer.com/results/?type=all&year={year}&month={month}&day={day}".format(
      year=self.start_date.strftime('%Y'),
      month=self.start_date.strftime('%m'),
      day=self.start_date.strftime('%d'),
    )
    yield scrapy.Request(url, self.parse)

  def parse(self, response):

    # Retrieve links to the next day; each daily match summary
    # page has a set of 3 navigation links:
    #   '« previous day', 'today', 'next day »'
    for href in response.css('li.dNav a::attr(href)').getall():
      yield scrapy.Request(response.urljoin(href), self.parse)
