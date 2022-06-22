from seeder.models import Match, MatchOdds, Player

import scrapy


def item_from_model(classname, model):
  """
  Create a scrapy.Item subclass dynamically from a sqlalchemy model.
  """
  colnames = [c.name for c in model.__table__.columns]
  attr_names = {
    col: scrapy.Field()
    for col in colnames
  }
  attr_names['__model__'] = model
  attr_names['make'] = lambda obj: obj.__model__.make(**dict(obj))
  attr_names['make_dependencies'] = lambda obj: obj.__model__.make_dependencies(**dict(obj))
  attr_names['make_with_dependencies'] = lambda obj: obj.__model__.make_with_dependencies(**dict(obj))
  return type(classname, (scrapy.Item,), attr_names) 


MatchItem = item_from_model('MatchItem', Match)
MatchOddsItem = item_from_model('MatchOddsItem', MatchOdds)
PlayerItem = item_from_model('PlayerItem', Player)
