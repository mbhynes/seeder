import logging
import os
import sqlalchemy
from scrapy.utils.project import get_project_settings

from sqlalchemy import select, inspect

logger = logging.getLogger(__name__)

SEEDER_DB_CONN_STR = 'SEEDER_DB_CONN_STR'


def get_engine(conn_str=None, **kwargs):
  """
  Create a sqlalchemy engine.
  """
  engine_args = get_project_settings().get('SEEDER_SQLALCHEMY_ENGINE_ARGS', {})
  conn_str = (
    conn_str 
    or os.getenv('SEEDER_DB_CONN_STR')
    or get_project_settings('SEEDER_DB_CONN_STR') 
  )
  if not conn_str:
    raise ValueError(f"No ${SEEDER_DB_CONN_STR} is set in the settings.py or environment.")
  dialect = conn_str.split(':')[0]
  _args = dict(engine_args.get(dialect, {}), **kwargs)
  return sqlalchemy.create_engine(conn_str, **_args)


def upsert_record(sessionmaker, model, record):
  """
  Update a dictionary record to a row of the provided model. 
  """
  primary_keys = inspect(model).primary_key
  missing_keys = set([pk.name for pk in primary_keys]) - record.keys()
  if len(missing_keys) > 0:
    raise ValueError(f"Cannot upsert item; missing primary keys: [{missing_keys}]")
  where_payload = {
    pk.name: record.get(pk.name)
    for pk in primary_keys
  }
  with sessionmaker() as session:
    current = session.get(model, where_payload)
    if current:
      for key, val in record.items():
        setattr(current, key, val)
    else:
      session.add(model(**record))
    session.commit()
    success = True
  return success 

def upsert_item(sessionmaker, item):
  """
  Upsert (insert or update) an item to the database. 

  The item must map to a single model using its __model__ attribute,
  which will be used to construct a primary key set and retrieve the
  record to update, if it exists, or create it.
  """
  return upsert_record(sessionmaker, item.__model__, dict(item))
