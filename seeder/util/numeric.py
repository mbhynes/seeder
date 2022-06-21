import re
from datetime import timedelta

def sum_ignore_none(*args):
  result = 0
  nnz = 0
  for arg in args:
    if arg is not None:
      result += arg
      nnz += 1
  if nnz > 0:
    return result
  return None

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

def coerce_timedelta(x, pattern=r"([01][0-9]|2[0-3]):([0-5][0-9])", default=timedelta()):
  result = default
  m = re.match(pattern, x)
  if m is not None:
    hours, minutes = m.groups()
    result = timedelta(
      hours=coerce_int(hours, default=0),
      minutes=coerce_int(minutes, default=0)
    )
  return result
