import datetime
import logging
import sqlalchemy

LOG_LEVEL = logging.INFO
BOT_NAME = 'seeder'

SPIDER_MODULES = ['seeder.spiders']
NEWSPIDER_MODULE = 'seeder.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'seeder (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 2

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 2

# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#  'seeder.middlewares.SeederSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#  'seeder.middlewares.SeederDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#  'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
  'seeder.pipelines.DatabasePipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

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

