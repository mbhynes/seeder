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
    url = base_url.format(year=2000, month=3, day=19)
    response = scrapy.http.HtmlResponse(url, body=requests.get(url).content)
    spider = TennisExplorerSpider()
    results = list(spider._parse_match_listings(response))

    # Assert the next set of requests are created
    actual_requests = [r.url for r in results if type(r) is scrapy.Request]
    expected_requests = [
      base_url.format(year=2000, month=3, day=18),
      base_url.format(year=2000, month=3, day=20),
    ]
    assert sorted(actual_requests) == sorted(expected_requests)

    # Assert the items have been collected
    actual_records = [r for r in results if type(r) is dict]
    expected_records = [{
      "tournament":   "/indian-wells/2000/atp-men/",
      "match_id":     55469, 
      "match_at":     datetime.datetime(2000, 3, 19),
      "is_win_p1":    True,
      "is_win_p2":    False,
      "avg_odds_p1":  None,
      "avg_odds_p2":  None,
      "p1":           "/player/corretja/",
      "result_p1":    3,
      "sets_p1":      18,
      "score1_p1":    6,
      "score2_p1":    6,
      "score3_p1":    6,
      "score4_p1":    None,
      "score5_p1":    None,
      "p2":           "/player/enqvist/",
      "result_p2":    0,
      "sets_p2":      11,
      "score1_p2":    4,
      "score2_p2":    4,
      "score3_p2":    3,
      "score4_p2":    None,
      "score5_p2":    None,
    }, {
      "tournament":   "/indian-wells/2000/atp-men/?type=double",
       "match_id":    55500,
       "match_at":    datetime.datetime(2000, 3, 19),
       "is_win_p1":   True,
       "is_win_p2":   False,
       "avg_odds_p1": None,
       "avg_odds_p2": None,
       "p1":          "/doubles-team/o-brien/palmer/",
       "result_p1":   2,
       "sets_p1":     13,
       "score1_p1":   6,
       "score2_p1":   7,
       "score3_p1":   None,
       "score4_p1":   None,
       "score5_p1":   None,
       "p2":          "/doubles-team/haarhuis/stolle/",
       "result_p2":   0,
       "sets_p2":     10,
       "score1_p2":   4,
       "score2_p2":   6,
       "score3_p2":   None,
       "score4_p2":   None,
       "score5_p2":   None,
    }]
    key = lambda r: r['match_id']
    assert sorted(actual_records, key=key) == sorted(expected_records, key=key)
