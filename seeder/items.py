import scrapy


class MatchItem(scrapy.Item):
    match_id = scropy.Field()
    tournament = scropy.Field()
    match_at = scropy.Field()
    player1 = scropy.Field()
    player2 = scropy.Field()
    odds1 = scropy.Field()
    odds2 = scropy.Field()
    sets1 = scropy.Field()
    sets2 = scropy.Field()
