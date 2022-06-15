import re
from datetime import timedelta

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
