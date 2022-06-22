import os
import datetime
import requests

from unittest import mock
import pytest

import scrapy

from seeder.models import PlayerType
from seeder.items import MatchItem
from seeder.spiders.parsers.match_result_parser import MatchResultParser

class TestMatchResultParser:

  @pytest.mark.vcr()
  def test_parse_items(self):
    base_url = "https://www.tennisexplorer.com/results/?type=all&year={year:04d}&month={month:02d}&day={day:02d}"
    start_date = datetime.datetime(2000, 3, 19)
    url = base_url.format(year=start_date.year, month=start_date.month, day=start_date.day)
    response = scrapy.http.HtmlResponse(url, body=requests.get(url).content)
    actual = MatchResultParser(start_watermark=start_date, stop_watermark=start_date).parse_items(response)

    expected = [MatchItem(**{
      "tournament":   "/indian-wells/2000/atp-men/",
      "match_number": 55469, 
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
    }), MatchItem(**{
      "tournament":   "/indian-wells/2000/atp-men/?type=double",
      "match_number": 55500,
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
    })]

    key = lambda r: r['match_number']
    assert sorted(actual, key=key) == sorted(expected, key=key)

  @pytest.mark.vcr()
  def test_parse_links(self):
    domain = "https://www.tennisexplorer.com"
    path = "/results/?type=all&year={year:04d}&month={month:02d}&day={day:02d}"
    start_date = datetime.datetime(2000, 3, 19)
    url = domain + path.format(year=start_date.year, month=start_date.month, day=start_date.day)
    response = scrapy.http.HtmlResponse(url, body=requests.get(url).content)
    actual = MatchResultParser(
      start_watermark=(start_date - datetime.timedelta(days=1)),
      stop_watermark=(start_date + datetime.timedelta(days=1)),
    ).parse_links(response)

    expected = [
      path.format(year=start_date.year, month=start_date.month, day=start_date.day - 1),
      path.format(year=start_date.year, month=start_date.month, day=start_date.day + 1),
      "/match-detail/?id=55469",
      "/match-detail/?id=55500",
    ]
    assert sorted(actual) == sorted(expected)

  @pytest.mark.vcr()
  def test_parse_links_outside_watermarks(self):
    domain = "https://www.tennisexplorer.com"
    path = "/results/?type=all&year={year:04d}&month={month:02d}&day={day:02d}"
    start_date = datetime.datetime(2000, 3, 19)
    url = domain + path.format(year=start_date.year, month=start_date.month, day=start_date.day)
    response = scrapy.http.HtmlResponse(url, body=requests.get(url).content)
    actual = MatchResultParser(
      start_watermark=start_date,
      stop_watermark=start_date,
    ).parse_links(response)

    expected = [
      "/match-detail/?id=55469",
      "/match-detail/?id=55500",
    ]
    assert sorted(actual) == sorted(expected)
