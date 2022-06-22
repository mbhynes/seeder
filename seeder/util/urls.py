from urllib.parse import parse_qs, urlsplit, urlunsplit

def update_query(url, params=None):
  """
  Return a url with the provided params upserted into the <query> fragment.
  """
  if params is None:
    return url
  parts = urlsplit(url)
  qs = parse_qs(parts.query)
  upserted_query = {**qs, **params}
  upserted_qs = '&'.join(f'{k}={v}' for (k, v) in upserted_query.items())
  upserted_parts = parts._replace(query=upserted_qs)
  return urlunsplit(upserted_parts)
