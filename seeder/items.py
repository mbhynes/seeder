import scrapy

class MatchItem(scrapy.Item):
    match_id = scrapy.Field()
    tournament = scrapy.Field()
    match_at = scrapy.Field()
    player1 = scrapy.Field()
    player2 = scrapy.Field()
    odds1 = scrapy.Field()
    odds2 = scrapy.Field()
    sets1 = scrapy.Field()
    sets2 = scrapy.Field()
