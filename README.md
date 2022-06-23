# `seeder`

`seeder` is a data scraping and management package for [tennisexplorer.com](https://www.tennisexplorer.com).
It allows you to periodically scrape and store the player and match data in a relational SQL database.

![Example Scraping Workflow](doc/_static/seeder.gif)

## Installation

1. **Clone the repository**
```bash
git clone git@github.com:mbhynes/seeder.git
```

2. **Set up the `virtualenv` and install the dependencies:**

The dependencies and `virtualenv` setup is handled by running the `dev` script:
```bash
./dev up
```

3. **Check that the package passes its tests:**

```bash
./dev test

dev-test: Thu 16 Jun 2022 17:46:17 EDT: INFO: Running dev-test with env:
   ROOT_DIR=.
============================================ test session starts =============================================
platform darwin -- Python 3.9.10, pytest-7.1.2, pluggy-1.0.0
rootdir: /Users/mike/src/github.com/mbhynes/seeder
plugins: vcr-1.0.2
collected 2 items

tests/seeder/spiders/test_tennis_explorer_spider.py ..                                                 [100%]

============================================= 2 passed in 0.57s ==============================================
```

## Running A Spider

1. **Set the connection string `SEEDER_DB_CONN_STR` in the environment**

  - This string is the fully-specified connection string to pass to `sqlalchemy`'s [`create_engine`](https://docs.sqlalchemy.org/en/14/core/engines.html#sqlalchemy.create_engine) function
  - The dialect, username, password, etc should all be contained here (i.e. not in any VCS-tracked file or `settings.py`)
```bash
# for initial testing, use a sqlite (local file) database
export SEEDER_DB_CONN_STR='sqlite:///private/seeder.db' 
```

2. **Run the spider with the `scrapy` CLI or `dev crawl`** 

```bash
# Run scrapy directly
source .venv/bin/activate
scrapy crawl tennisexplorer

# Or use the convenience wrapper
./dev crawl
```

3. **Inspect the resulting database**

 - Dump out an example record from the sqlite db file:
```bash
sqlite3 -line private/seeder.db 'select * from matches limit 1;'

   match_id = 2118041
 tournament = /chiang-rai-7-itf/2022/wta-women/
   match_at = 2022-06-16 10:00:00.000000
 match_type = single
  is_win_p1 = 1
  is_win_p2 = 0
avg_odds_p1 = 1.54
avg_odds_p2 = 2.28
         p1 = /player/ueda-dd577/
  result_p1 = 2
    sets_p1 = 13
  score1_p1 = 7
  score2_p1 = 6
  score3_p1 =
  score4_p1 =
  score5_p1 =
         p2 = /player/ounmuang/
  result_p2 = 0
    sets_p2 = 8
  score1_p2 = 5
  score2_p2 = 3
  score3_p2 =
  score4_p2 =
  score5_p2 =
 updated_at = 2022-06-16 20:41:12.870986
 created_at = 2022-06-16 20:41:12.870989
```

## Configuration

### Spider Crawl Configuration

The spider crawl timespan is configured such that only the match `/results/` pages in the datetime interval `[SEEDER_START_WATERMARK, SEEDER_STOP_WATERMARK]` will be crawled and parsed, using the following parameters in `settings.py`:
```
import datetime

# Set the date for which to start a match listing crawl.
# This is the date to submit in the query string to the /results/ endpoint:
#   https://www.tennisexplorer.com/results/?type=all&year=<YEAR>&month=<MONTH>&day=<DAY>
SEEDER_START_DATE = datetime.datetime(2022, 1, 1) 

# Set the earliest date for which the /results/ pages should be crawled
SEEDER_START_WATERMARK = datetime.datetime(2021, 1, 1) 

# Set the latest date for which the /results/ pages should be crawled
SEEDER_STOP_WATERMARK = datetime.datetime(2022, 1, 1) 
```

If unset or set to `None`, these will default to a sane span of `[today - 2 days, today + 3 days]`, which is reasonable for daily incremental crawls.

To manage the database, the start and stop watermarks may be used to populate the tables with minimal requests, e.g.:

1. **Initial Backfill**

  - Run an initial backfill to populate the data starting from a fixed point in the past:

```bash
source .venv/bin/activate
scrapy crawl tennisexplorer \
  -s SEEDER_START_WATERMARK='2021-01-01' \
  -s SEEDER_START_DATE='2021-07-01' \
```
  
  - This should produce output like the following:

```
scrapy crawl tennisexplorer -s SEEDER_START_DATE=2021-07-01 -s SEEDER_START_WATERMARK=2021-01-01
2022-06-17 09:09:16 [scrapy.utils.log] INFO: Scrapy 2.5.0 started (bot: seeder)
2022-06-17 09:09:16 [tennisexplorer] INFO: Running <class 'seeder.spiders.tennis_explorer_spider.TennisExplorerSpider'> spider over watermark span [2021-01-01 00:00:00, 2022-06-24 00:00:00] starting from 2021-07-01 00:00:00.
2022-06-17 09:09:16 [scrapy.middleware] INFO: Enabled item pipelines:
['seeder.pipelines.DatabasePipeline']
2022-06-17 09:09:16 [scrapy.core.engine] INFO: Spider opened
2022-06-17 09:09:16 [scrapy.extensions.logstats] INFO: Crawled 0 pages (at 0 pages/min), scraped 0 items (at 0 items/min)
2022-06-17 09:09:16 [scrapy.extensions.telnet] INFO: Telnet console listening on 127.0.0.1:6023
2022-06-17 09:10:16 [scrapy.extensions.logstats] INFO: Crawled 16 pages (at 16 pages/min), scraped 13857 items (at 13857 items/min)
2022-06-17 09:11:16 [scrapy.extensions.logstats] INFO: Crawled 32 pages (at 16 pages/min), scraped 30894 items (at 17037 items/min)
...
```
    
2. **Incremental Crawl**

  - Every day (suppose), run an incremental crawl using a start watermark that overlaps slightly with the previous crawl's stop watermark
  - The default values of the start and stop watermark of `[today - 3 days, today + 7 days]` are intended to be sane defaults for this use case, in which a small overlap is desirable (since we upsert records and wish to capture changes after matches are played & the results are available)

```bash
source .venv/bin/activate
scrapy crawl tennisexplorer
```

## Data Model

The data model is specified with `sqlalchemy` models in the module [seeder.models](seeder/blob/main/seeder/models.py).

The model is summarized in the below Entity Relational Diagram (ERD), in which the black entities are implemented and the **red** entities are aspirational models that are **not** implemented (but which would be nice to have and possible if the spider were extended).

![Data Model ERD](doc/_static/erd.tennisexplorer.com.drawio.svg)

The entities in this model are as follows:

  - **Match**

    - Grain: 1 row per scheduled match in the spider's watermark timespan
    - Source Endpoints: 
      - [`/results/`](https://www.tennisexplorer.com/results/)
      - [`/next/`](https://www.tennisexplorer.com/next/)
    - A `Match` contains *both* singles and doubles matches in a single table, differentiated by the `match_type` field. This is an relatively opinionated decision, but it has several advantages: (1) it reduces the number of tables to manage [i.e. there is no need for `DoublesMatch`, `SinglesMatch`, `Player`, `Team`] and (2) would still correctly handle weird shit like [Canadian doubles](https://en.wikipedia.org/wiki/Canadian_doubles) if you were ever so inclined to want that in your database. Some people just have more fun.
    - Currently the spider just walks linearly from the `/results/` page for the `$SEEDER_START_DATE`. (And naturally You could just grab the html with a basic `curl` command like
     ```bash
     curl -O https://www.tennisexplorer.com/results/?type=all&year=2022&month=01&day=[1-31]
     ```
      and then parse the html, but this won't scale very well in terms of human effort if you want to periodically and incrementally crawl, inspect error logs, manage schemas, etc...) 


  - **Player**

    - Grain: 1 row per player **or** team that has had at least 1 match in the spider's watermark timespan
    - Source Endpoints: 
      - [`/player/`](https://www.tennisexplorer.com/player/)
      - [`/doubles-team/`](https://www.tennisexplorer.com/doubles-team/)
    - A `Player` record may be either a `PlayerType.single` or `PlayerType.double`, in which latter case the members of the doubles team may be retrieved with the self-referential foreign keys `p1` and `p2`. No attempt is made to order these, since we preserve the ordering from the `/doubles-team/` endpoint. 
    - Please note that we currently don't crawl the `/player/` or `/doubles-team/` endpoints directly; we issue a skeleton record to maintain referential integrityj

## Implementation Details

### Crawler Components

The crawler system makes use of several `scrapy` components: 
- [spiders](https://docs.scrapy.org/en/latest/topics/spiders.html) for managing the crawl
- [item pipelines](https://docs.scrapy.org/en/latest/topics/item-pipeline.html) for upserting records to the database
- [spider middleware](https://docs.scrapy.org/en/latest/topics/spider-middleware.html) for logging metadata about a crawl (which also creates records in the datbase)

### Spider

Our spider is defined in the class `TennisExplorerSpider` in [`seeder.spiders.tennis_explorer_spider`](seeder/spiders/tennis_explorer_spider.py).

The spider is not responsible for any of the parsing or processing directly.
Rather, it maintains a mapping of parser classes for each endpoint, where are parser extends `seeder.parsers.Parser` and must implement 2 methods that return iterables of `scrapy.Item` and `scrapy.Request`, respectively, from a `scrapy.Response`:

```python
class Parser(object):

  def __init__(self, *args, **kwargs):
    pass

  def parse_items(self, response):
    return [scrapy.Item(...), scrapy.Item(...)]

  def parse_links(self, response):
    raise [scrapy.Request(...), scrapy.Request(...)]
```

The spider's `parse` method selects the appropriate parser for the url of each `scrapy.Request` (based on the url's `path`), as shown in the below skeleton snippet.
To add additional parsers, the parsing logic may be implemented in a parser that handels each endpoint, after which the `TennisExplorerSpider`'s `ENDPOINT_PARSERS` may be updated.

```python
class TennisExplorerSpider(scrapy.Spider):

  # Define endpoint-specific parser classes here
  ENDPOINT_PARSERS = {
    '/results/': {
      'parser': MatchResultParser,
      'parser_kwargs': {},
      'request_kwargs': {'priority': 1},
    },
    '/next/': {
      ...
    },
    '/match-detail/': {
      ...
    },
  }

  def __init__(self, ...):
    
    # create the local mapping of endpoint->parser objects
    ctx = { ... } # come context
    self.parsers = {
      endpoint: config['parser'](**ctx, **config.get('parser_kwargs', {})) 
      for (endpoint, config) in self.ENDPOINT_PARSERS.items()
    }

  def parse(self, response):
    url = urllib.parse.urlparse(response.url)
    parser = self.parsers.get(url.path) 
    for item in parser.parse_items(response):
      yield item

    for href in parser.parse_links(response):
      yield scrapy.Request(href, self.parse)
```

### Item Pipeline

Records are inserted into the database using a combination of:
  - A `scrapy.Item` processing pipeline, [`seeder.pipelines.DatabasePipeline`](seeder/pipelines.py)
  - Model builder logic specifed in each model in [`seeder.models`](seeder/models.py); each model for the pipeline has 3 methods that create `sqlalchemy` ORM instances given a dictionary input payload:
    - `make(**kwargs)`, which creates a (potentially incomplete) record
    - `make_dependencies(**kwargs)`, which creates an iterable of incomplete records that the record would depend on (i.e. skeleton records for any foreign keys the record has to maintain referential integrity)
    - `make_with_dependencies(**kwargs)`, which calls the above 2 methods and concatenates their output
  - `scapy.Item`s in the [`seeder.items`](seeder/items.py) module, which are dynamically built from the `sqlalchemy` models 

The item pipeline does relatively little work itself, but is reponsible for:
- creating ORM model instances for each `scrapy.Item` it receives by calling that `item`'s `make_with_dependencies` method
- subsequently upserting these records to the database

Some of that seems unusual (e.g. the *incomplete* records), but there are a few considerations to note that motivate this process:
  - When a `scrapy.Response` is processed, we may not have all of the information returned in that response to create a record (e.g. the `/results/` endpoint for match results can create `Match` records, but would not have the dimensional attributes for each `Player` to create *complete* `Player` records). As such, we have to emit *incomplete* records that contain only the bare minimum information (i.e. the record's primary key), with the expectation that the page containing the remainder of the data needed will be processed at some point in the future
  - Each ORM model must specify how to contruct its skeleton dependent records, but does not need to complete them. Since we cannot guarantee processing order of items in the scraping pipeline, all of the dependencies for a specific item must be created and committed to the database within the same pipeline `process_item` call
  - A direct consequence of this is that the ORM models have very loose nullability constraints on each column, since almost all of the columns *could* be null if a table row was created from a skeleton ORM record.

## Related Work

- [slick](https://github.com/underscorenygren/slick)
  - This was an interesting find; it's a framework for storing `scrapy` item pipelines in relational databases using `sqlalchemy`. The code is professionallywritten and documented, but not heavily starred/forked.My guess is this was developed commercially over a not insignificant timespan, but then open-sourced in the [initial commit](https://github.com/underscorenygren/slick/commit/c90b9a1383a9afaaa80adedf6598f5180152d926).

## Acknowledgements

- This project is short & sweet owing entirely to the great stuff provided by the following dependencies:
  - [`scrapy`](https://scrapy.org/) for managing the crawler
  - [`beautifulsoup`](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) for parsing html
  - [`sqlalchemy`](https://www.sqlalchemy.org/) for the database Object-Relational-Mapper [(ORM)](https://en.wikipedia.org/wiki/Object%E2%80%93relational_mapping)
  - [`pytest`](https://docs.pytest.org/en/7.1.x/) for writing simple and easy to read tests 
  - [`pytest-vcr`](https://pytest-vcr.readthedocs.io/en/latest/) for simplifying the testing of code that depends on HTTP requests
