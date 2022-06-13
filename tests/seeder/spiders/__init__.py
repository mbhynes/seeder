import datetime
import unittest
import importlib

from unittest import mock

from seeder.spiders import TennisExplorerSpider

MODULE = 'seeder.spiders'


class TestTennisExplorerSpider(unittest.TestSuite):

  def _assert_attributes_equal(self, obj, reference):
    paylaod = {getattr(obj, key) for key in reference}
    self.assertEquals(payload, reference)

  @mock.patch(f'{MODULE}.datetime.date.today', datetime.date(2000, 1, 1))
  def test_init_default_args(self, mock_today):
    spider = TennisExplorerSpider()
    self._assert_attributes_equal(spider, {
      'start_date': datetime.date(2000, 1, 1),
      'max_future_date': None,
      'stop_watermark': None,
    })

