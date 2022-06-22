import logging
from seeder.db import DatabaseMixin, default_engine, upsert_record
from seeder.models import BaseModel

logger = logging.getLogger(__name__)


class DatabasePipeline(DatabaseMixin):

  def __init__(self, engine=default_engine, **kwargs):
    super().__init__(engine=engine, **kwargs)

  def open_spider(self, spider):
    self.create_all(BaseModel)

  def process_item(self, item, spider):
    records = item.make_with_dependencies()
    for r in records:
      try:
        success = upsert_record(self.sessionmaker, r)
        if not success:
          raise ValueError(f"Failed to upsert record '{r}' created by item: {item}")
      except Exception as e:
        spider.logger.error(f"Encountered exception '{e}' when upserting {item}")
    return item
