"""
Scrapy crawler and database configuration settings.

For more information, see: https://docs.scrapy.org/en/latest/topics/settings.html
"""
import datetime
import logging
import sqlalchemy

# ========================================================
# Scrapy configuration settings
# ========================================================

LOG_LEVEL = logging.INFO
BOT_NAME = 'seeder'

SPIDER_MODULES = ['seeder.spiders']
NEWSPIDER_MODULE = 'seeder.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 16

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 2

# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
  'seeder.middlewares.UrlCacheMiddleware': 543,
}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
EXTENSIONS = {
}

# Configure item pipelines.
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
  'seeder.pipelines.DatabasePipeline': 300,
}

# ========================================================
# Databse configuration settings.
# ========================================================

# Set the sqlalchemy engine database connection string.
# NOTE: Do *not* hardcode sensitive data in this connection string in production databases;
# Instead set the $SEEDER_DB_CONN_STR environment variable:
#   export SEEDER_DB_CONN_STR='mysql://sensitivestring'
SEEDER_DB_CONN_STR = 'sqlite:///private/seeder.test.db'

SEEDER_SQLALCHEMY_ENGINE_ARGS = {
  'sqlite': {},

  # Run with a single-threaded pool
  # (http://docs.sqlalchemy.org/en/latest/core/pooling.html#sqlalchemy.pool.SingletonThreadPool)
  'mysql': {
    'connect_args': {
      "connect_timeout": 1,
    },
    'isolation_level': 'READ_COMMITTED',
    'poolclass': sqlalchemy.pool.StaticPool,
    'pool_recycle': 5 * 60,
  }
}

# Set seeder endpoints to exclude from crawling. Adding an entry here controls whether the
# spider will make further requessts for certain endpoints, e.g. '/match-detail/'.
# If you don't want to crawl these (e.g. to speed up a specific crawl), they can be removed.
SEEDER_EXCLUDE_ENDPOINTS = []

# Set the date for which to start a match listing crawl.
# This is the date to submit in the query string to the /results/ endpoint:
#   https://www.tennisexplorer.com/results/?type=all&year=<YEAR>&month=<MONTH>&day=<DAY>
# If set to None, this will default to datetime.date.now().
SEEDER_START_DATE = None

# Set the earliest date for which the /results/ pages should be crawled
# For backfills, this should be a date in the past from which point data is desired
# If set to None, this will default to today - 3 days
SEEDER_START_WATERMARK = None

# Set the latest date for which the /results/ pages should be crawled
# If set to None, this will default to today + 7 days
SEEDER_STOP_WATERMARK = None
