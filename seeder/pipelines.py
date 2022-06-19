import logging
from seeder.db import DatabaseMixin, default_engine, upsert_item
from seeder.models import BaseModel

logger = logging.getLogger(__name__)


class DatabasePipeline(DatabaseMixin):

  def __init__(self, engine=default_engine):
    super().__init__(engine=engine)

  def open_spider(self, spider):
    self.create_all(BaseModel)

  def process_item(self, item, spider):
    try:
      success = upsert_item(self.sessionmaker, item)
      if not success:
        raise ValueError(f"Failed to upsert item: {item}")
    except Exception as e:
      spider.logger.error(f"Encountered exception '{e}' when upserting {item}")
    return item
