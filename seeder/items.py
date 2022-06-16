from seeder.models import Match, Player

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
  attr_names['to_model'] = lambda obj: obj.__model__(**dict(obj))
  return type(classname, (scrapy.Item,), attr_names) 


MatchItem = item_from_model('MatchItem', Match)
PlayerItem = item_from_model('PlayerItem', Player)
