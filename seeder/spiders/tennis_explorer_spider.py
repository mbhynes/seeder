from copy import deepcopy
import logging
import os
import re

from datetime import MINYEAR, datetime, timedelta

from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup
import scrapy

from seeder.items import MatchItem

logger = logging.getLogger(__name__)


class TennisExplorerSpider(scrapy.Spider):
  
  max_future_days = 7
  name = 'tennisexplorer.com'
  allowed_domains = ['tennisexplorer.com']

  def __init__(self, start_date=None, stop_watermark=None, start_watermark=None, log=logger):
    now = datetime.today()
    self.start_date = start_date or now
    self.start_watermark = start_watermark or datetime(MINYEAR, 1, 1)
    self.stop_watermark = stop_watermark or (now + timedelta(days=self.max_future_days))
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
      '/results/': self.parse_match_listings,
    }
    url = urlparse(response.url)
    parser = endpoint_parsers.get(url.path) 
    if parser:
      yield parser(response)
    else:
      self.log.warn(f"Received reponse for path '{url.path}' which is not in the endpoint parsers mapping.")

  def _is_datetime_bounded(self, dt):
    is_notnull = (dt is not None)
    return is_notnull and (self.start_watermark <= dt <= self.stop_watermark)

  def _parse_match_listings(self, response):
    """
    Parse the match listings / results page for the url:
      tennisexplorer.com/results/{...}
    This method will return:
      - Requests for further player or match info endpoints
      - Requests for listings on other dates
      - Parses match items
    """
    soup = BeautifulSoup(response.body, 'html.parser')
    for record in self._parse_match_records(soup, response.url): 
      yield record

    # Retrieve links to the next day; each daily match summary
    # page has a set of 3 navigation links:
    #   '« previous day', 'today', 'next day »'
    for href in response.css('li.dNav a::attr(href)').getall():
      if self._is_datetime_bounded(self._parse_date(href)):
        yield scrapy.Request(response.urljoin(href), self.parse)

  @staticmethod
  def _parse_match_records(soup, url):
    """
    Parse a match results table into an iterable of items.
    """
    context = {
      'match_date': TennisExplorerSpider._parse_date(url), 
    }
    records = []
    tables = soup.find_all('table', class_='result')
    for tab in tables:
      records += TennisExplorerSpider._parse_match_table_rows(tab, context)
    return records

  @staticmethod
  def _parse_match_table_rows(soup, global_context=None):
    """
    Parse rows of table into an iterable of items.
    """
    def _build_player_match_record(row, context):
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
          match_id = parse_qs(urlparse(match_url).query).get('id')[0]
          record['match_id'] = match_id
      return record
    
    def _coerce_record_dtypes(record):
      fn_map = {
        'match_time':   coerce_timedelta,
        'match_id':     coerce_int,
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

    def _build_records(rows, global_context):
      records = {}
      context = {}
      for (n, row) in enumerate(rows, start=1):
        # If this row contains a new header, reset the tournament context for the subsequent rows,
        # and then continue to the next row, which contains match result data. 
        if ' '.join(row.attrs.get('class', [])) == 'head flags':
          context = {
            **global_context,
            **{'tournament': row.find('td', class_='t-name').find('a').attrs.get('href')},
          }
          continue
        key = _key_record(row)
        if not key:
          # logger.warning(f"Could not parse a key from row {n} with text: '{row.text}'")
          continue
        raw_record = _build_player_match_record(row, context)
        records[key] = _coerce_record_dtypes(raw_record)
      return records

    def _merge_player_records(records):
      split_fn = lambda k: k[1] == ''
      left_records = {key[0]: value for (key, value) in records.items() if split_fn(key)}
      right_records = {key[0]: value for (key, value) in records.items() if not split_fn(key)}
      merged = []
      for (key, record) in right_records.items():
        left = left_records[key]
        right = right_records[key]
        merged.append({
          'match_id':     left['match_id'],
          'tournament':   left['tournament'],
          'match_at':     left['match_date'] + left['match_time'],

          'is_win_p1':    left['result'] > right['result'],
          'is_win_p2':    right['result'] > left['result'],

          'avg_odds_p1':  left['avg_odds_p1'],
          'avg_odds_p2':  left['avg_odds_p2'],

          'p1':           left['player'],
          'result_p1':    left['result'],
          'sets_p1':      sum_ignore_none(*[left[f'score{k}'] for k in range(1, 6)]),
          'score1_p1':    left['score1'],
          'score2_p1':    left['score2'],
          'score3_p1':    left['score3'],
          'score4_p1':    left['score4'],
          'score5_p1':    left['score5'],

          'p2':           right['player'],
          'result_p2':    right['result'],
          'sets_p2':      sum_ignore_none(*[right[f'score{k}'] for k in range(1, 6)]),
          'score1_p2':    right['score1'],
          'score2_p2':    right['score2'],
          'score3_p2':    right['score3'],
          'score4_p2':    right['score4'],
          'score5_p2':    right['score5'],
        }) 
      return merged

    rows = soup.find_all('tr', class_=['head flags', 'one', 'two'])
    context = deepcopy(global_context or {})
    records = _build_records(rows, context)
    return _merge_player_records(records)
    return result #[r for r in records.values()]

  @staticmethod
  def _parse_date(url):
    dt = None
    try: 
      qs = parse_qs(urlparse(url).query)
      y = qs.get('year', [])
      m = qs.get('month', [])
      d = qs.get('day', [])
      if all([len(y) == 1, len(m) == 1, len(d) == 1]):
        dt = datetime(int(y[0]), int(m[0]), int(d[0]))
    except Exception as e:
      logger.error(f"Encountered exception: '{e}' when parsing url: '{dt}'")
    finally:
      return dt

def sum_ignore_none(*args):
  result = 0
  for arg in args:
    if arg is not None:
      result += arg
  return result

def coerce_int(x, default=None):
  try:
    return int(x)
  except ValueError:
    return default

def coerce_float(x, default=None):
  try:
    return float(x)
  except ValueError:
    return default

def coerce_timedelta(x, default=timedelta()):
  result = default
  pattern = r"([0-2][0-3]):([0-5][0-5])"
  m = re.match(pattern, x)
  if m is not None:
    hours, minutes = m.groups()
    result = timedelta(hours=groups[0], minutes=groups[11])
  return result
