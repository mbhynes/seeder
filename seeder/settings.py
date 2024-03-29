"""
Scrapy crawler and database configuration settings.

For more information, see: https://docs.scrapy.org/en/latest/topics/settings.html
"""
import os
import datetime
import logging
import sqlalchemy

# ========================================================
# Scrapy configuration settings
# ========================================================

LOG_LEVEL = logging.INFO
BOT_NAME = 'seederbot'

SPIDER_MODULES = ['seeder.spiders']
NEWSPIDER_MODULE = 'seeder.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
DOWNLOAD_DELAY = 0
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8
AUTOTHROTTLE_DEBUG = True
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

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
# Scrapy caching settings
# ========================================================
# We wish to cache the response html to enable faster 
# database restatement if errors in the parsers are detected,
# or if new models are developed from the html pages.

HTTPCACHE_ENABLED = True
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.DbmCacheStorage'
HTTPCACHE_POLICY = 'scrapy.extensions.httpcache.DummyPolicy'
HTTPCACHE_EXPIRATION_SECS = 0 # if zero, don't expire
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [404]
HTTPCACHE_IGNORE_MISSING = False
HTTPCACHE_GZIP = True
HTTPCACHE_ALWAYS_STORE = True



# ========================================================
# Databse configuration settings.
# ========================================================

# Set the sqlalchemy engine database connection string.
# NOTE: Do *not* hardcode sensitive data in this connection string in production databases;
# Instead set the $SEEDER_DB_CONN_STR environment variable:
#   export SEEDER_DB_CONN_STR='mysql://sensitivestring'
SEEDER_DB_CONN_STR = 'sqlite:///private/seeder.db'

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
