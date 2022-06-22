from seeder.util.urls import update_query

def test_update_query():
  assert update_query('/endpoint/', None) == '/endpoint/'
  assert update_query('/endpoint/', {'a': 0}) == '/endpoint/?a=0'
  assert update_query('/endpoint/?a=0', {'a': 1, 'b': 2}) == '/endpoint/?a=1&b=2'
