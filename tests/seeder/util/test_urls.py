import pytest
import datetime

from seeder.util.urls import update_query, date_from_qs

def test_update_query():
  assert update_query('/endpoint/', None) == '/endpoint/'
  assert update_query('/endpoint/', {'a': 0}) == '/endpoint/?a=0'
  assert update_query('/endpoint/?a=0', {'a': 1, 'b': 2}) == '/endpoint/?a=1&b=2'
  assert update_query('/endpoint/?a=0&a=1', {'a': 2, 'b': 2}) == '/endpoint/?a=2&b=2'
  assert update_query('/endpoint/?a=0&a=1', {'b': 2}) == '/endpoint/?a=1&b=2'

def test_date_from_qs():
  expected = datetime.datetime(1, 1, 3)
  assert date_from_qs('/endpoint/?year=0001&month=01&day=3') == expected
  assert date_from_qs('/endpoint/?y=0001&month=1&day=03', year='y') == expected
  assert date_from_qs('/endpoint/?params=wrong', on_errors='coerce') == None

  with pytest.raises(ValueError):
    date_from_qs('/endpoint/?params=wrong', on_errors='raise')

  with pytest.raises(ValueError):
    date_from_qs('/endpoint/?year=2000&month=20&day=1', on_errors='raise')
