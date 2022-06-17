import datetime
import requests

from unittest import mock
import pytest

import scrapy

from seeder.spiders.tennis_explorer_spider import TennisExplorerSpider
from seeder.models import PlayerType
from seeder.items import MatchItem, PlayerItem

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
        'start_date': to_datetime(today),
        'start_watermark': to_datetime(
          today - datetime.timedelta(days=TennisExplorerSpider.default_start_watermark_offset)
        ),
        'stop_watermark': to_datetime(
          today + datetime.timedelta(days=TennisExplorerSpider.default_stop_watermark_offset)
        ),
      })

  @pytest.mark.vcr()
  def test_parse_results_endpoint(self):
    base_url = "https://www.tennisexplorer.com/results/?type=all&year={year:04d}&month={month:02d}&day={day:02d}"
    start_date = datetime.datetime(2000, 3, 19)
    url = base_url.format(year=start_date.year, month=start_date.month, day=start_date.day)
    response = scrapy.http.HtmlResponse(url, body=requests.get(url).content)
    spider = TennisExplorerSpider(
      start_date=start_date,
      start_watermark=start_date - datetime.timedelta(days=1),
      stop_watermark=start_date + datetime.timedelta(days=1),
    )
    results = list(spider.parse(response))

    # Assert the next set of requests are created
    actual_requests = [r.url for r in results if type(r) is scrapy.Request]
    expected_requests = [
      base_url.format(year=start_date.year, month=start_date.month, day=start_date.day - 1),
      base_url.format(year=start_date.year, month=start_date.month, day=start_date.day + 1),
    ]
    assert sorted(actual_requests) == sorted(expected_requests)

    spider.log.error("Printing results:")
    spider.log.error([type(r) for r in results])
    # Assert the items have been collected
    actual_records = [dict(r) for r in results if type(r) is MatchItem]
    expected_records = [{
      "tournament":   "/indian-wells/2000/atp-men/",
      "match_id":     55469, 
      "match_at":     datetime.datetime(2000, 3, 19),
      "match_type":   PlayerType.single,
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
      "match_id":     55500,
      "match_at":     datetime.datetime(2000, 3, 19),
      "match_type":   PlayerType.double,
      "is_win_p1":    True,
      "is_win_p2":    False,
      "avg_odds_p1":  None,
      "avg_odds_p2":  None,
      "p1":           "/doubles-team/o-brien/palmer/",
      "result_p1":    2,
      "sets_p1":      13,
      "score1_p1":    6,
      "score2_p1":    7,
      "score3_p1":    None,
      "score4_p1":    None,
      "score5_p1":    None,
      "p2":           "/doubles-team/haarhuis/stolle/",
      "result_p2":    0,
      "sets_p2":      10,
      "score1_p2":    4,
      "score2_p2":    6,
      "score3_p2":    None,
      "score4_p2":    None,
      "score5_p2":    None,
    }]
    key = lambda r: r['match_id']
    assert sorted(actual_records, key=key) == sorted(expected_records, key=key)

    actual_records = [dict(r) for r in results if type(r) is PlayerItem]
    expected_records = [{
      "player_id":    "/player/corretja/",
      "player_type":  PlayerType.single,
      "p1":           None,
      "p2":           None,
    }, {
      "player_id":    "/player/enqvist/",
      "player_type":  PlayerType.single,
      "p1":           None,
      "p2":           None,
    }, {
      "player_id":    "/player/o-brien/",
      "player_type":  PlayerType.single,
      "p1":           None,
      "p2":           None,
    }, {
      "player_id":    "/player/palmer/",
      "player_type":  PlayerType.single,
      "p1":           None,
      "p2":           None,
    }, {
      "player_id":    "/player/haarhuis/",
      "player_type":  PlayerType.single,
      "p1":           None,
      "p2":           None,
    }, {
      "player_id":    "/player/stolle/",
      "player_type":  PlayerType.single,
      "p1":           None,
      "p2":           None,
    }, {
      "player_id":    "/doubles-team/o-brien/palmer/",
      "player_type":  PlayerType.double,
      "p1":           "/player/o-brien/",
      "p2":           "/player/palmer/",
    }, {
      "player_id":   "/doubles-team/haarhuis/stolle/",
      "player_type":  PlayerType.double,
      "p1":           "/player/haarhuis/",
      "p2":           "/player/stolle/",
    }]
    key = lambda r: r['player_id']
    assert sorted(actual_records, key=key) == sorted(expected_records, key=key)
