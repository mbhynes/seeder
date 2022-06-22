import datetime

from urllib.parse import parse_qs, urlparse, urlsplit, urlunsplit

def update_query(url, params=None):
  """
  Return a url with the provided params upserted into the <query> fragment.
  """
  if params is None:
    return url
  parts = urlsplit(url)
  qs = {k: v[-1] for (k,v) in parse_qs(parts.query).items() if len(v) > 0}
  upserted_query = {**qs, **params}
  upserted_qs = '&'.join(f'{k}={v}' for (k, v) in upserted_query.items())
  upserted_parts = parts._replace(query=upserted_qs)
  return urlunsplit(upserted_parts)

def date_from_qs(url, year='year', month='month', day='day', on_errors='raise'):
  """
  Extract a datetime.datetime from the query string parameters of a given url.
  """
  assert on_errors in ['raise', 'coerce']
  dt = None
  try: 
    qs = parse_qs(urlparse(url).query)
    y = qs.get(year, [])
    m = qs.get(month, [])
    d = qs.get(day, [])
    if all([len(y) > 0, len(m) > 0, len(d) > 0]):
      dt = datetime.datetime(int(y[-1]), int(m[-1]), int(d[-1]))
    else:
      raise ValueError("Failed to parse year/month/date from query='{qs}'")
  except Exception as e:
    if on_errors == 'raise':
      raise ValueError(f"Failed to parse date from url='{url}'" + repr(e)) from None
  finally:
    if (on_errors == 'raise') and (dt is None):
      raise ValueError(f"Failed to parse date from url='{url}'")
    return dt
