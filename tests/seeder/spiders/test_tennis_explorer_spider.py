import datetime
import requests

from unittest import mock
import pytest

import scrapy

from seeder.spiders.tennis_explorer_spider import TennisExplorerSpider

MODULE = 'seeder.spiders.tennis_explorer_spider'


class TestTennisExplorerSpider:

  def _assert_attributes_equal(self, obj, reference):
    payload = {key: getattr(obj, key) for key in reference}
    assert payload == reference

  def test_init_default_args(self):
    today = datetime.datetime(2000, 1, 1)
    min_date = datetime.datetime(datetime.MINYEAR, 1, 1)
    with mock.patch(f'{MODULE}.datetime') as mock_date:
      mock_date.today.return_value = today
      mock_date.return_value = min_date
      spider = TennisExplorerSpider()
      self._assert_attributes_equal(spider, {
        'start_date': today,
        'start_watermark': min_date,
        'stop_watermark': today + datetime.timedelta(days=TennisExplorerSpider.max_future_days),
      })

  @pytest.mark.vcr()
  def test_parse_match_listings(self):
    base_url = "https://www.tennisexplorer.com/results/?type=all&year={year:04d}&month={month:02d}&day={day:02d}"
    url = base_url.format(year=2000, month=1, day=8)
    response = scrapy.http.HtmlResponse(url, body=requests.get(url).content)
    spider = TennisExplorerSpider()
    results = list(spider._parse_match_listings(response))

    actual_requests = [r.url for r in results if type(r) is scrapy.Request]
    expected_requests = [
      base_url.format(year=2000, month=1, day=7),
      base_url.format(year=2000, month=1, day=9),
    ]
    assert sorted(actual_requests) == sorted(expected_requests)
