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
  conn_str = conn_str or os.getenv('SEEDER_DB_CONN_STR')
  if not conn_str:
    raise ValueError(f"No ${SEEDER_DB_CONN_STR} is set in the environment or provided to get_engine().")
  dialect = conn_str.split(':')[0]
  _args = dict(engine_args.get(dialect, {}), **kwargs)
  return sqlalchemy.create_engine(conn_str, **_args)


def upsert_item(item, sessionmaker):
  """
  Upsert (insert or update) an item to the database. 

  The item must map to a single model using its __model__ attribute,
  which will be used to construct a primary key set and retrieve the
  record to update, if it exists, or create it.
  """
  success = False
  model = item.__model__
  primary_keys = inspect(model).primary_key
  missing_keys = set([pk.name for pk in primary_keys]) - item.keys()
  if len(missing_keys) > 0:
    raise ValueError(f"Cannot upsert item; missing primary keys: [{missing_keys}]")
  where_payload = {
    pk.name: item.get(pk.name)
    for pk in primary_keys
  }
  with sessionmaker() as session:
    record = session.get(model, where_payload)
    if not record:
      session.add(item.to_model())
    else:
      for key, val in item.items():
        setattr(record, key, val)
    session.commit()
    success = True
  return success 

default_engine = get_engine()


class DatabaseMixin(object):

  def __init__(self, engine=default_engine, **kwargs):
    super().__init__(**kwargs)
    self.engine = engine
    self.sessionmaker = sqlalchemy.orm.sessionmaker(bind=engine)

  def create_all(self, base_model):
    base_model.metadata.create_all(self.engine)
