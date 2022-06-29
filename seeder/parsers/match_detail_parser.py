import logging
import re

import datetime

from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup
import scrapy

from seeder.models import MatchSurface
from seeder.items import MatchOddsItem, MatchItem
from seeder.parsers import Parser
from seeder.util.numeric import coerce_float, coerce_int, coerce_timedelta

logger = logging.getLogger(__name__)


class MatchDetailParser(Parser):
  """
  Parse a MatchOddsItem instance for each odds change record in the moneyline 
  odds table of a match on a /match-details/ page of tennisexplorer.com:
    tennisexplorer.com/match-detail/?id=<match>.

  Bugs/Caveats:
    - Matches that have only a single line provided by a bookmaker do not have a
      timestamp for when the line was issued at on the site. As such, we can't determine
      whether these lines are opening odds or closing odds, and must assume they are closing.
      It's possible to estimate the opening timestamp as the minimum of all bookies'
      lines' issue timestamps, but this is left to downstream consumers since we cannot
      make any guarantees of the accuracy. The timestamps appear to be on the partner site
      oddsportal.com.

  TODOs:
    - Refactor the parsers methods, especially the convoluted full outer join of dictionaries
    - Add parsers (& models) for bets other than moneyline
  """

  def __init__(self, logger=logger, **kwargs):
    self.logger = logger

  def parse_links(self, response):
    return []

  def parse_items(self, response):
    """
    Parse a match results table into an iterable of items.
    """
    odds_items = self._parse_moneyline_odds_items(response, global_context={})
    match_items = self._parse_match_items(response, global_context={})
    return odds_items + match_items

  def _parse_match_timestamp(self, response):
    try:
      match_date_text = response.selector.xpath('//*[@id="center"]/div[1]/span/text()').get()
      match_time_text = response.selector.xpath('//*[@id="center"]/div[1]/text()[1]').get()
      if not match_date_text:
        raise ValueError(f"Could not retrieve a match date from {response.url}")
      if not match_time_text:
        raise ValueError(f"Could not retrieve a match start time from {response.url}")

      if match_date_text.lower().strip() == 'today':
        match_date = datetime.datetime.fromordinal(datetime.date.today().toordinal())
      else:
        match_date = datetime.datetime.strptime(match_date_text, '%d.%m.%Y')

      match_time = coerce_timedelta(
        match_time_text,
        pattern=r"[,\s]*([01][0-9]|2[0-3]):([0-5][0-9])[,\s]*",
        default=None
      )
      if not match_time:
        self.logger.error(f"Failed to convert the match time '{match_time_text}' to timedelta for {response.url}")
        match_time = datetime.timedelta()

      return match_date + match_time

    except Exception as e:
      self.logger.error(e)
      return None


  def _parse_match_round(self, response):
    """
    Parse the round text describing when the match occurred in the tournament order
    from the html of a /match-detail/ page. The html fragment we are parsing looks like:
    <div class="box boxBasic lGray">
      <span class="upper">19.06.2022</span>, 14:25, <a href="...">Tournament</a>, Round, Surface
    </div>
    """
    try:

      text = response.selector.xpath('//*[@id="center"]/div[1]/text()').getall()[-1]
      if not text:
        raise ValueError(f"Could not retrieve match metadata text from {response.url}")
      tokens = text.split(',')
      if len(tokens) < 2:
        raise ValueError(f"Could not parse round tokens from {response.url}")
      return tokens[-2].strip()
    except Exception as e:
      self.logger.error(e)
      return None

  def _parse_match_surface(self, response):
    """
    Parse the surface (grass/clay/etc) from the html of a /match-detail/ page. 
    The html fragment we are parsing looks like: 
    <div class="box boxBasic lGray">
      <span class="upper">19.06.2022</span>, 14:25, <a href="...">Tournament</a>, Round, Surface
    </div>
    """
    try:
      text = response.selector.xpath('//*[@id="center"]/div[1]/text()').getall()[-1]
      if not text:
        raise ValueError(f"Could not retrieve match metadata text from {response.url}")
      tokens = text.strip().split(',')
      if len(tokens) == 0:
        raise ValueError(f"Could not parse surface tokens from {response.url}")
      return MatchSurface.from_string(tokens[-1])
    except Exception as e:
      self.logger.error(e)
      return MatchSurface.unknown

  def _parse_moneyline_odds_items(self, response, global_context={}):
    """
    Extract a transaction fact table of match odds issued by each available
    bookmaker for the moneyline wager.

    The tennisexplorer /match-details/ pages provide a table of the bookmakers'
    provided odds, with an embedded list of the odds changes with a miminum 
    resolution of 1 minute for each change they've detected. We extract each
    change for each bookmaker as a distinct fact record.
    """
    match_at = self._parse_match_timestamp(response)
    match_number = coerce_int(parse_qs(urlparse(response.url).query)['id'][0])
    if not match_at:
      return []
    soup = BeautifulSoup(response.body, "html.parser")
    root_tab = soup.find(id="oddsMenu-1-data")
    if not root_tab:
      self.logger.error(f"Could not retrieve the data table from '{response.url}'")
      return []

    context = {
      'match_at': match_at,
      'match_number': match_number,
    }
    items = []
    for row in root_tab.find_all("tr", class_=["one", "two"]):
      _it = self._parse_match_odds_records(row, context=context)
      items += _it
    return items
  
  def _parse_match_items(self, response):
    # Add the parial match item to upsert (to get the surface & round) 
    return [MatchItem(
      match_number=coerce_int(parse_qs(urlparse(response.url).query)['id'][0]),
      match_surface=self._parse_match_surface(response),
      match_round=self._parse_match_round(response),
    )]

  def _parse_match_odds_records(self, soup, context):
    """
    Extract each issued odds (transaction fact) for a match for a single row,
    assumed to correspond to a single bookmaker.

    TODO: refactor this to make it cleaner.
    """
    assert 'match_at' in context
    year = context['match_at'].year
    bookmaker = soup.find("td").find("span", class_="t").next_element
    odds_divs = soup.find_all("div", class_="odds-in")
    if len(odds_divs) != 2:
      self.logger.error(
        f"Expected 2 odds change div columns for {bookmaker} but found {len(odds_change_divs)}"
      )
      return None

    def _merge_odds_series(odds):
      issue_timestamps = set([o['issued_at'] for o in odds[0]] + [o['issued_at'] for o in odds[1]])
      sorted_odds = [
        sorted(odds[0], key=lambda r: r['issued_at']),
        sorted(odds[1], key=lambda r: r['issued_at']),
      ]
      last_vals = [None, None]
      k_last = [0, 0]
      records = []
      num_timestamps = len(issue_timestamps)
      for idx, ts in enumerate(sorted(issue_timestamps), start=1):
        # Increment the time index for each player. Since the odds for each side of the line
        # maybe updated at different timestamps, this is a convoluted way of performing a
        # full outer join & a forward fill on the series.
        for p in range(len(sorted_odds)):
          if sorted_odds[p][k_last[p]].get('issued_at') == ts:
            last_vals[p] = sorted_odds[p][k_last[p]].get('odds') 
            k_last[p] = min(k_last[p] + 1, len(sorted_odds[p]) - 1)

        record = {
          'match_number': context['match_number'],
          'issued_by': bookmaker,
          'issued_at': ts,
          'index': idx,
          'index_rev': num_timestamps - (idx - 1),
          'is_opening': (idx == 1) and (ts < context['match_at']), # opening must be issued strictkly before match time 
          'is_closing': (idx == num_timestamps),
          'odds_p1': last_vals[0],
          'odds_p2': last_vals[1],
        }
        records.append(record)

      return records

    odds = [
      [],
      [],
    ]
    timestamps = []
    for p, div in enumerate(odds_divs):
      # Try to find an odds-change-div, which contains the table of
      # odds changes issued by the bookmaker if multiple were issued.
      odds_changes = div.find('div', class_='odds-change-div')
      if odds_changes:
        for r in odds_changes.find_all("tr"):
          fields = r.find_all('td')
          # Ignore rows with the "Opening Odds" header
          if len(fields) != 3:
            self.logger.debug(f"Skipping row {r} with only {len(fields)} fields; expected 3.")
            continue

          odds[p].append({
            'issued_at': datetime.datetime.strptime(f"{year}.{fields[0].text}", "%Y.%d.%m. %H:%M"),
            'odds': coerce_float(fields[1].text),
          })
      else:
        # If there is no issued at timestamp, assume that the odds represent the closing line
        odds[p].append({
          'issued_at': context.get('match_at'),
          'odds': coerce_float(div.text),
        })
   
    result = _merge_odds_series(odds)
    return [MatchOddsItem(**r) for r in result]
