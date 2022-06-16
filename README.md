# `seeder`

`seeder` is a data scraping and management package for [tennisexplorer.com](https://www.tennisexplorer.com).
It allows you to periodically scrape and store the player and match data in a structured SQL database.

## Installation

1. Clone the repository
```bash
git clone git@github.com:mbhynes/seeder.git
```

2. Set up the `virtualenv` and install the dependencies:

```bash
./dev up
```

3. Check that the package passes its tests:

```bash
./dev test
```

## Running A Spider

1. Set the connection string `SEEDER_DB_CONN_STR` in the environment:

  - This string is the fully-specified connection string to pass to `sqlalchemy`'s [`create_engine`](https://docs.sqlalchemy.org/en/14/core/engines.html#sqlalchemy.create_engine) function
  - The dialect, username, password, etc should all be contained here (i.e. not in any VCS-tracked file or `settings.py`)
```bash
# for initial testing, use a sqlite (local file) database
export SEEDER_DB_CONN_STR='sqlite:///private/seeder.db' 
```

2. Run the spider with the `scrapy` CLI

```bash
scrapy crawl tennisexplorer
```

3. Inspect the resulting database

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
