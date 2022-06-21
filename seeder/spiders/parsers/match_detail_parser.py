from copy import deepcopy
import logging
import re

import datetime

from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup
import scrapy

from seeder.spiders.parsers import Parser
from seeder.util.numeric import coerce_float, coerce_timedelta

logger = logging.getLogger(__name__)


class MatchDetailParser(Parser):

  def __init__(self, logger=logger, **kwargs):
    self.logger = logger

  def parse_links(self, response):
    return []

  def parse_items(self, response):
    """
    Parse a match results table into an iterable of items.
    """
    return self.parse_moneyline_odds_items(response, global_context={})

  def _parse_match_timestamp(self, response):
    try:
      match_date_text = response.selector.xpath('//*[@id="center"]/div[1]/span/text()').get()
      match_time_text = response.selector.xpath('//*[@id="center"]/div[1]/text()[1]').get()
      if not match_date_text:
        raise ValueError(f"Could not retrieve a match date from {response.url}")
      if not match_time_text:
        raise ValueError(f"Could not retrieve a match start time from {response.url}")

      if match_date_text == 'TODAY':
        match_date = datetime.datetime.fromordinal(datetime.date.today().toordinal())
      else:
        match_date = datetime.datetime.strptime(match_date_text, '%d.%m.%Y')

      match_time = coerce_timedelta(
        match_time_text,
        pattern=r"[,\s]*([01][0-9]|2[0-3]):([0-5][0-9])[,\s]*",
        default=None
      )
      if not match_time:
        raise ValueError(f"Failed to convert the match time '{match_time_tex}' to timedelta for {response.url}")

      return match_date + match_time

    except Exception as e:
      self.logger.error(e)
      return None

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
    if not match_at:
      return []
    soup = BeautifulSoup(response.body, "html.parser")
    root_tab = soup.find(id="oddsMenu-1-data")
    if not root_tab:
      self.logger.error(f"Could not retrieve the data table from '{response.url}'")
      return []

    items = []
    for row in root_tab.find_all("tr", class_=["one", "two"]):
      _it = self._parse_match_odds_records(row, context={'match_at': match_at})
      items += _it
    return items

  def _parse_match_odds_records(self, soup, context):
    """
    Extract each issued odds (transaction fact) for a match for a single row,
    assumed to correspond to a single bookmaker.

    TODO: clean this up.
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
      for ts in sorted(issue_timestamps):
        # Increment the time index for each player. Since the odds for each side of the line
        # maybe updated at different timestamps, this is a convoluted way of performing a
        # full outer join & a forward fill on the series.
        for p in range(len(sorted_odds)):
          if sorted_odds[p][k_last[p]].get('issued_at') == ts:
            last_vals[p] = sorted_odds[p][k_last[p]].get('odds') 
            k_last[p] = min(k_last[p] + 1, len(sorted_odds[p]) - 1)

        record = {
          'issued_at': ts,
          'issued_by': bookmaker,
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
   
    return _merge_odds_series(odds)
