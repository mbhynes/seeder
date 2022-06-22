from urllib.parse import parse_qs, urlsplit, urlunsplit, urlencode

def update_query(url, params=None):
  """
  Return a url with the provided params upserted into the <query> fragment.
  """
  if params is None:
    return url
  parts = urlsplit(url)
  qs = parse_qs(parts.query)
  upserted_parts = parts._replace(query=urlencode({**qs, **params}))
  return urlunsplit(upserted_parts)
