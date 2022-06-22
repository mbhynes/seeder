from copy import deepcopy
import logging
import re

from datetime import MINYEAR, datetime, timedelta

from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup
import scrapy

from seeder.items import MatchItem, PlayerItem
from seeder.models import PlayerType
from seeder.spiders.parsers import Parser
from seeder.util.numeric import coerce_int, coerce_float, coerce_timedelta, sum_ignore_none

logger = logging.getLogger(__name__)


class MatchResultParser(Parser):

  def __init__(self, start_watermark, stop_watermark, logger=logger):
    self.start_watermark = start_watermark
    self.stop_watermark = stop_watermark
    self.logger = logger

  @staticmethod
  def _parse_date_from_qs(url, year='year', month='month', day='day'):
    dt = None
    try: 
      qs = parse_qs(urlparse(url).query)
      y = qs.get(year, [])
      m = qs.get(month, [])
      d = qs.get(day, [])
      if all([len(y) == 1, len(m) == 1, len(d) == 1]):
        dt = datetime(int(y[0]), int(m[0]), int(d[0]))
    finally:
      return dt

  def _is_datetime_bounded(self, dt):
    is_notnull = (dt is not None)
    return is_notnull and (self.start_watermark <= dt <= self.stop_watermark)

  def parse_links(self, response):
    """
    Retrieve links to the next day; each daily match summary
    page has a set of 3 navigation links:
      '« previous day', 'today', 'next day »'
    """
    links = []
    # Get the next & previous days' match result links
    for href in response.css('li.dNav a::attr(href)').getall():
      if self._is_datetime_bounded(self._parse_date_from_qs(href)):
        links.append(href)

    # Get all /match-detail/ references from within the 'results' table.
    # Nb we ignore any /match-detail/ refs not in the table such that the db 
    # is populated with matches from an systemtic timespan determined by
    # the start & stop watermarks.
    soup = BeautifulSoup(response.body, 'html.parser')
    table = soup.find('table', class_='result')
    if table:
      for link in table.find_all('a'):
        href = link.attrs.get('href', '')
        if urlparse(href).path == '/match-detail/':
          links.append(href)

    return links

  def parse_items(self, response):
    """
    Parse a match results table into an iterable of items.
    """
    soup = BeautifulSoup(response.body, 'html.parser')
    context = {
      'match_date': self._parse_date_from_qs(response.url), 
      'url':        response.url,
    }
    match_records = []
    tables = soup.find_all('table', class_='result')
    for tab in tables:
      match_records += self._parse_match_table_rows(tab, context)

    return match_records

  def _parse_match_table_rows(self, soup, global_context=None):
    """
    Parse rows of table into an iterable of items.
    """
    def _record_from_row(row, context):
      record = deepcopy(context)
      first_score_col = None
      cols = row.find_all('td')
      ncols = len(cols)
      for (k, col) in enumerate(cols, start=1):
        cls = ' '.join(col.attrs.get('class', []))
        if cls == 'first time':
          record['match_time'] = col.next_element
        elif cls == 't-name':
          record['player'] = col.find('a').attrs.get('href')
        elif cls == 'coursew':
          record['avg_odds_p1'] = col.next_element
        elif cls == 'course':
          record['avg_odds_p2'] = col.next_element
        elif cls == 'result':
          record['result'] = col.next_element
        elif cls == 'score':
          if first_score_col is None:
            first_score_col = k
          key = f'score{k - first_score_col + 1}'
          record[key] = col.next_element
        elif (cls == '') and (k == ncols):
          match_url = col.find('a').attrs.get('href')
          match_number = parse_qs(urlparse(match_url).query).get('id')[0]
          record['match_number'] = match_number
      return record

    def _key_record(row):
      """
      Retrieve the row's id. Each row is one of a pair, e.g. (10, 10b), that signifies
      the "home" and "away" counterpart players for the match.
      """
      pattern = r'r([0-9]+)(b?)'
      key = re.match(pattern, row.attrs.get('id', ''))
      if key:
        return key.groups()
      return None
    
    def _coerce_record_dtypes(record):
      fn_map = {
        'match_time':   coerce_timedelta,
        'match_number':     coerce_int,
        'result':       coerce_int,
        'score1':       coerce_int,
        'score2':       coerce_int,
        'score3':       coerce_int,
        'score4':       coerce_int,
        'score5':       coerce_int,
        'avg_odds_p1':  coerce_float,
        'avg_odds_p2':  coerce_float,
      }
      coerced = {}
      for (key, val) in record.items():
        coerced[key] = fn_map.get(key, lambda _: _)(val)
      return coerced

    def _build_records(rows, global_context):
      records = {}
      context = {}
      for (n, row) in enumerate(rows, start=1):
        # If this row contains a new header, reset the tournament context for the subsequent rows,
        # and then continue to the next row, which contains match result data. 
        if ' '.join(row.attrs.get('class', [])) == 'head flags':
          header_el = row.find('td', class_='t-name')
          tournament_href = header_el.find('a')
          if tournament_href:
            tournament_url = tournament_href.attrs.get('href')
          else:
            # ITF Futures tournaments do not have specific URLs; as a fallback,
            # we take the tag's text and remove non-workd characters from it.
            tournament_url = re.sub(r'[\W]', '',  header_el.text)
          context = {
            **global_context,
            **{'tournament': tournament_url},
          }
          continue
        key = _key_record(row)
        if not key:
          continue
        raw_record =  _record_from_row(row, context)
        records[key] = _coerce_record_dtypes(raw_record)
      return records

    def _merge_player_records(records):
      split_fn = lambda k: k[1] == ''
      left_records = {key[0]: value for (key, value) in records.items() if split_fn(key)}
      right_records = {key[0]: value for (key, value) in records.items() if not split_fn(key)}
      if len(right_records) != len(left_records):
        self.logger.warn(
          f"Detected probable parsing error for url='{global_context.get('url')}\n;"
          "left records do not match right records during merge:\n"
          f"\tleft.keys not in right.keys: {left_records.keys() - right_records.keys()}\n"
          f"\tright.keys not in left.keys: {right_records.keys() - left_records.keys()}"
        )
      merged = []
      for (key, left) in left_records.items():
        try:
          right = right_records[key]
          merged.append(MatchItem({
            'match_number': left['match_number'],
            'tournament':   left['tournament'],
            'match_at':     left['match_date'] + left['match_time'],
            'match_type':   PlayerType.from_url(left['player']),

            'is_win_p1':    (
                left['result'] > right['result'] 
                if all([left.get('result') is not None, right.get('result') is not None])
                else None
              ),
            'is_win_p2':    (
                right['result'] > left['result'] 
                if all([left.get('result') is not None, right.get('result') is not None])
                else None
              ),

            'avg_odds_p1':  left.get('avg_odds_p1'),
            'avg_odds_p2':  left.get('avg_odds_p2'),

            'p1':           left['player'],
            'result_p1':    left.get('result'),
            'sets_p1':      sum_ignore_none(*[left.get(f'score{k}') for k in range(1, 6)]),
            'score1_p1':    left.get('score1'),
            'score2_p1':    left.get('score2'),
            'score3_p1':    left.get('score3'),
            'score4_p1':    left.get('score4'),
            'score5_p1':    left.get('score5'),

            'p2':           right['player'],
            'result_p2':    right.get('result'),
            'sets_p2':      sum_ignore_none(*[right.get(f'score{k}') for k in range(1, 6)]),
            'score1_p2':    right.get('score1'),
            'score2_p2':    right.get('score2'),
            'score3_p2':    right.get('score3'),
            'score4_p2':    right.get('score4'),
            'score5_p2':    right.get('score5'),
          })) 
        except Exception as e:
          self.logger.error(
            f"Encountered exception '{e}' when merging records for {key} from {global_context.get('url')}"
          )
      return merged

    rows = soup.find_all('tr', class_=['head flags', 'one', 'two'])
    context = deepcopy(global_context or {})
    records = _build_records(rows, context)
    return _merge_player_records(records)
