import datetime

from seeder.util.numeric import sum_ignore_none, coerce_int, coerce_float, coerce_timedelta

def test_sum_ignore_none():
  assert sum_ignore_none(None) == None
  assert sum_ignore_none(None, 1) == 1
  assert sum_ignore_none(None, 1, 1) == 2

def test_coerce_int():
  assert coerce_int('1') == 1
  assert coerce_int('asd1') == None

def test_coerce_float():
  assert coerce_float('1.0') == 1.0
  assert coerce_float('asd1.0') == None

def test_coerce_timedelta():
  assert coerce_timedelta('00:00') == datetime.timedelta()
  assert coerce_timedelta('00:01') == datetime.timedelta(minutes=1)
  assert coerce_timedelta('00:59') == datetime.timedelta(minutes=59)
  assert coerce_timedelta('01:00') == datetime.timedelta(hours=1)
  assert coerce_timedelta('23:00') == datetime.timedelta(hours=23)
  assert coerce_timedelta('23:59') == datetime.timedelta(hours=23, minutes=59)

  assert coerce_timedelta('fail') == datetime.timedelta()
  assert coerce_timedelta('fail', default=None) == None
