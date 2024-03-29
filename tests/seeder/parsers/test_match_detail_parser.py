import datetime
import requests

from unittest import mock
import pytest

import scrapy

from seeder.items import MatchOddsItem, MatchItem
from seeder.models import MatchSurface
from seeder.parsers.match_detail_parser import MatchDetailParser


class TestMatchDetailParser:

  @pytest.mark.vcr()
  def test_parse_moneyline_odds_items(self):
    url = "https://www.tennisexplorer.com/match-detail/?id=2121735&timezone=+0"
    response = scrapy.http.HtmlResponse(url, body=requests.get(url).content)
    parser = MatchDetailParser()

    # Take only a subset of the (many) records to test.
    # TODO: find a match-details page with a reasonable number of records to VCR
    actual_records = [
      dict(r) for r in parser._parse_moneyline_odds_items(response)
      if r.get('issued_by') in set(['bet365', '188bet'])
    ]
    expected_records = [
      {
        'match_number': 2121735,
        'issued_by': '188bet',
        'issued_at': datetime.datetime(2022, 6, 19, 14, 25), 
        'index': 1,
        'index_rev': 1,
        'is_opening': False, # Since there is no issue timestamp provided, this can't be treated as "opening"
        'is_closing': True,
        'odds_p1': 1.53,
        'odds_p2': 2.32,
      }, {
        'match_number': 2121735,
        'issued_by': 'bet365',
        'issued_at': datetime.datetime(2022, 6, 19, 4, 34), 
        'index': 1,
        'index_rev': 3,
        'is_opening': True,
        'is_closing': False,
        'odds_p1': 1.72,
        'odds_p2': 2.00,
      }, {
        'match_number': 2121735,
        'issued_by': 'bet365',
        'issued_at': datetime.datetime(2022, 6, 19, 9, 10), 
        'index': 2,
        'index_rev': 2,
        'is_opening': False,
        'is_closing': False,
        'odds_p1': 1.61,
        'odds_p2': 2.20,
      }, {
        'match_number': 2121735,
        'issued_by': 'bet365',
        'issued_at': datetime.datetime(2022, 6, 19, 9, 51), 
        'index': 3,
        'index_rev': 1,
        'is_opening': False,
        'is_closing': True,
        'odds_p1': 1.53,
        'odds_p2': 2.37,
      }
    ]
    key = lambda r: (r['match_number'], r['issued_by'], r['issued_at'])
    assert sorted(actual_records, key=key) == sorted(expected_records, key=key)

  @pytest.mark.vcr()
  def test_parse_match_items(self):
    url = "https://www.tennisexplorer.com/match-detail/?id=2121735&timezone=+0"
    response = scrapy.http.HtmlResponse(url, body=requests.get(url).content)
    parser = MatchDetailParser()

    actual_records = [
      dict(r) for r in parser._parse_match_items(response)
    ]
    expected_records = [{
      'match_number': 2121735, 
      'match_surface': MatchSurface.grass,
      'match_round': 'Qualification - quarterfinal',
    }]
    key = lambda r: r['match_number']
    assert sorted(actual_records, key=key) == sorted(expected_records, key=key)
