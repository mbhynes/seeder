import datetime

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
    to_datetime = lambda d: datetime.datetime.fromordinal(d.toordinal())
    today = datetime.date(2000, 1, 1)
    with mock.patch(f'{MODULE}.date') as mock_date:
      mock_date.today.return_value = today
      spider = TennisExplorerSpider()
      self._assert_attributes_equal(spider, {
        'start_date': to_datetime(
          today - datetime.timedelta(days=TennisExplorerSpider.default_start_watermark_offset)
        ),
        'start_watermark': to_datetime(
          today - datetime.timedelta(days=TennisExplorerSpider.default_start_watermark_offset)
        ),
        'stop_watermark': to_datetime(
          today + datetime.timedelta(days=TennisExplorerSpider.default_stop_watermark_offset)
        ),
      })
